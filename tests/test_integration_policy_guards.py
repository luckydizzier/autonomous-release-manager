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


def _seed_repo(tmp_path: Path) -> None:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Tester")
    (tmp_path / "file.txt").write_text("base")
    _git(tmp_path, "add", "file.txt")
    _git(tmp_path, "commit", "-m", "chore: baseline")
    _git(tmp_path, "tag", "v0.1.0")
    (tmp_path / "feature.txt").write_text("f")
    _git(tmp_path, "add", "feature.txt")
    _git(tmp_path, "commit", "-m", "feat: add feature")


def test_remote_safe_blocks_push_by_default(tmp_path: Path):
    _seed_repo(tmp_path)
    p = _run(
        tmp_path,
        "--repo",
        str(tmp_path),
        "release",
        "--push",
        "--allow-dirty",
        "--project-name",
        "x",
    )
    assert p.returncode == 1
    assert "Remote-safe mode is enabled" in p.stderr
    assert not (tmp_path / ".arm").exists()
    assert not (tmp_path / "dist").exists()


def test_branch_policy_blocks_disallowed_branch(tmp_path: Path):
    _seed_repo(tmp_path)
    cfg = tmp_path / "arm.toml"
    cfg.write_text("[policy]\nallowed_branches=['release/*']\n", encoding="utf-8")
    p = _run(
        tmp_path,
        "--repo",
        str(tmp_path),
        "--config",
        str(cfg),
        "release",
        "--allow-dirty",
        "--project-name",
        "x",
    )
    assert p.returncode == 1
    assert "Branch policy violation" in p.stderr
    assert not (tmp_path / ".arm").exists()
    assert not (tmp_path / "dist").exists()
