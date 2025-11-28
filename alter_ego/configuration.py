"""Runtime configuration helpers for Alter/Ego.

This module centralises discovery of the folders and files Alter/Ego
relies on at runtime.  Callers no longer need to duplicate logic to
resolve where personas, GPT4All models, or the memory database live –
``configuration`` reads ``alter_ego_config.yaml`` (when present) and then
applies environment variable overrides so every component shares a single
source of truth.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

try:  # YAML is an optional dependency for tests/CI environments
    import yaml  # type: ignore
except Exception:  # pragma: no cover - handled by returning defaults
    yaml = None  # type: ignore

APP_ROOT = Path(__file__).resolve().parent
CONFIG_FILE = APP_ROOT / "alter_ego_config.yaml"

DEFAULT_LOG_PATH = APP_ROOT / "chaos_echo_log.chaos"

# Legacy fallback used by early Windows builds that shipped personas in a
# fixed location on C:\.  We still honour it so existing installations do
# not break when updating.
LEGACY_PERSONA_ROOT = Path(r"C:\EdenOS_Origin\all_daemons")


log = logging.getLogger(__name__)


def _expand(path: str | os.PathLike[str]) -> Path:
    """Expand ``path`` relative to :data:`APP_ROOT` when required."""

    expanded = Path(os.path.expandvars(os.path.expanduser(str(path))))
    return expanded if expanded.is_absolute() else (APP_ROOT / expanded).resolve()


def _env(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


@lru_cache(maxsize=1)
def load_configuration() -> Dict[str, Any]:
    """Return the parsed YAML configuration as a dictionary."""

    if not CONFIG_FILE.exists() or yaml is None:
        return {}

    try:
        loaded = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        log.warning("Failed to parse %s: %s", CONFIG_FILE, exc)
        return {}

    return loaded or {}


def _path_from_config(*keys: str) -> Optional[Path]:
    cfg = load_configuration()
    for key in keys:
        value = cfg.get(key)
        if isinstance(value, str) and value.strip():
            return _expand(value)
    return None


def get_persona_root(create: bool = True) -> Path:
    """Return the directory that stores persona definitions."""

    if env := _env("PERSONA_ROOT"):
        return _expand(env)

    if (cfg_path := _path_from_config("persona_root", "persona_dir")) is not None:
        return cfg_path

    if LEGACY_PERSONA_ROOT.exists():
        return LEGACY_PERSONA_ROOT

    fallback = APP_ROOT / "personas"
    if create:
        fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def get_models_dir(create: bool = True) -> Path:
    """Return the GPT4All model directory."""

    for env in ("GPT4ALL_MODEL_DIR", "GPT4ALL_MODELS_DIR"):
        if override := _env(env):
            path = _expand(override)
            if path.exists():
                return path

    if (cfg_path := _path_from_config("models_dir", "model_dir")) is not None and cfg_path.exists():
        return cfg_path

    if local := _env("LOCALAPPDATA"):
        candidate = Path(local) / "nomic.ai" / "GPT4All"
        if candidate.exists():
            return candidate

    legacy = Path.home() / "AppData" / "Local" / "nomic.ai" / "GPT4All"
    if legacy.exists():
        return legacy

    fallback = APP_ROOT / "models"
    if create:
        fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def get_model_name(default: Optional[str] = None) -> Optional[str]:
    """Return the preferred GPT4All model filename, if one is configured."""

    if env := _env("GPT4ALL_MODEL"):
        return env

    cfg = load_configuration()
    for key in ("llm_model_name", "model", "model_name"):
        value = cfg.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return default


def get_memory_db_path() -> Path:
    """Return the SQLite database path for semantic memory."""

    if env := _env("MEMORY_DB"):
        return _expand(env)

    if (cfg_path := _path_from_config("memory_db", "db_path")) is not None:
        return cfg_path

    return APP_ROOT / "alter_ego_memory.db"


def get_log_path() -> Path:
    """Return the autosave log file path."""

    if env := _env("ALTER_EGO_LOG_PATH"):
        return _expand(env)

    if (cfg_path := _path_from_config("log_path", "autosave_log")) is not None:
        return cfg_path

    return DEFAULT_LOG_PATH


def get_default_log_path() -> Path:
    """Return the default autosave log file path."""

    return DEFAULT_LOG_PATH


def get_switch_log_path(create: bool = True) -> Path:
    """Return the persona switch log file path."""

    if env := _env("ALTER_EGO_SWITCH_LOG"):
        path = _expand(env)
    elif (cfg_path := _path_from_config("switch_log_path", "switch_log")) is not None:
        path = cfg_path
    else:
        path = APP_ROOT / "alter_switch_log.chaos"

    if create:
        path.parent.mkdir(parents=True, exist_ok=True)

    return path


def describe_data_locations() -> Dict[str, Path]:
    """Return a mapping of important runtime paths for documentation."""

    return {
        "personas": get_persona_root(create=False),
        "models": get_models_dir(create=False),
        "memory_db": get_memory_db_path(),
        "autosave_log": get_log_path(),
    }


__all__ = [
    "describe_data_locations",
    "get_default_log_path",
    "get_log_path",
    "get_memory_db_path",
    "get_model_name",
    "get_models_dir",
    "get_persona_root",
    "get_switch_log_path",
    "load_configuration",
]
