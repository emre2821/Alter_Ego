"""Runtime configuration helpers for Alter/Ego.

This module centralises the logic for discovering paths that the
application relies on. It merges values from ``alter_ego_config.yaml``
with environment variable overrides so every component reads from the
same source of truth.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Dict

import yaml

APP_DIR = Path(__file__).resolve().parent
CONFIG_FILE = APP_DIR / "alter_ego_config.yaml"

DEFAULT_PATHS = {
    "persona_root": APP_DIR / "personas",
    "models_dir": APP_DIR / "models",
    "memory_db": APP_DIR / "alter_ego_memory.db",
}

ENV_OVERRIDES = {
    "persona_root": ("PERSONA_ROOT",),
    "models_dir": ("GPT4ALL_MODEL_DIR", "GPT4ALL_MODELS_DIR"),
    "memory_db": ("MEMORY_DB",),
}


def _read_yaml_config() -> Dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        data = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data or {}


def _resolve_path(value: str | Path | None) -> Path | None:
    if value in (None, ""):
        return None
    path = Path(value)
    if not path.is_absolute():
        path = (CONFIG_FILE.parent / path).resolve()
    return path


@lru_cache()
def get_runtime_paths() -> Dict[str, Path]:
    """Return resolved runtime paths with config + env precedence."""

    cfg = _read_yaml_config()
    resolved = {}
    for key, default in DEFAULT_PATHS.items():
        candidate = None

        # 1) environment variable override
        env_vars = ENV_OVERRIDES.get(key, ())
        for env_var in env_vars:
            candidate = _resolve_path(os.getenv(env_var))
            if candidate is not None:
                break

        # 2) configuration file entry
        if candidate is None:
            cfg_value = cfg.get(key) or cfg.get("paths", {}).get(key)
            if cfg_value is None and key == "memory_db":
                cfg_value = cfg.get("db_path")
            candidate = _resolve_path(cfg_value)

        # 3) fallback default
        if candidate is None:
            candidate = default

        resolved[key] = candidate

    return resolved


def get_persona_root() -> Path:
    return get_runtime_paths()["persona_root"]


def get_models_dir() -> Path:
    return get_runtime_paths()["models_dir"]


def get_memory_db_path() -> Path:
    return get_runtime_paths()["memory_db"]


__all__ = [
    "get_persona_root",
    "get_models_dir",
    "get_memory_db_path",
    "get_runtime_paths",
]
