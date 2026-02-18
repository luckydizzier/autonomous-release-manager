from pathlib import Path

from arm.services.packager import PackageSpec, build_zip


def test_packager_excludes_git(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "x").write_text("no")
    (tmp_path / "a.txt").write_text("yes")
    dist = tmp_path / "dist"
    z = build_zip(PackageSpec(project_name="p", version="1.0.0", repo_dir=tmp_path, dist_dir=dist))
    assert z.exists()
