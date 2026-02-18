from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from arm.domain.models import Commit


class GitError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class GitResult:
    stdout: str
    stderr: str
    returncode: int


def run_git(args: list[str], *, cwd: Path) -> GitResult:
    p = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        text=True,
        capture_output=True,
    )
    res = GitResult(stdout=p.stdout, stderr=p.stderr, returncode=p.returncode)
    if p.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {p.stderr.strip()}")
    return res


def is_dirty(*, repo_dir: Path) -> bool:
    res = run_git(["status", "--porcelain"], cwd=repo_dir)
    return res.stdout.strip() != ""


def current_branch(*, repo_dir: Path) -> str:
    res = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_dir)
    return res.stdout.strip()


def last_tag(*, repo_dir: Path, tag_prefix: str) -> str | None:
    # newest tag reachable from HEAD
    try:
        res = run_git(["describe", "--tags", "--abbrev=0", "--match", f"{tag_prefix}*"], cwd=repo_dir)
    except GitError:
        return None
    tag = res.stdout.strip()
    return tag or None


def commit_log(*, repo_dir: Path, from_ref: str | None, to_ref: str) -> list[Commit]:
    if from_ref:
        rev = f"{from_ref}..{to_ref}"
    else:
        rev = to_ref
    # delimiter separates commits reliably
    fmt = "%H%n%s%n%b%n==END=="
    res = run_git(["log", "--no-color", f"--pretty=format:{fmt}", rev], cwd=repo_dir)
    chunks = res.stdout.split("==END==")
    commits: list[Commit] = []
    for chunk in chunks:
        chunk = chunk.strip("\n")
        if not chunk.strip():
            continue
        lines = chunk.splitlines()
        sha = lines[0].strip()
        subject = lines[1].strip() if len(lines) > 1 else ""
        body = "\n".join(lines[2:]).strip() if len(lines) > 2 else ""
        commits.append(Commit(sha=sha, subject=subject, body=body))
    return commits


def diff_stat(*, repo_dir: Path, from_ref: str | None, to_ref: str) -> str:
    args = ["diff", "--stat"]
    if from_ref:
        args += [from_ref, to_ref]
    else:
        args += [to_ref]
    res = run_git(args, cwd=repo_dir)
    return res.stdout


def commit_file(*, repo_dir: Path, path: Path, message: str, sign: bool = False) -> str:
    run_git(["add", str(path)], cwd=repo_dir)
    cmd = ["commit", "-m", message]
    if sign:
        cmd.append("-S")
    run_git(cmd, cwd=repo_dir)
    sha = run_git(["rev-parse", "HEAD"], cwd=repo_dir).stdout.strip()
    return sha


def create_tag(*, repo_dir: Path, tag: str, sign: bool = False) -> None:
    if sign:
        run_git(["tag", "-s", tag, "-m", f"release {tag}"], cwd=repo_dir)
    else:
        run_git(["tag", tag], cwd=repo_dir)


def delete_tag(*, repo_dir: Path, tag: str) -> None:
    run_git(["tag", "-d", tag], cwd=repo_dir)


def push_branch(*, repo_dir: Path, remote: str, branch: str) -> None:
    run_git(["push", remote, branch], cwd=repo_dir)


def push_tag(*, repo_dir: Path, remote: str, tag: str) -> None:
    run_git(["push", remote, tag], cwd=repo_dir)
