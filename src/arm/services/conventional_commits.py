from __future__ import annotations

import re
from dataclasses import dataclass

from arm.domain.models import Commit, ConventionalCommit


@dataclass(frozen=True, slots=True)
class ConventionalCommitError:
    sha: str
    subject: str
    reason: str


_HEADER_RE = re.compile(
    r"^(?P<type>[a-z]+)"  # type
    r"(?:\((?P<scope>[^)]+)\))?"  # optional scope
    r"(?P<bang>!)?"  # breaking bang
    r":\s+"  # colon + space(s)
    r"(?P<desc>.+?)\s*$"  # description
)


def parse_conventional_subject(subject: str) -> ConventionalCommit | None:
    m = _HEADER_RE.match(subject.strip())
    if not m:
        return None
    typ = m.group("type")
    scope = m.group("scope")
    desc = m.group("desc")
    breaking = bool(m.group("bang"))
    return ConventionalCommit(type=typ, scope=scope, description=desc, breaking=breaking)


def has_breaking_footer(body: str) -> bool:
    # Conventional Commits: footer token "BREAKING CHANGE:" or "BREAKING-CHANGE:"
    b = body or ""
    return ("BREAKING CHANGE:" in b) or ("BREAKING-CHANGE:" in b)


def validate_commits(commits: list[Commit]) -> tuple[list[ConventionalCommit], list[ConventionalCommitError]]:
    ok: list[ConventionalCommit] = []
    errs: list[ConventionalCommitError] = []
    for c in commits:
        parsed = parse_conventional_subject(c.subject)
        if not parsed:
            errs.append(ConventionalCommitError(sha=c.sha, subject=c.subject, reason="Non-conventional subject"))
            continue
        breaking = parsed.breaking or has_breaking_footer(c.body)
        ok.append(
            ConventionalCommit(
                type=parsed.type,
                scope=parsed.scope,
                description=parsed.description,
                breaking=breaking,
            )
        )
    return ok, errs
