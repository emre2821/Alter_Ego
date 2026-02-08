from pathlib import Path

import pytest

from alter_ego.alter_ego_computer import Config, load_config


def test_load_config_rejects_scalar_yaml(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("0\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Config file must contain a mapping"):
        load_config(cfg_path)


def test_load_config_allows_empty_yaml(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("", encoding="utf-8")

    cfg = load_config(cfg_path)

    assert isinstance(cfg, Config)
    assert cfg.data_dir == Config().data_dir
