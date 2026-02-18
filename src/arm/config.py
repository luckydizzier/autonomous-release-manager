from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from arm.domain.models import BumpType


@dataclass(frozen=True, slots=True)
class ReleasePolicy:
    patch_types: set[str] = field(
        default_factory=lambda: {"fix", "perf", "refactor", "docs", "chore", "test", "build", "ci", "style"}
    )
    no_bump_types: set[str] = field(default_factory=lambda: {"revert", "merge"})
    unknown_type_behavior: str = "patch"  # patch|none|fail
    initial_version: str = "0.1.0"
    fail_on_dirty: bool = True
    allowed_branches: set[str] = field(default_factory=set)  # empty = allow all
    remote_safe_default: bool = True
    default_remote: str = "origin"

    def normalize_behavior(self) -> str:
        b = self.unknown_type_behavior.strip().lower()
        if b not in {"patch", "none", "fail"}:
            return "patch"
        return b

    def forced_bump(self, level: str) -> BumpType | None:
        level = (level or "auto").strip().lower()
        if level == "auto":
            return None
        return BumpType(level)


@dataclass(frozen=True, slots=True)
class AppConfig:
    policy: ReleasePolicy


def _read_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    return tomllib.loads(path.read_text(encoding="utf-8"))


def load_config(config_path: str | None) -> AppConfig:
    path = Path(config_path).resolve() if config_path else Path("arm.toml").resolve()
    data = _read_toml(path)
    pol = (data.get("policy") or {}) if isinstance(data, dict) else {}

    patch_types = set(pol.get("patch_types", [])) if isinstance(pol.get("patch_types", []), list) else None
    no_bump_types = set(pol.get("no_bump_types", [])) if isinstance(pol.get("no_bump_types", []), list) else None

    policy = ReleasePolicy(
        patch_types=patch_types or ReleasePolicy().patch_types,
        no_bump_types=no_bump_types or ReleasePolicy().no_bump_types,
        unknown_type_behavior=str(pol.get("unknown_type_behavior", "patch")),
        initial_version=str(pol.get("initial_version", "0.1.0")),
        fail_on_dirty=bool(pol.get("fail_on_dirty", True)),
        allowed_branches=set(pol.get("allowed_branches", []))
        if isinstance(pol.get("allowed_branches", []), list)
        else set(),
        remote_safe_default=bool(pol.get("remote_safe_default", True)),
        default_remote=str(pol.get("default_remote", "origin")),
    )
    return AppConfig(policy=policy)
