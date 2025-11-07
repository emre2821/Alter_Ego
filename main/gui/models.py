"""Helpers for discovering GPT4All model folders used by the GUI."""

from __future__ import annotations

from pathlib import Path

from configuration import get_models_dir


def default_models_dir() -> Path:
    path = get_models_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_models(models_dir: Path) -> list[str]:
    try:
        return sorted(p.name for p in models_dir.glob("*.gguf"))
    except Exception:
        return []


__all__ = ["default_models_dir", "list_models"]
