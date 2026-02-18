from __future__ import annotations

import fnmatch
import json
from pathlib import Path

import typer

from arm.config import load_config
from arm.adapters import git as git_adapter
from arm.adapters.git import GitError
from arm.domain.models import BumpType, SemVer
from arm.services.changelog import prepend_changelog, render_release_section
from arm.services.conventional_commits import validate_commits
from arm.services.packager import PackageSpec, build_zip
from arm.services.rollback import rollback_last_release
from arm.services.semver import compute_next_version
from arm.services.transaction_log import build_transaction, read_last_release, write_last_release

app = typer.Typer(add_completion=False, help="Autonomous Release Manager (arm)")


class ValidationFailed(RuntimeError):
    pass


def _repo_dir(repo: str | None) -> Path:
    return Path(repo or ".").resolve()


def _level_to_bump(level: str) -> BumpType | None:
    level = (level or "auto").lower()
    if level == "auto":
        return None
    return BumpType(level)


def _branch_allowed(branch: str, patterns: set[str]) -> bool:
    if not patterns:
        return True
    return any(fnmatch.fnmatch(branch, p) for p in patterns)


@app.callback()
def _root(
    ctx: typer.Context,
    repo: str | None = typer.Option(None, "--repo", help="Path to the git repo (default: cwd)"),
    config: str | None = typer.Option(None, "--config", help="Path to arm.toml policy config"),
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["repo_dir"] = _repo_dir(repo)
    ctx.obj["config"] = load_config(config)


@app.command()
def status(ctx: typer.Context, tag_prefix: str = typer.Option("v", "--tag-prefix")) -> None:
    repo_dir: Path = ctx.obj["repo_dir"]
    dirty = False
    last = None
    branch = None
    try:
        dirty = git_adapter.is_dirty(repo_dir=repo_dir)
        last = git_adapter.last_tag(repo_dir=repo_dir, tag_prefix=tag_prefix)
        branch = git_adapter.current_branch(repo_dir=repo_dir)
    except Exception:
        # keep status usable even if not a git repo
        pass
    typer.echo(
        json.dumps(
            {"repo": str(repo_dir), "dirty": dirty, "last_tag": last, "branch": branch},
            indent=2,
        )
    )


@app.command()
def validate(
    ctx: typer.Context,
    from_ref: str = typer.Option(None, "--from"),
    to_ref: str = typer.Option("HEAD", "--to"),
    tag_prefix: str = typer.Option("v", "--tag-prefix"),
) -> None:
    repo_dir: Path = ctx.obj["repo_dir"]
    if from_ref is None:
        from_ref = git_adapter.last_tag(repo_dir=repo_dir, tag_prefix=tag_prefix)
    commits = git_adapter.commit_log(repo_dir=repo_dir, from_ref=from_ref, to_ref=to_ref)
    parsed, errors = validate_commits(commits)
    if errors:
        for e in errors:
            typer.echo(f"{e.sha[:8]} {e.reason}: {e.subject}", err=True)
        raise typer.Exit(code=2)
    typer.echo(f"OK ({len(parsed)} commits)")


@app.command()
def plan(
    ctx: typer.Context,
    level: str = typer.Option("auto", "--level"),
    json_out: bool = typer.Option(False, "--json"),
    tag_prefix: str = typer.Option("v", "--tag-prefix"),
    initial_version: str = typer.Option(None, "--initial-version"),
    to_ref: str = typer.Option("HEAD", "--to"),
) -> None:
    repo_dir: Path = ctx.obj["repo_dir"]
    policy = ctx.obj["config"].policy
    last = git_adapter.last_tag(repo_dir=repo_dir, tag_prefix=tag_prefix)
    initial = initial_version or policy.initial_version
    current = SemVer.parse(last.lstrip(tag_prefix)) if last else SemVer.parse(initial)
    commits = git_adapter.commit_log(repo_dir=repo_dir, from_ref=last, to_ref=to_ref)
    parsed, errors = validate_commits(commits)
    if errors:
        for e in errors:
            typer.echo(f"{e.sha[:8]} {e.reason}: {e.subject}", err=True)
        raise typer.Exit(code=2)
    next_v, decision = compute_next_version(
        current, parsed, policy=policy, forced=_level_to_bump(level)
    )
    preview = render_release_section(next_v, parsed)

    if json_out:
        typer.echo(
            json.dumps(
                {
                    "from": last,
                    "to": to_ref,
                    "current_version": str(current),
                    "next_version": str(next_v),
                    "bump": decision.bump,
                    "reason": decision.reason,
                    "changelog_preview": preview,
                },
                indent=2,
                default=str,
            )
        )
    else:
        typer.echo(f"{current} -> {next_v} ({decision.bump}: {decision.reason})")
        typer.echo("\n" + preview)


@app.command()
def release(
    ctx: typer.Context,
    dry_run: bool = typer.Option(False, "--dry-run"),
    level: str = typer.Option("auto", "--level"),
    no_commit: bool = typer.Option(False, "--no-commit"),
    no_tag: bool = typer.Option(False, "--no-tag"),
    sign_commit: bool = typer.Option(False, "--sign-commit"),
    sign_tag: bool = typer.Option(False, "--sign-tag"),
    allow_dirty: bool = typer.Option(False, "--allow-dirty"),
    push: bool = typer.Option(False, "--push"),
    remote_safe: bool | None = typer.Option(None, "--remote-safe/--no-remote-safe"),
    remote: str | None = typer.Option(None, "--remote"),
    tag_prefix: str = typer.Option("v", "--tag-prefix"),
    initial_version: str = typer.Option(None, "--initial-version"),
    project_name: str = typer.Option("project", "--project-name"),
) -> None:
    repo_dir: Path = ctx.obj["repo_dir"]
    policy = ctx.obj["config"].policy
    branch = git_adapter.current_branch(repo_dir=repo_dir)
    if not _branch_allowed(branch, policy.allowed_branches):
        typer.echo(
            f"Branch policy violation: current branch '{branch}' is not in allowed_branches.",
            err=True,
        )
        raise typer.Exit(code=1)

    remote_safe_effective = policy.remote_safe_default if remote_safe is None else remote_safe
    if push and remote_safe_effective:
        typer.echo(
            "Remote-safe mode is enabled. Refusing push. Use --no-remote-safe with --push to allow.",
            err=True,
        )
        raise typer.Exit(code=1)
    remote_name = remote or policy.default_remote

    enforce_clean = policy.fail_on_dirty and not allow_dirty
    if enforce_clean and git_adapter.is_dirty(repo_dir=repo_dir):
        typer.echo("Dirty working tree. Use --allow-dirty to override.", err=True)
        raise typer.Exit(code=1)

    last = git_adapter.last_tag(repo_dir=repo_dir, tag_prefix=tag_prefix)
    initial = initial_version or policy.initial_version
    current = SemVer.parse(last.lstrip(tag_prefix)) if last else SemVer.parse(initial)

    commits = git_adapter.commit_log(repo_dir=repo_dir, from_ref=last, to_ref="HEAD")
    parsed, errors = validate_commits(commits)
    if errors:
        for e in errors:
            typer.echo(f"{e.sha[:8]} {e.reason}: {e.subject}", err=True)
        raise typer.Exit(code=2)

    try:
        next_v, decision = compute_next_version(
            current, parsed, policy=policy, forced=_level_to_bump(level)
        )
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2)
    section = render_release_section(next_v, parsed)

    changelog_path = repo_dir / "CHANGELOG.md"
    existing = changelog_path.read_text(encoding="utf-8") if changelog_path.exists() else ""
    new_changelog = prepend_changelog(existing, section)

    tag = f"{tag_prefix}{next_v}"
    dist_dir = repo_dir / "dist"

    actions: list[str] = []
    artifacts: list[Path] = []
    rollback_actions: list[str] = []
    changelog_commit_sha: str | None = None
    tag_created = False
    changelog_existed_before = changelog_path.exists()
    changelog_before = existing if changelog_existed_before else None

    try:
        actions.append(f"write {changelog_path}")
        if not dry_run:
            changelog_path.write_text(new_changelog, encoding="utf-8")

        if not no_commit:
            actions.append("git commit CHANGELOG.md")
            if not dry_run:
                changelog_commit_sha = git_adapter.commit_file(
                    repo_dir=repo_dir,
                    path=changelog_path,
                    message=f"chore(release): {tag}",
                    sign=sign_commit,
                )

        if not no_tag:
            actions.append(f"git tag {tag}")
            if not dry_run:
                git_adapter.create_tag(repo_dir=repo_dir, tag=tag, sign=sign_tag)
                tag_created = True

        actions.append("build zip")
        if not dry_run:
            zip_path = build_zip(
                PackageSpec(
                    project_name=project_name,
                    version=str(next_v),
                    repo_dir=repo_dir,
                    dist_dir=dist_dir,
                )
            )
            artifacts.append(zip_path)

        if not dry_run:
            tx = build_transaction(
                repo_dir=repo_dir,
                version=str(next_v),
                tag=None if no_tag else tag,
                changelog_path=changelog_path,
                changelog_commit_sha=changelog_commit_sha,
                changelog_existed_before=changelog_existed_before,
                changelog_before=changelog_before,
                artifacts=artifacts,
            )
            write_last_release(repo_dir=repo_dir, tx=tx)
        if push:
            actions.append(f"git push {remote_name} {branch}")
            if not dry_run:
                git_adapter.push_branch(repo_dir=repo_dir, remote=remote_name, branch=branch)
            if not no_tag:
                actions.append(f"git push {remote_name} {tag}")
                if not dry_run:
                    git_adapter.push_tag(repo_dir=repo_dir, remote=remote_name, tag=tag)
    except Exception as exc:
        if not dry_run:
            # Compensating rollback for partial execution.
            if tag_created:
                try:
                    git_adapter.delete_tag(repo_dir=repo_dir, tag=tag)
                    rollback_actions.append(f"deleted tag {tag}")
                except GitError:
                    rollback_actions.append(f"failed deleting tag {tag}")
            if changelog_commit_sha:
                try:
                    git_adapter.run_git(["revert", "--no-edit", changelog_commit_sha], cwd=repo_dir)
                    rollback_actions.append(f"reverted commit {changelog_commit_sha}")
                except GitError:
                    rollback_actions.append(f"failed reverting commit {changelog_commit_sha}")
            elif changelog_path.exists():
                if changelog_existed_before and changelog_before is not None:
                    changelog_path.write_text(changelog_before, encoding="utf-8")
                    rollback_actions.append("restored previous CHANGELOG.md")
                else:
                    changelog_path.unlink(missing_ok=True)
                    rollback_actions.append("removed generated CHANGELOG.md")
            for a in artifacts:
                if a.exists():
                    a.unlink()
                    rollback_actions.append(f"deleted artifact {a}")
        typer.echo(
            json.dumps(
                {
                    "error": str(exc),
                    "dry_run": dry_run,
                    "actions": actions,
                    "auto_rollback_actions": rollback_actions,
                },
                indent=2,
            ),
            err=True,
        )
        raise typer.Exit(code=1)

    typer.echo(
        json.dumps(
            {
                "current_version": str(current),
                "next_version": str(next_v),
                "bump": decision.bump,
                "reason": decision.reason,
                "tag": None if no_tag else tag,
                "dry_run": dry_run,
                "remote_safe": remote_safe_effective,
                "actions": actions,
                "artifacts": [str(a) for a in artifacts],
            },
            indent=2,
            default=str,
        )
    )


@app.command()
def rollback(
    ctx: typer.Context,
    dry_run: bool = typer.Option(False, "--dry-run"),
    hard: bool = typer.Option(False, "--hard"),
    keep_artifacts: bool = typer.Option(False, "--keep-artifacts"),
) -> None:
    repo_dir: Path = ctx.obj["repo_dir"]
    tx = read_last_release(repo_dir=repo_dir)
    res = rollback_last_release(repo_dir=repo_dir, tx=tx, dry_run=dry_run, hard=hard, keep_artifacts=keep_artifacts)
    if not dry_run:
        # best-effort cleanup of tx log
        try:
            (repo_dir / ".arm" / "last_release.json").unlink()
        except FileNotFoundError:
            pass
    typer.echo(json.dumps({"dry_run": dry_run, "actions": res.actions}, indent=2))


if __name__ == "__main__":
    app()
