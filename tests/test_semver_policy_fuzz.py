import random

from arm.config import ReleasePolicy
from arm.domain.models import BumpType, ConventionalCommit, SemVer
from arm.services.semver import compute_next_version


ORDER = {BumpType.none: 0, BumpType.patch: 1, BumpType.minor: 2, BumpType.major: 3}


def expected_bump(commits: list[ConventionalCommit], policy: ReleasePolicy) -> BumpType:
    best = BumpType.none
    behavior = policy.normalize_behavior()
    for c in commits:
        if c.breaking:
            b = BumpType.major
        elif c.type == "feat":
            b = BumpType.minor
        elif c.type in policy.patch_types:
            b = BumpType.patch
        elif c.type in policy.no_bump_types:
            b = BumpType.none
        else:
            if behavior == "fail":
                raise ValueError("unknown type")
            b = BumpType.none if behavior == "none" else BumpType.patch
        if ORDER[b] > ORDER[best]:
            best = b
    return best


def bump_ref(v: SemVer, b: BumpType) -> SemVer:
    if b == BumpType.none:
        return v
    if b == BumpType.patch:
        return SemVer(v.major, v.minor, v.patch + 1)
    if b == BumpType.minor:
        return SemVer(v.major, v.minor + 1, 0)
    return SemVer(v.major + 1, 0, 0)


def test_semver_policy_fuzz_histories():
    rng = random.Random(1337)
    types = [
        "feat",
        "fix",
        "perf",
        "docs",
        "chore",
        "refactor",
        "test",
        "build",
        "ci",
        "style",
        "revert",
        "merge",
        "weirdx",
        "foo",
    ]
    policies = [
        ReleasePolicy(unknown_type_behavior="patch"),
        ReleasePolicy(unknown_type_behavior="none"),
        ReleasePolicy(unknown_type_behavior="fail"),
    ]

    for _ in range(250):
        current = SemVer(rng.randint(0, 3), rng.randint(0, 20), rng.randint(0, 50))
        commits = [
            ConventionalCommit(
                type=rng.choice(types),
                scope=None,
                description="x",
                breaking=(rng.random() < 0.08),
            )
            for _ in range(rng.randint(0, 60))
        ]
        forced = rng.choice([None, BumpType.none, BumpType.patch, BumpType.minor, BumpType.major])
        for policy in policies:
            if forced and forced != BumpType.none:
                nxt, dec = compute_next_version(current, commits, policy=policy, forced=forced)
                assert dec.bump == forced
                assert str(nxt) == str(bump_ref(current, forced))
                continue
            try:
                expected = expected_bump(commits, policy)
            except ValueError:
                try:
                    compute_next_version(current, commits, policy=policy, forced=forced)
                except ValueError:
                    continue
                raise AssertionError("Expected ValueError for unknown type under fail policy")
            nxt, dec = compute_next_version(current, commits, policy=policy, forced=forced)
            assert dec.bump == expected
            assert str(nxt) == str(bump_ref(current, expected))

