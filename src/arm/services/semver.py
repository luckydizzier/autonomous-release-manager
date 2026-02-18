from __future__ import annotations

from arm.config import ReleasePolicy
from arm.domain.models import BumpDecision, BumpType, ConventionalCommit, SemVer


_BUMP_ORDER: dict[BumpType, int] = {
    BumpType.none: 0,
    BumpType.patch: 1,
    BumpType.minor: 2,
    BumpType.major: 3,
}


def bump_from_commit(c: ConventionalCommit, *, policy: ReleasePolicy) -> BumpDecision:
    if c.breaking:
        return BumpDecision(BumpType.major, "breaking change")
    if c.type == "feat":
        return BumpDecision(BumpType.minor, "feat")
    if c.type in policy.patch_types:
        return BumpDecision(BumpType.patch, c.type)
    if c.type in policy.no_bump_types:
        return BumpDecision(BumpType.none, c.type)
    behavior = policy.normalize_behavior()
    if behavior == "none":
        return BumpDecision(BumpType.none, f"unknown:none:{c.type}")
    if behavior == "fail":
        raise ValueError(f"Unknown conventional commit type under fail policy: {c.type}")
    return BumpDecision(BumpType.patch, f"unknown:patch:{c.type}")


def max_bump(decisions: list[BumpDecision]) -> BumpDecision:
    if not decisions:
        return BumpDecision(BumpType.none, "no commits")
    best = decisions[0]
    for d in decisions[1:]:
        if _BUMP_ORDER[d.bump] > _BUMP_ORDER[best.bump]:
            best = d
    return best


def compute_next_version(
    current: SemVer,
    commits: list[ConventionalCommit],
    *,
    policy: ReleasePolicy,
    forced: BumpType | None = None,
) -> tuple[SemVer, BumpDecision]:
    if forced and forced != BumpType.none:
        return current.bump(forced), BumpDecision(forced, "forced")
    decisions = [bump_from_commit(c, policy=policy) for c in commits]
    decision = max_bump(decisions)
    return current.bump(decision.bump), decision
