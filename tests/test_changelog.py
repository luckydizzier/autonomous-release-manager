from arm.domain.models import ConventionalCommit, SemVer
from arm.services.changelog import prepend_changelog, render_release_section


def test_prepend_adds_header():
    sec = "## 1.0.0 - 2026-01-01\n\n- item\n"
    out = prepend_changelog("", sec)
    assert out.startswith("# Changelog")
    assert "## 1.0.0" in out


def test_render_groups():
    commits = [
        ConventionalCommit(type="feat", scope="core", description="add", breaking=False),
        ConventionalCommit(type="fix", scope=None, description="bug", breaking=False),
    ]
    sec = render_release_section(SemVer.parse("1.0.0"), commits)
    assert "### Features" in sec
    assert "### Fixes" in sec
