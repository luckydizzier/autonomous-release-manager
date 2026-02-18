# Release Checklist

## Version `v0.1.0`

1. Verify `pyproject.toml` version is `0.1.0`.
2. Run local tests: `pytest -q`.
3. Run local dry-run flow in a sample repo:
   - `arm --repo . plan`
   - `arm --repo . release --dry-run --allow-dirty --project-name demo`
4. Validate rollback behavior:
   - `arm --repo . rollback --dry-run`
5. Confirm CI is green on GitHub Actions (ubuntu-latest, macos-latest, Python 3.12).
6. Create annotated tag:
   - `git tag -a v0.1.0 -m "v0.1.0"`
7. Push branch and tag:
   - `git push origin main`
   - `git push origin v0.1.0`
8. Create GitHub Release using `.github/RELEASE_TEMPLATE.md`.
9. Attach artifact zip from `dist/` (for example `dist/autonomous-release-manager-v0.1.0.zip`).
10. Post-release sanity check:
    - `arm --repo . status`
    - `arm --repo . validate`
