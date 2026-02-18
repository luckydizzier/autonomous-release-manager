from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from arm.adapters.git import GitError, delete_tag, run_git
from arm.services.transaction_log import ReleaseTransaction


@dataclass(frozen=True, slots=True)
class RollbackResult:
    actions: list[str]


def rollback_last_release(*, repo_dir: Path, tx: ReleaseTransaction, dry_run: bool, hard: bool, keep_artifacts: bool) -> RollbackResult:
    actions: list[str] = []

    if tx.tag:
        actions.append(f"delete tag {tx.tag}")
        if not dry_run:
            try:
                delete_tag(repo_dir=repo_dir, tag=tx.tag)
            except GitError:
                # ignore missing tag
                pass

    if tx.changelog_commit_sha:
        if hard:
            actions.append(f"hard reset to {tx.changelog_commit_sha}^")
            if not dry_run:
                run_git(["reset", "--hard", f"{tx.changelog_commit_sha}^"], cwd=repo_dir)
        else:
            actions.append(f"revert commit {tx.changelog_commit_sha}")
            if not dry_run:
                run_git(["revert", "--no-edit", tx.changelog_commit_sha], cwd=repo_dir)
    elif tx.changelog_path:
        actions.append(f"restore changelog {tx.changelog_path}")
        if not dry_run:
            p = Path(tx.changelog_path)
            if tx.changelog_existed_before:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(tx.changelog_before or "", encoding="utf-8")
            else:
                p.unlink(missing_ok=True)

    if not keep_artifacts:
        for a in tx.artifacts:
            actions.append(f"delete artifact {a}")
            if not dry_run:
                p = Path(a)
                if p.exists():
                    p.unlink()

    return RollbackResult(actions=actions)
