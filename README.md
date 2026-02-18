# Autonomous Release Manager (arm)

Local-only release manager CLI for git repositories:
- reads git commit history and diff stats
- validates Conventional Commits
- computes SemVer bump
- generates/prepends Markdown changelog
- builds a zip artifact
- supports dry-run and rollback

## Install (dev)

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

## Commands (MVP)

```bash
arm status
arm validate [--from REF --to REF]
arm plan [--json] [--level auto|major|minor|patch]
arm release [--dry-run] [--level ...] [--no-commit] [--no-tag] [--allow-dirty] \
  [--sign-commit] [--sign-tag] [--push] [--remote-safe/--no-remote-safe] [--remote origin]
arm rollback [--dry-run] [--hard] [--keep-artifacts]
```

## Notes

- By default, `arm release` refuses to run on a dirty working tree unless `--allow-dirty` is set.
- `arm release --dry-run` has **zero side effects** (no file writes, no tags, no dist artifacts, no `.arm` log).
- By default, **remote-safe mode is ON**, so `--push` is blocked unless you pass `--no-remote-safe`.
- Branch policy can be enforced via `arm.toml`.

## Policy config (`arm.toml`)

```toml
[policy]
initial_version = "0.1.0"
fail_on_dirty = true
unknown_type_behavior = "patch" # patch|none|fail
patch_types = ["fix", "perf", "docs", "chore", "refactor", "test", "build", "ci", "style"]
no_bump_types = ["revert", "merge"]
allowed_branches = ["main", "release/*"]
remote_safe_default = true
default_remote = "origin"
```

## Quick smoke test (in any git repo)

```bash
arm --repo . status
arm --repo . validate
arm --repo . plan
arm --repo . release --dry-run --allow-dirty --project-name demo
```
