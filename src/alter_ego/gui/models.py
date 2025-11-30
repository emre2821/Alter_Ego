"""Helpers for discovering GPT4All model folders used by the GUI."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Tuple

from configuration import get_model_name, get_models_dir

log = logging.getLogger("alter_ego_gui.models")

STARTER_MODEL = "DeepSeek-R1-Distill-Qwen-1.5B-Q4_0.gguf"


def resolve_models_dir(create: bool = True) -> Path:
    """Return the directory that should be displayed in the Models menu."""

    return get_models_dir(create=create)


def list_models(models_dir: Path) -> List[str]:
    """Return sorted ``.gguf`` model filenames available under ``models_dir``."""

    try:
        return sorted(p.name for p in models_dir.glob("*.gguf"))
    except Exception:  # pragma: no cover - defensive logging
        log.exception("Failed to list models in directory: %s", models_dir)
        return []


def current_selection(models_dir: Path) -> Tuple[Path, Optional[str]]:
    """Return the (dir, filename) pair that should be pre-selected."""

    if model_name := get_model_name():
        candidate = models_dir / model_name
        if candidate.exists():
            return models_dir, model_name
    return models_dir, None


def starter_model_path(models_dir: Path) -> Path:
    """Return the recommended starter model location."""

    return models_dir / STARTER_MODEL


__all__ = [
    "STARTER_MODEL",
    "current_selection",
    "list_models",
    "resolve_models_dir",
    "starter_model_path",
]
