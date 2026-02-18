from __future__ import annotations

from datetime import date

from arm.domain.models import ConventionalCommit, SemVer


def render_release_section(version: SemVer, commits: list[ConventionalCommit]) -> str:
    d = date.today().isoformat()
    lines: list[str] = []
    lines.append(f"## {version} - {d}")

    breaking = [c for c in commits if c.breaking]
    feats = [c for c in commits if c.type == "feat" and not c.breaking]
    fixes = [c for c in commits if c.type in {"fix", "perf", "refactor"} and not c.breaking]
    other = [c for c in commits if c not in breaking + feats + fixes]

    def add_group(title: str, items: list[ConventionalCommit]) -> None:
        if not items:
            return
        lines.append("")
        lines.append(f"### {title}")
        for it in items:
            scope = f"**{it.scope}**: " if it.scope else ""
            bang = " (BREAKING)" if it.breaking else ""
            lines.append(f"- {scope}{it.description}{bang}")

    add_group("Breaking Changes", breaking)
    add_group("Features", feats)
    add_group("Fixes", fixes)
    add_group("Other", other)

    lines.append("")
    return "\n".join(lines)


def prepend_changelog(existing: str | None, new_section: str) -> str:
    existing = (existing or "").lstrip("\n")
    header = "# Changelog\n\n"
    if existing.startswith("# Changelog"):
        # keep existing header
        rest = existing.split("\n", 1)[1].lstrip("\n") if "\n" in existing else ""
        return header + new_section.rstrip() + "\n\n" + rest
    return header + new_section.rstrip() + "\n\n" + existing
