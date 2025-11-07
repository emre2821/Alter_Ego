"""Background text-to-speech loop for the Alter/Ego GUI."""

from __future__ import annotations

from typing import Optional
import queue
import threading
import os
"""Background text-to-speech loop for the GUI."""

from __future__ import annotations

import os
import queue
import threading
import time
from typing import Optional

try:
    import pyttsx3  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pyttsx3 = None

_ENABLE_TTS = os.getenv("ENABLE_TTS", "1") != "0"
_tts_queue: Optional[queue.Queue[str]] = None
_tts_thread: Optional[threading.Thread] = None


def start(enable: Optional[bool] = None) -> None:
    """Start the background speech loop if TTS is available."""

    global _tts_queue, _tts_thread

    if enable is None:
        enable = _ENABLE_TTS

    if not enable or pyttsx3 is None:
        return

    if _tts_thread and _tts_thread.is_alive():
        return

    _tts_queue = queue.Queue()

    def _loop():
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 165)
            engine.setProperty("volume", 0.9)
            while True:
                message = _tts_queue.get()
                if message is None:
                    break
                engine.say(message)
                engine.runAndWait()
        except Exception as exc:
            print(f"[tts_warning] {exc}")

    _tts_thread = threading.Thread(target=_loop, daemon=True)
    _tts_thread.start()


def speak(text: str) -> None:
    if _tts_queue is not None:
        _tts_queue.put(text)


def shutdown() -> None:
    global _tts_queue, _tts_thread

    if _tts_queue is not None:
        try:
            _tts_queue.put(None)
        except Exception:
            pass
    _tts_queue = None
    _tts_thread = None


__all__ = ["start", "speak", "shutdown"]
    pyttsx3 = None  # type: ignore

ENABLE_TTS = os.getenv("ENABLE_TTS", "1") != "0"
_TTS_Q: Optional[queue.Queue[str]] = None
_TTS_THREAD: Optional[threading.Thread] = None


def start_tts_loop() -> None:
    global _TTS_Q, _TTS_THREAD
    if not (ENABLE_TTS and pyttsx3 is not None):
        return
    if _TTS_THREAD and _TTS_THREAD.is_alive():
        return

    _TTS_Q = queue.Queue()

    def _loop():
        try:
            eng = pyttsx3.init()
            eng.setProperty("rate", 165)
            eng.setProperty("volume", 0.9)
            while True:
                msg = _TTS_Q.get()
                if msg is None:
                    break
                eng.say(msg)
                eng.runAndWait()
        except Exception:
            pass

    _TTS_THREAD = threading.Thread(target=_loop, daemon=True)
    _TTS_THREAD.start()


def speak(text: str) -> None:
    if _TTS_Q is not None:
        _TTS_Q.put(text)


def shutdown_tts(delay: float = 0.1) -> None:
    try:
        if _TTS_Q is not None:
            _TTS_Q.put(None)
    except Exception:
        pass
    if delay:
        time.sleep(delay)


__all__ = ["start_tts_loop", "speak", "shutdown_tts"]
