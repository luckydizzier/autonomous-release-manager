# Autonomous Release Manager (arm)

Local-only release manager CLI for git repositories.

## Install

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

## Usage

```bash
arm --repo . status
arm --repo . validate
arm --repo . plan
arm --repo . release --dry-run --project-name demo
arm --repo . rollback --dry-run
```

## Examples

### Dry run release

```bash
arm --repo . release --dry-run --allow-dirty --project-name demo
```

### Apply release on allowed branch

```bash
arm --repo . release --project-name autonomous-release-manager
```

### Signed release metadata

```bash
arm --repo . release --sign-commit --sign-tag --project-name autonomous-release-manager
```

### Explicit remote push (unsafe by default)

```bash
arm --repo . release --push --no-remote-safe --remote origin --project-name autonomous-release-manager
```

## Flags

### `remote-safe`

- Default is enabled (`--remote-safe`).
- When enabled, `--push` is blocked to prevent accidental remote side effects.
- Disable explicitly with `--no-remote-safe` only when you intend to push.

### `allowed_branches`

- Set via `arm.toml` (`[policy].allowed_branches`).
- Supports exact branch names and simple globs like `release/*`.
- Release execution fails fast when the current branch is not allowed.

### `sign-commit` and `sign-tag`

- `--sign-commit` signs the release commit (`git commit -S`).
- `--sign-tag` signs the release tag (`git tag -s`).
- Requires local git signing setup (GPG/SSH signing config).

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

## Commands

```bash
arm status
arm validate [--from REF --to REF]
arm plan [--json] [--level auto|major|minor|patch]
arm release [--dry-run] [--level ...] [--no-commit] [--no-tag] [--allow-dirty] \
  [--sign-commit] [--sign-tag] [--push] [--remote-safe/--no-remote-safe] [--remote origin]
arm rollback [--dry-run] [--hard] [--keep-artifacts]
```
