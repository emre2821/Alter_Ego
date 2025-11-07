"""Theme loading + normalisation helpers for the Alter/Ego GUI."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict

APP_DIR = Path(__file__).resolve().parent.parent
THEME_DIR = Path(os.getenv("THEME_DIR") or (APP_DIR / "themes"))

BUILTIN_THEMES: Dict[str, Dict] = {
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


def _coerce_theme_from_tokens(name: str, tokens: dict) -> dict:
    def tok(k, default):
        return tokens.get(k, default)

    bg = tok("background", "#1f1f2e")
    text_bg = tok("panel", tok("background-2", "#2e2e3f"))
    text_fg = tok("foreground", "#dcdcdc")
    entry_bg = tok("input-bg", "#3c3c50")
    entry_fg = tok("input-fg", "#ffffff")
    user_fg = tok("accent", "#85d6ff")
    alter_fg = tok("highlight", "#f5b6ff")
    font_family = tokens.get("font_family", "Consolas")
    try:
        font_size = int(tokens.get("font_size", 11))
    except Exception:
        font_size = 11

    return {
        "bg": bg,
        "text_bg": text_bg,
        "text_fg": text_fg,
        "user_fg": user_fg,
        "alter_fg": alter_fg,
        "entry_bg": entry_bg,
        "entry_fg": entry_fg,
        "font_family": font_family,
        "font_size": font_size,
        "_source": f"tokens:{name}",
    }


def _normalize_theme_json(name: str, data: dict) -> dict | None:
    if "eden_themes" in data and isinstance(data["eden_themes"], list) and data["eden_themes"]:
        default_name = data.get("default_palette")
        chosen = None
        if default_name:
            for t in data["eden_themes"]:
                if t.get("name") == default_name:
                    chosen = t
                    break
        if not chosen:
            chosen = data["eden_themes"][0]
        return _coerce_theme_from_tokens(chosen.get("name", name), chosen.get("tokens", {}))

    if "tokens" in data and isinstance(data["tokens"], dict):
        return _coerce_theme_from_tokens(data.get("name", name), data["tokens"])

    keys = {"bg", "text_bg", "text_fg", "user_fg", "alter_fg", "entry_bg", "entry_fg"}
    if any(k in data for k in keys):
        merged = BUILTIN_THEMES["dark"].copy()
        merged.update(data)
        merged.setdefault("font_family", "Consolas")
        merged.setdefault("font_size", 11)
        merged["_source"] = f"direct:{name}"
        return merged

    return None


import logging

def load_json_themes(theme_dir: Path) -> Dict[str, Dict]:
    themes: Dict[str, Dict] = {}
    if not theme_dir.exists():
        return themes
    for p in sorted(theme_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            norm = _normalize_theme_json(p.stem, data)
            if norm:
                themes[p.stem] = norm
        except Exception as e:
            logging.error(f"Failed to load theme file '{p}': {e}")
            continue
    return themes


__all__ = ["BUILTIN_THEMES", "load_json_themes", "THEME_DIR"]
