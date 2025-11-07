"""Persistent GUI preferences (theme, Prismari, selected model)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json
import logging
import os


log = logging.getLogger("alter_ego_gui.prefs")

APP_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = APP_DIR / "gui_config.json"

_DEFAULT_PREFS: Dict[str, Any] = {
    "theme": "eden",
    "model": None,
    "prismari_enabled": True,
}


def load_gui_config() -> Dict[str, Any]:
    """Load persisted GUI configuration, falling back to defaults."""

    prefs = dict(_DEFAULT_PREFS)
    if CONFIG_PATH.exists():
        try:
            loaded = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("[config_warning] could not read %s: %s", CONFIG_PATH, exc)
        else:
            if isinstance(loaded, dict):
                prefs.update(loaded)

    if env_theme := os.getenv("ALTER_EGO_THEME"):
        prefs["theme"] = env_theme

    return prefs


def save_gui_config(prefs: Dict[str, Any]) -> None:
    """Persist GUI configuration to disk."""

    try:
        serialized_prefs = json.dumps(prefs, indent=2)
    except (TypeError, ValueError) as exc:
        log.warning("[config_warning] could not serialize prefs: %s", exc)
        return

    try:
        CONFIG_PATH.write_text(serialized_prefs, encoding="utf-8")
    except OSError as exc:
        log.warning("[config_warning] could not write %s: %s", CONFIG_PATH, exc)


__all__ = ["load_gui_config", "save_gui_config", "CONFIG_PATH"]
