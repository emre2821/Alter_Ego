"""Alter/Ego package initializer and lightweight text-to-speech wrapper."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_pkg_root = Path(__file__).parent
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))


class AlterEgo:
    """Minimal text-to-speech assistant powered by ``pyttsx3``."""

    def __init__(self, **engine_kwargs: Any) -> None:
        import pyttsx3

        self.engine = pyttsx3.init(**engine_kwargs)

    def speak(self, text: str) -> None:
        """Speak the supplied ``text`` aloud."""

        self.engine.say(text)
        self.engine.runAndWait()


__all__ = ["AlterEgo"]
