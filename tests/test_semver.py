import pytest

from arm.config import ReleasePolicy
from arm.domain.models import BumpType, ConventionalCommit, SemVer
from arm.services.semver import compute_next_version


def test_semver_bump_major_wins():
    policy = ReleasePolicy()
    current = SemVer.parse("1.2.3")
    commits = [
        ConventionalCommit(type="fix", scope=None, description="a", breaking=False),
        ConventionalCommit(type="feat", scope=None, description="b", breaking=False),
        ConventionalCommit(type="chore", scope=None, description="c", breaking=True),
    ]
    next_v, decision = compute_next_version(current, commits, policy=policy)
    assert str(next_v) == "2.0.0"
    assert decision.bump == BumpType.major


def test_forced_level():
    policy = ReleasePolicy()
    current = SemVer.parse("0.1.0")
    next_v, decision = compute_next_version(current, [], policy=policy, forced=BumpType.minor)
    assert str(next_v) == "0.2.0"
    assert decision.reason == "forced"


def test_unknown_type_none_policy():
    policy = ReleasePolicy(unknown_type_behavior="none")
    current = SemVer.parse("0.1.0")
    commits = [ConventionalCommit(type="unknownx", scope=None, description="x", breaking=False)]
    next_v, decision = compute_next_version(current, commits, policy=policy)
    assert str(next_v) == "0.1.0"
    assert decision.bump == BumpType.none


def test_unknown_type_fail_policy():
    policy = ReleasePolicy(unknown_type_behavior="fail")
    current = SemVer.parse("0.1.0")
    commits = [ConventionalCommit(type="unknownx", scope=None, description="x", breaking=False)]
    with pytest.raises(ValueError):
        compute_next_version(current, commits, policy=policy)
