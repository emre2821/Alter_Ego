"""Runtime configuration helpers for Alter/Ego.

This module centralizes discovery of folders and filenames that were
previously scattered across the GUI and runtime helpers.  The exported
functions resolve locations based on the shipped ``alter_ego_config.yaml``
file and allow environment variables to override every setting.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional
import os

try:
    import yaml
except Exception:  # pragma: no cover - yaml is an optional dependency
    yaml = None

APP_ROOT = Path(__file__).resolve().parent
CONFIG_FILE = APP_ROOT / "alter_ego_config.yaml"


def _expand(path: str) -> Path:
    """Return ``path`` expanded relative to :data:`APP_ROOT`.

    ``alter_ego_config.yaml`` historically stored relative paths.  We keep
    that behaviour by treating entries as relative to the repository root
    unless they are already absolute.
    """

    candidate = Path(os.path.expandvars(os.path.expanduser(path)))
    if candidate.is_absolute():
        return candidate
    return APP_ROOT / candidate


@lru_cache(maxsize=1)
def load_configuration() -> Dict[str, Any]:
    """Return the merged configuration dictionary.

    The YAML file is optional – an empty dict is returned when parsing
    fails.  Environment variables are *not* applied at this layer; each
    accessor performs its own override logic so the original contents stay
    visible to callers that need raw values.
    """

    if not CONFIG_FILE.exists() or yaml is None:
        return {}

    try:
        data = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data or {}


def _env(name: str) -> Optional[str]:
    value = os.getenv(name)
    if value:
        return value.strip() or None
    return None


def get_persona_root() -> Path:
    """Return the directory that stores persona definitions."""

    env_override = _env("PERSONA_ROOT")
    if env_override:
        return _expand(env_override)

    cfg = load_configuration()
    cfg_path = cfg.get("persona_root")
    if isinstance(cfg_path, str) and cfg_path:
        return _expand(cfg_path)

    # Legacy Lyss path used by early installations.
    legacy = Path(r"C:\EdenOS_Origin\all_daemons")
    if legacy.exists():
        return legacy

    return APP_ROOT / "personas"


def get_models_dir(create: bool = True) -> Path:
    """Return the GPT4All model directory.

    ``create`` controls whether the fallback local folder is created when it
    does not already exist.
    """

    for env in ("GPT4ALL_MODEL_DIR", "GPT4ALL_MODELS_DIR"):
        env_override = _env(env)
        if env_override and Path(env_override).expanduser().exists():
            return Path(env_override).expanduser()

    cfg = load_configuration()
    cfg_path = cfg.get("models_dir")
    if isinstance(cfg_path, str) and cfg_path:
        expanded = _expand(cfg_path)
        if expanded.exists():
            return expanded

    localappdata = _env("LOCALAPPDATA")
    if localappdata:
        candidate = Path(localappdata) / "nomic.ai" / "GPT4All"
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

    env_name = _env("GPT4ALL_MODEL")
    if env_name:
        return env_name

    cfg = load_configuration()
    name = cfg.get("llm_model_name")
    if isinstance(name, str) and name:
        return name

    return default


def get_memory_db_path() -> Path:
    """Return the SQLite database used for memory embeddings."""

    env_override = _env("MEMORY_DB")
    if env_override:
        return _expand(env_override)

    cfg = load_configuration()
    cfg_path = cfg.get("db_path") or cfg.get("memory_db")
    if isinstance(cfg_path, str) and cfg_path:
        return _expand(cfg_path)

    return APP_ROOT / "alter_ego_memory.db"


def get_log_path() -> Path:
    """Return the default autosave log path."""

    env_override = _env("ALTER_EGO_LOG_PATH")
    if env_override:
        return _expand(env_override)

    cfg = load_configuration()
    cfg_path = cfg.get("log_path")
    if isinstance(cfg_path, str) and cfg_path:
        return _expand(cfg_path)

    return APP_ROOT / "chaos_echo_log.chaos"


def describe_data_locations() -> Dict[str, Path]:
    """Return a snapshot of the important runtime paths."""

    return {
        "personas": get_persona_root(),
        "models": get_models_dir(create=False),
        "memory_db": get_memory_db_path(),
        "autosave_log": get_log_path(),
    }
