## Autonomous Release Manager `v0.1.0`

### Summary

Release type: `minor`  
Tag: `v0.1.0`

### Release Notes

- Add release-grade safety controls for branch policy and remote-safe mode.
- Add signing options for commit/tag (`--sign-commit`, `--sign-tag`).
- Add policy/config coverage and semver fuzz/property-style tests.
- Improve rollback transaction handling and integration coverage.

### Usage

```bash
arm --repo . release --dry-run --project-name autonomous-release-manager
```

### Artifacts

- Attach ZIP artifact generated into `dist/`:
  - `dist/autonomous-release-manager-v0.1.0.zip`

### Validation

- [ ] CI passing on `ubuntu-latest` and `macos-latest`
- [ ] `pytest -q` green locally
- [ ] Rollback scenario validated
