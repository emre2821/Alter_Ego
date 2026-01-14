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
ASSETS_DIRNAME = "assets"
DEFAULT_CONFIG_FILENAME = "alter_ego_config.yaml"
DEFAULT_SYMBOLIC_CONFIG_FILENAME = "symbolic_config.yaml"
DEFAULT_GUI_CONFIG_FILENAME = "gui_config.json"
DEFAULT_CONSTITUTION_FILENAME = "eden.constitution.agent.chaosrights"
DEFAULT_DATASET_DIRNAME = "datasets"
DEFAULT_THEME_DIRNAME = "themes"
DEFAULT_PERSONA_DIRNAME = "personas"

ASSETS_ROOT = APP_ROOT / ASSETS_DIRNAME
CONFIG_FILE = APP_ROOT / DEFAULT_CONFIG_FILENAME
CONFIG_PATH = CONFIG_FILE
SYMBOLIC_CONFIG_PATH = APP_ROOT / DEFAULT_SYMBOLIC_CONFIG_FILENAME
GUI_CONFIG_PATH = APP_ROOT / DEFAULT_GUI_CONFIG_FILENAME
CONSTITUTION_PATH = APP_ROOT / DEFAULT_CONSTITUTION_FILENAME

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

    config_path = get_config_path()
    if not config_path.exists() or yaml is None:
        return {}

    try:
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except Exception as exc:
        log.warning("Failed to parse %s: %s", config_path, exc)
        return {}

    return loaded or {}


def _path_from_config(*keys: str) -> Optional[Path]:
    cfg = load_configuration()
    for key in keys:
        value = cfg.get(key)
        if isinstance(value, str) and value.strip():
            return _expand(value)
    return None


def _default_assets_root() -> Path:
    if env := _env("ALTER_EGO_ASSETS_ROOT"):
        return _expand(env)
    if env := _env("ASSETS_ROOT"):
        return _expand(env)
    return ASSETS_ROOT if ASSETS_ROOT.exists() else APP_ROOT


def get_assets_root(create: bool = True) -> Path:
    """Return the directory that stores Alter/Ego assets."""

    root = _default_assets_root()
    if create:
        root.mkdir(parents=True, exist_ok=True)
    return root


def _resolve_assets_subdir(dirname: str, legacy_path: Path, create: bool) -> Path:
    assets_root = get_assets_root(create=create)
    assets_path = assets_root / dirname
    if assets_root != APP_ROOT:
        if create:
            assets_path.mkdir(parents=True, exist_ok=True)
        return assets_path
    if create:
        legacy_path.mkdir(parents=True, exist_ok=True)
    return legacy_path


def _resolve_assets_file(filename: str, legacy_path: Path) -> Path:
    assets_root = get_assets_root(create=False)
    assets_path = assets_root / filename
    if assets_root != APP_ROOT:
        return assets_path
    return legacy_path


def get_config_path() -> Path:
    """Return the path to the main Alter/Ego configuration file."""

    if env := _env("ALTER_EGO_CONFIG_PATH"):
        return _expand(env)
    if CONFIG_PATH != CONFIG_FILE:
        return CONFIG_PATH
    if CONFIG_FILE != APP_ROOT / DEFAULT_CONFIG_FILENAME:
        return CONFIG_FILE
    return _resolve_assets_file(DEFAULT_CONFIG_FILENAME, CONFIG_FILE)


def get_symbolic_config_path() -> Path:
    """Return the path to the symbolic configuration file."""

    if env := _env("ALTER_EGO_SYMBOLIC_CONFIG_PATH"):
        return _expand(env)
    return _resolve_assets_file(DEFAULT_SYMBOLIC_CONFIG_FILENAME, SYMBOLIC_CONFIG_PATH)


def get_gui_config_path() -> Path:
    """Return the path to the GUI configuration file."""

    if env := _env("ALTER_EGO_GUI_CONFIG_PATH"):
        return _expand(env)
    return _resolve_assets_file(DEFAULT_GUI_CONFIG_FILENAME, GUI_CONFIG_PATH)


