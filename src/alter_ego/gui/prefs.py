"""Persistent GUI preferences (theme, Prismari, selected model)."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict

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
            log.warning("could not read %s: %s", CONFIG_PATH, exc)
        else:
            if isinstance(loaded, dict):
                prefs |= loaded
            else:  # pragma: no cover - defensive guard
                log.warning(
                    "expected dict in %s but received %s", CONFIG_PATH, type(loaded).__name__
                )
    if env_theme := os.getenv("ALTER_EGO_THEME"):
        prefs["theme"] = env_theme
    return prefs


def save_gui_config(prefs: Dict[str, Any]) -> None:
    """Persist GUI configuration to disk atomically."""

    try:
        serialized = json.dumps(prefs, indent=2)
    except (TypeError, ValueError) as exc:
        log.warning("could not serialize GUI prefs: %s", exc)
        return

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    with NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=str(CONFIG_PATH.parent), delete=False
    ) as tmp:
        tmp.write(serialized)
        tmp_path = Path(tmp.name)

    try:
        os.replace(tmp_path, CONFIG_PATH)
    except OSError as exc:
        log.warning("could not write %s: %s", CONFIG_PATH, exc)
        try:
            tmp_path.unlink()
        except OSError:
            pass


__all__ = ["CONFIG_PATH", "load_gui_config", "save_gui_config"]
