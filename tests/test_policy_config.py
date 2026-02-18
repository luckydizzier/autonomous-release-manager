from pathlib import Path

from arm.config import load_config


def test_load_policy_from_arm_toml(tmp_path: Path):
    cfg = tmp_path / "arm.toml"
    cfg.write_text(
        """
[policy]
unknown_type_behavior = "none"
initial_version = "0.0.1"
fail_on_dirty = false
patch_types = ["fix", "perf"]
no_bump_types = ["docs", "chore", "merge", "revert"]
""".strip(),
        encoding="utf-8",
    )

    app_cfg = load_config(str(cfg))
    p = app_cfg.policy
    assert p.normalize_behavior() == "none"
    assert p.initial_version == "0.0.1"
    assert p.fail_on_dirty is False
    assert p.patch_types == {"fix", "perf"}
    assert "docs" in p.no_bump_types

