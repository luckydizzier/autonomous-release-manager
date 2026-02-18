from __future__ import annotations

import fnmatch
import os
import zipfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PackageSpec:
    project_name: str
    version: str
    repo_dir: Path
    dist_dir: Path
    exclude_globs: tuple[str, ...] = (
        ".git/*",
        ".arm/*",
        "dist/*",
        ".venv/*",
        "__pycache__/*",
        "*.pyc",
    )


def _is_excluded(rel_posix: str, globs: tuple[str, ...]) -> bool:
    for g in globs:
        if fnmatch.fnmatch(rel_posix, g) or fnmatch.fnmatch(rel_posix + "/", g):
            return True
    return False


def build_zip(spec: PackageSpec) -> Path:
    spec.dist_dir.mkdir(parents=True, exist_ok=True)
    out = spec.dist_dir / f"{spec.project_name}-{spec.version}.zip"
    if out.exists():
        out.unlink()

    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(spec.repo_dir):
            root_p = Path(root)
            rel_root = root_p.relative_to(spec.repo_dir).as_posix()
            # prune excluded dirs
            dirs[:] = [d for d in dirs if not _is_excluded(((rel_root + "/") if rel_root != "." else "") + d, spec.exclude_globs)]
            for f in files:
                rel = (root_p / f).relative_to(spec.repo_dir).as_posix()
                if _is_excluded(rel, spec.exclude_globs):
                    continue
                zf.write(spec.repo_dir / rel, arcname=rel)
    return out
