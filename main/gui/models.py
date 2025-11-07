"""Model discovery helpers for the Alter/Ego GUI."""
"""Helpers for discovering GPT4All model folders used by the GUI."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

from configuration import get_models_dir, get_model_name


def resolve_models_dir() -> Path:
    """Return the directory that should be displayed in the Models menu."""

    return get_models_dir(create=True)


def list_models(models_dir: Path) -> List[str]:
    try:
        return sorted(p.name for p in models_dir.glob("*.gguf"))
    except Exception:
        return []


def current_selection(models_dir: Path) -> Tuple[Path, Optional[str]]:
    """Return the (dir, filename) pair that should be pre-selected."""

    if model_name := get_model_name():
        candidate = models_dir / model_name
        if candidate.exists():
            return models_dir, model_name
    return models_dir, None


__all__ = ["resolve_models_dir", "list_models", "current_selection"]

from configuration import get_models_dir


def default_models_dir() -> Path:
    path = get_models_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


import logging

def list_models(models_dir: Path) -> list[str]:
    try:
        return sorted(p.name for p in models_dir.glob("*.gguf"))
    except Exception as e:
        logging.exception("Failed to list models in directory: %s", models_dir)
        return []


__all__ = ["default_models_dir", "list_models"]
