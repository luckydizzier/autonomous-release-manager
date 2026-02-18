from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BumpType(str, Enum):
    none = "none"
    patch = "patch"
    minor = "minor"
    major = "major"


@dataclass(frozen=True, slots=True)
class SemVer:
    major: int
    minor: int
    patch: int

    @staticmethod
    def parse(s: str) -> "SemVer":
        parts = s.strip().lstrip("v").split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid semver: {s!r}")
        return SemVer(*(int(p) for p in parts))

    def bump(self, bump: BumpType) -> "SemVer":
        match bump:
            case BumpType.none:
                return self
            case BumpType.patch:
                return SemVer(self.major, self.minor, self.patch + 1)
            case BumpType.minor:
                return SemVer(self.major, self.minor + 1, 0)
            case BumpType.major:
                return SemVer(self.major + 1, 0, 0)
        raise ValueError(f"Unknown bump: {bump}")

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


@dataclass(frozen=True, slots=True)
class Commit:
    sha: str
    subject: str
    body: str


@dataclass(frozen=True, slots=True)
class ConventionalCommit:
    type: str
    scope: str | None
    description: str
    breaking: bool


@dataclass(frozen=True, slots=True)
class BumpDecision:
    bump: BumpType
    reason: str


@dataclass(frozen=True, slots=True)
class ReleasePlan:
    from_ref: str
    to_ref: str
    current_version: SemVer
    next_version: SemVer
    bump: BumpType
    changelog_preview: str
