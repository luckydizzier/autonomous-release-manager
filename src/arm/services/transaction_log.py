from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ReleaseTransaction:
    created_at_utc: str
    repo_dir: str
    version: str
    tag: str | None
    changelog_path: str | None
    changelog_commit_sha: str | None
    changelog_existed_before: bool
    changelog_before: str | None
    artifacts: list[str] = field(default_factory=list)


def build_transaction(
    *,
    repo_dir: Path,
    version: str,
    tag: str | None,
    changelog_path: Path | None,
    changelog_commit_sha: str | None,
    changelog_existed_before: bool,
    changelog_before: str | None,
    artifacts: list[Path],
) -> ReleaseTransaction:
    return ReleaseTransaction(
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        repo_dir=str(repo_dir),
        version=version,
        tag=tag,
        changelog_path=str(changelog_path) if changelog_path else None,
        changelog_commit_sha=changelog_commit_sha,
        changelog_existed_before=changelog_existed_before,
        changelog_before=changelog_before,
        artifacts=[str(a) for a in artifacts],
    )


def write_last_release(*, repo_dir: Path, tx: ReleaseTransaction) -> Path:
    arm_dir = repo_dir / ".arm"
    arm_dir.mkdir(parents=True, exist_ok=True)
    path = arm_dir / "last_release.json"
    path.write_text(json.dumps(asdict(tx), indent=2) + "\n", encoding="utf-8")
    return path


def read_last_release(*, repo_dir: Path) -> ReleaseTransaction:
    path = repo_dir / ".arm" / "last_release.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return ReleaseTransaction(**data)
