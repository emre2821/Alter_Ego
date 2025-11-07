"""Model discovery helpers for the Alter/Ego GUI."""

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

    model_name = get_model_name()
    if model_name:
        candidate = models_dir / model_name
        if candidate.exists():
            return models_dir, model_name
    return models_dir, None


__all__ = ["resolve_models_dir", "list_models", "current_selection"]
