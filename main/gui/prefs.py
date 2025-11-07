"""Persistent GUI preferences (theme, Prismari, selected model)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json
import os

APP_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = APP_ROOT / "gui_config.json"

_DEFAULT_PREFS: Dict[str, Any] = {
    "theme": "eden",
    "model": None,
    "prismari_enabled": True,
}


def load_gui_config() -> Dict[str, Any]:
    prefs = dict(_DEFAULT_PREFS)
    if CONFIG_PATH.exists():
        try:
            loaded = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                prefs.update(loaded)
        except (json.JSONDecodeError, OSError) as exc:
                prefs |= loaded
        except Exception as exc:
            print(f"[config_warning] could not read {CONFIG_PATH}: {exc}")

    env_theme = os.getenv("ALTER_EGO_THEME")
    if env_theme:
        prefs["theme"] = env_theme

    return prefs


def save_gui_config(prefs: Dict[str, Any]) -> None:
    try:
        CONFIG_PATH.write_text(json.dumps(prefs, indent=2), encoding="utf-8")
    except OSError as exc:
        print(f"[config_warning] could not write {CONFIG_PATH}: {exc}")
"""Persisted GUI preferences (theme + selected model)."""

from __future__ import annotations

import json
import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = APP_DIR / "gui_config.json"


def load_gui_config() -> dict:
    cfg = {"theme": "eden", "model": None, "prismari_enabled": True}
    if CONFIG_PATH.exists():
        try:
            loaded = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            loaded = {}
        if isinstance(loaded, dict):
            cfg |= loaded
    if env_theme := os.getenv("ALTER_EGO_THEME"):
        cfg["theme"] = env_theme
    return cfg


def save_gui_config(cfg: dict) -> None:
    try:
        CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    except OSError:
        pass


__all__ = ["load_gui_config", "save_gui_config", "CONFIG_PATH"]
