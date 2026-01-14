"""Theme discovery helpers for the Alter/Ego GUI."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, Iterable

from configuration import get_theme_root

log = logging.getLogger("alter_ego_gui.themes")

APP_DIR = Path(__file__).resolve().parent.parent
DEFAULT_THEME_DIR = get_theme_root()

BUILTIN_THEMES: Dict[str, Dict[str, object]] = {
    "eden": {
        "bg": "#101820",
        "text_bg": "#0f2740",
        "text_fg": "#e0f7fa",
        "user_fg": "#29b6f6",
        "alter_fg": "#ff80ab",
        "entry_bg": "#1c2b36",
        "entry_fg": "#ffffff",
        "font_family": "Corbel",
        "font_size": 18,
    },
    "dark": {
        "bg": "#1f1f2e",
        "text_bg": "#2e2e3f",
        "text_fg": "#dcdcdc",
        "user_fg": "#85d6ff",
        "alter_fg": "#f5b6ff",
        "entry_bg": "#3c3c50",
        "entry_fg": "#ffffff",
        "font_family": "Consolas",
        "font_size": 11,
    },
    "light": {
        "bg": "#fafafa",
        "text_bg": "#ffffff",
        "text_fg": "#222222",
        "user_fg": "#0044cc",
        "alter_fg": "#880088",
        "entry_bg": "#f0f0f0",
        "entry_fg": "#000000",
        "font_family": "Segoe UI",
        "font_size": 12,
    },
}


LEGACY_THEME_DIRS: Iterable[Path] = (
    APP_DIR / "config" / "themes",
    APP_DIR.parent / "themes",
)


def discover_theme_dir() -> Path:
    """Return the directory that should be scanned for JSON themes."""

    if env_dir := os.getenv("THEME_DIR"):
        path = Path(env_dir).expanduser()
        if path.exists():
            return path
        log.warning("THEME_DIR=%s does not exist; falling back to defaults", env_dir)

    if DEFAULT_THEME_DIR.exists():
        return DEFAULT_THEME_DIR

    for legacy in LEGACY_THEME_DIRS:
        if legacy.exists():
            log.warning(
                "Using legacy theme directory at %s; move themes into assets/themes or set THEME_DIR.",
                legacy,
            )
            return legacy

    return DEFAULT_THEME_DIR


def _normalize_theme_json(name: str, data: object) -> Dict[str, object] | None:
    if not isinstance(data, dict):
        log.warning("theme %s is not a JSON object; skipping", name)
        return None

    base = BUILTIN_THEMES.get(name, {})
    merged = dict(base)
    merged.update(data)

    required = {"bg", "text_bg", "text_fg", "user_fg", "alter_fg"}
    if missing := required - merged.keys():
        log.warning("theme %s missing keys: %s", name, ", ".join(sorted(missing)))
        return None

    normalized = dict(merged)
    normalized.setdefault("entry_bg", normalized["text_bg"])
    normalized.setdefault("entry_fg", normalized["text_fg"])
    normalized.setdefault("font_family", "Segoe UI")
    normalized.setdefault("font_size", 12)
    return normalized


def load_json_themes(theme_dir: Path) -> Dict[str, Dict[str, object]]:
    """Load ``*.json`` themes from ``theme_dir``."""

    themes: Dict[str, Dict[str, object]] = {}
    if not theme_dir.exists():
        return themes

    for path in theme_dir.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("could not read theme %s: %s", path.name, exc)
            continue

        if normalized := _normalize_theme_json(path.stem, data):
            themes[path.stem] = normalized
    return themes


def available_themes(theme_dir: Path) -> Dict[str, Dict[str, object]]:
    """Return merged builtin + JSON themes."""

    merged = dict(BUILTIN_THEMES)
    merged |= load_json_themes(theme_dir)
    return merged


__all__ = [
    "BUILTIN_THEMES",
    "available_themes",
    "discover_theme_dir",
    "load_json_themes",
]
