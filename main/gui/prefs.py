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
            if isinstance(
                loaded := json.loads(CONFIG_PATH.read_text(encoding="utf-8")), dict
            ):
                prefs |= loaded
        except (json.JSONDecodeError, OSError) as exc:
            print(f"[config_warning] could not read {CONFIG_PATH}: {exc}")
        except Exception as exc:
            print(f"[config_warning] could not read {CONFIG_PATH}: {exc}")
            if isinstance(loaded := json.loads(CONFIG_PATH.read_text(encoding="utf-8")), dict):
            loaded = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("[config_warning] could not read %s: %s", CONFIG_PATH, exc)
        else:
            if isinstance(loaded, dict):
                prefs |= loaded
            else:
                log.warning(
                    "[config_warning] expected dict in %s but got %s",
                    CONFIG_PATH,
                    type(loaded).__name__,
                )
                prefs.update(loaded)

    if env_theme := os.getenv("ALTER_EGO_THEME"):
        prefs["theme"] = env_theme

    return prefs


def save_gui_config(prefs: Dict[str, Any]) -> None:
    """Persist GUI configuration to disk atomically."""

    try:
        serialized_prefs = json.dumps(prefs, indent=2)
    except (TypeError, ValueError) as exc:
        log.warning("[config_warning] could not serialize prefs: %s", exc)
        return

    temp_path: Path | None = None
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(CONFIG_PATH.parent),
            delete=False,
        ) as temp_file:
            temp_file.write(serialized_prefs)
            temp_path = Path(temp_file.name)
        os.replace(temp_path, CONFIG_PATH)
    except OSError as exc:
        log.warning("[config_warning] could not write %s: %s", CONFIG_PATH, exc)
        if temp_path is not None:
            try:
                temp_path.unlink()
            except OSError:
                pass
        data = json.dumps(prefs, indent=2)
    except TypeError as exc:
        log.warning("[config_warning] could not serialize prefs: %s", exc)
        return

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    temp_path = None
    try:
        with NamedTemporaryFile(
            "w", encoding="utf-8", dir=CONFIG_PATH.parent, delete=False
        ) as tmp_file:
            temp_path = Path(tmp_file.name)
            tmp_file.write(data)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        temp_path.replace(CONFIG_PATH)
    except OSError as exc:
        log.warning("[config_warning] could not write %s: %s", CONFIG_PATH, exc)
        if temp_path is not None and temp_path.exists():
            temp_path.unlink(missing_ok=True)
        serialized_prefs = json.dumps(prefs, indent=2)
    except (TypeError, ValueError) as exc:
        log.warning("[config_warning] could not serialize prefs: %s", exc)
        return

    try:
        CONFIG_PATH.write_text(serialized_prefs, encoding="utf-8")
    except OSError as exc:
        CONFIG_PATH.write_text(json.dumps(prefs, indent=2), encoding="utf-8")
    except (OSError, TypeError) as exc:
        log.warning("[config_warning] could not write %s: %s", CONFIG_PATH, exc)


__all__ = ["load_gui_config", "save_gui_config", "CONFIG_PATH"]
