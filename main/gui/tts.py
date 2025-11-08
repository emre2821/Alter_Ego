"""Background text-to-speech loop for the GUI."""

from __future__ import annotations

import logging
import os
import queue
import threading
from typing import Optional

try:
    import pyttsx3  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pyttsx3 = None  # type: ignore

log = logging.getLogger("alter_ego_gui.tts")

_ENABLE_TTS = os.getenv("ENABLE_TTS", "1") not in {"0", "false", "False"}
_TTS_QUEUE: Optional[queue.Queue[str]] = None
_TTS_THREAD: Optional[threading.Thread] = None


def start(enable: Optional[bool] = None) -> None:
    """Start the background speech loop if TTS is available."""

    global _TTS_QUEUE, _TTS_THREAD

    if enable is None:
        enable = _ENABLE_TTS

    if not enable or pyttsx3 is None:
        return

    if _TTS_THREAD and _TTS_THREAD.is_alive():
        return

    _TTS_QUEUE = queue.Queue()

    def _loop() -> None:
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 165)
            engine.setProperty("volume", 0.9)
            while True:
                message = _TTS_QUEUE.get()
                if message is None:
                    break
                engine.say(message)
                engine.runAndWait()
        except Exception as exc:  # pragma: no cover - optional dependency errors
            log.warning("tts loop stopped: %s", exc)

    _TTS_THREAD = threading.Thread(target=_loop, daemon=True)
    _TTS_THREAD.start()


def speak(text: str) -> None:
    if _TTS_QUEUE is not None:
        _TTS_QUEUE.put(text)


def shutdown(delay: float = 0.1) -> None:
    global _TTS_QUEUE, _TTS_THREAD

    if _TTS_QUEUE is not None:
        try:
            _TTS_QUEUE.put(None)
        except Exception:
            pass
    _TTS_QUEUE = None
    _TTS_THREAD = None


__all__ = ["shutdown", "speak", "start"]