def get_constitution_path() -> Path:
    """Return the path to the Eden constitution file."""

    if env := _env("ALTER_EGO_CONSTITUTION_PATH"):
        return _expand(env)
    return _resolve_assets_file(DEFAULT_CONSTITUTION_FILENAME, CONSTITUTION_PATH)


def get_dataset_root(create: bool = True) -> Path:
    """Return the directory that stores dataset assets."""

    if env := _env("ALTER_EGO_DATASET_ROOT"):
        path = _expand(env)
    elif env := _env("DATASET_ROOT"):
        path = _expand(env)
    else:
        legacy = APP_ROOT / DEFAULT_DATASET_DIRNAME
        return _resolve_assets_subdir(DEFAULT_DATASET_DIRNAME, legacy, create=create)
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def get_theme_root(create: bool = True) -> Path:
    """Return the directory that stores theme assets."""

    if env := _env("ALTER_EGO_THEME_ROOT"):
        path = _expand(env)
    elif env := _env("THEME_DIR"):
        path = _expand(env)
    else:
        legacy = APP_ROOT / DEFAULT_THEME_DIRNAME
        return _resolve_assets_subdir(DEFAULT_THEME_DIRNAME, legacy, create=create)
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def get_persona_root(create: bool = True) -> Path:
    """Return the directory that stores persona definitions."""

    if env := _env("PERSONA_ROOT"):
        path = _expand(env)
        if create:
            path.mkdir(parents=True, exist_ok=True)
        return path

    if (cfg_path := _path_from_config("persona_root", "persona_dir")) is not None:
        return cfg_path

    if LEGACY_PERSONA_ROOT.exists():
        return LEGACY_PERSONA_ROOT

    legacy = APP_ROOT / DEFAULT_PERSONA_DIRNAME
    return _resolve_assets_subdir(DEFAULT_PERSONA_DIRNAME, legacy, create=create)


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


def get_default_log_path() -> Path:
    """Return the default autosave log file path."""

    return DEFAULT_LOG_PATH


def get_log_path() -> Path:
    """Return the autosave log file path."""

    if env := _env("ALTER_EGO_LOG_PATH"):
        return _expand(env)

    if (cfg_path := _path_from_config("log_path", "autosave_log")) is not None:
        return cfg_path

    return get_default_log_path()


def get_switch_log_path(create: bool = False) -> Path:
    """Return the persona switch log file path.

    When ``create`` is True, missing parent directories are created to ensure
    the returned path is writable.
    """

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
        "assets_root": get_assets_root(create=False),
        "personas": get_persona_root(create=False),
        "models": get_models_dir(create=False),
        "datasets": get_dataset_root(create=False),
        "themes": get_theme_root(create=False),
        "memory_db": get_memory_db_path(),
        "autosave_log": get_log_path(),
    }


def load_config(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the YAML config file from the configured path."""

    config_path = path or get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if yaml is None or not config_path.exists():
        return {}

    try:
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except Exception as exc:
        log.warning("Failed to parse %s: %s", config_path, exc)
        return {}

    return loaded or {}


def save_config(data: Dict[str, Any], path: Optional[Path] = None) -> None:
    """Persist configuration data to disk as YAML."""

    config_path = path or get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if yaml is None:
        log.warning("PyYAML is unavailable; cannot save %s", config_path)
        return

    config_path.write_text(
        yaml.safe_dump(data, sort_keys=False),
        encoding="utf-8",
    )


__all__ = [
    "describe_data_locations",
    "get_assets_root",
    "get_config_path",
    "get_constitution_path",
    "get_dataset_root",
    "get_default_log_path",
    "get_gui_config_path",
    "get_log_path",
    "get_memory_db_path",
    "get_model_name",
    "get_models_dir",
    "get_persona_root",
    "get_symbolic_config_path",
    "get_switch_log_path",
    "get_theme_root",
    "load_config",
    "load_configuration",
    "save_config",
]
