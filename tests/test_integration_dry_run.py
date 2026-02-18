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


def test_release_dry_run_has_no_side_effects(tmp_path: Path):
    subprocess.run(["git", "init"], cwd=str(tmp_path), check=True, text=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=str(tmp_path), check=True)

    (tmp_path / "file.txt").write_text("hi")
    subprocess.run(["git", "add", "file.txt"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "commit", "-m", "feat: init"], cwd=str(tmp_path), check=True)

    p = _run(tmp_path, "--repo", str(tmp_path), "release", "--dry-run", "--allow-dirty", "--project-name", "x")
    assert p.returncode == 0, (p.stdout, p.stderr)
    data = json.loads(p.stdout)
    assert data["dry_run"] is True

    assert not (tmp_path / "CHANGELOG.md").exists()
    assert not (tmp_path / ".arm").exists()
    assert not (tmp_path / "dist").exists()

    st = subprocess.run(["git", "status", "--porcelain"], cwd=str(tmp_path), text=True, capture_output=True)
    assert st.stdout.strip() == ""
