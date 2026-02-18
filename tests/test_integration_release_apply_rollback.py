import json
import os
import subprocess
import sys
from pathlib import Path


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    project_root = Path(__file__).resolve().parents[1]
    src_dir = project_root / "src"
    env = os.environ.copy()
    current_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{src_dir}{os.pathsep}{current_pp}" if current_pp else str(src_dir)
    return subprocess.run(
        [sys.executable, "-m", "arm.cli", *args],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        env=env,
    )


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd), text=True, capture_output=True, check=True)


def test_release_apply_then_rollback_restores_state(tmp_path: Path):
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Tester")

    (tmp_path / "file.txt").write_text("base")
    _git(tmp_path, "add", "file.txt")
    _git(tmp_path, "commit", "-m", "chore: baseline")
    _git(tmp_path, "tag", "v0.1.0")

    (tmp_path / "feature.txt").write_text("new feature")
    _git(tmp_path, "add", "feature.txt")
    _git(tmp_path, "commit", "-m", "feat: add feature file")

    r = _run(tmp_path, "--repo", str(tmp_path), "release", "--project-name", "x")
    assert r.returncode == 0, (r.stdout, r.stderr)
    release_data = json.loads(r.stdout)
    assert release_data["dry_run"] is False
    assert release_data["tag"] == "v0.2.0"
    assert (tmp_path / "CHANGELOG.md").exists()
    assert (tmp_path / ".arm" / "last_release.json").exists()
    assert (tmp_path / "dist" / "x-0.2.0.zip").exists()

    tags = _git(tmp_path, "tag", "--list").stdout
    assert "v0.2.0" in tags

    rr = _run(tmp_path, "--repo", str(tmp_path), "rollback")
    assert rr.returncode == 0, (rr.stdout, rr.stderr)
    rollback_data = json.loads(rr.stdout)
    assert "delete tag v0.2.0" in " | ".join(rollback_data["actions"])

    tags_after = _git(tmp_path, "tag", "--list").stdout
    assert "v0.2.0" not in tags_after
    assert not (tmp_path / ".arm" / "last_release.json").exists()
    assert not (tmp_path / "dist" / "x-0.2.0.zip").exists()
    # Changelog did not exist before release.
    assert not (tmp_path / "CHANGELOG.md").exists()

