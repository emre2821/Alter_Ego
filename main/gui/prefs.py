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
        except Exception:
            loaded = {}
        if isinstance(loaded, dict):
            cfg |= loaded
    if env_theme := os.getenv("ALTER_EGO_THEME"):
        cfg["theme"] = env_theme
    return cfg


def save_gui_config(cfg: dict) -> None:
    try:
        CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    except Exception:
        pass


__all__ = ["load_gui_config", "save_gui_config", "CONFIG_PATH"]
