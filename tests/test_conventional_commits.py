from arm.domain.models import Commit
from arm.services.conventional_commits import parse_conventional_subject, validate_commits


def test_parse_subject_with_scope_and_bang():
    cc = parse_conventional_subject("feat(core)!: big change")
    assert cc is not None
    assert cc.type == "feat"
    assert cc.scope == "core"
    assert cc.breaking is True


def test_validate_collects_errors():
    commits = [
        Commit(sha="a" * 40, subject="not conventional", body=""),
        Commit(sha="b" * 40, subject="fix: ok", body=""),
    ]
    ok, errs = validate_commits(commits)
    assert len(ok) == 1
    assert len(errs) == 1
