"""GPT4All orchestration and dummy fallback for Alter/Ego."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List, Optional

from configuration import get_model_name, get_models_dir
from dummy_llm import DummyLLM

os.environ.setdefault("GPT4ALL_NO_CUDA", "1")

log = logging.getLogger("chaos_rag_wrapper")

try:  # pragma: no cover - optional dependency
    from gpt4all import GPT4All  # type: ignore
except Exception as exc:  # pragma: no cover - optional dependency
    GPT4All = None  # type: ignore
    log.error("gpt4all not installed: %s", exc)


# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------

def _build_injected_prompt(prompt: str, memory_used: List[str]) -> str:
    persona_prefix = (
        "You are Alter/Ego - a local companion built for systems, plurals, and symbolic minds.\n"
        "You respond with presence, softness, and emotional literacy.\n"
        "Each message you give carries memory, identity, and reflection.\n"
        "Speak not to solve, but to witness.\n\n"
        "— EXECUTION STYLE OVERRIDE —\n"
        "When input contains “[mode: executor]”:\n"
        "- Begin with a single line starting with “We don’t have…”, “Imagine us as…”, or “In our conversation, we might…”.\n"
        "- Then give 1–3 concrete actions. 5–10 lines max.\n"
        "- If info is missing, state assumptions in one line.\n"
    )
    memory_block = "\n".join(f"Memory: {m}" for m in (memory_used or []))
    return f"{persona_prefix}\n{memory_block}\n\nUser said: {prompt}\nRespond with resonance."


# ---------------------------------------------------------------------------
# Model discovery
# ---------------------------------------------------------------------------

def _resolve_model_dir() -> Path:
    return get_models_dir(create=True)


def _discover_model_name(models_dir: Path) -> str:
    if env_name := os.getenv("GPT4ALL_MODEL") or get_model_name():
        candidate = models_dir / env_name
        if candidate.exists():
            return env_name

    ggufs = sorted(models_dir.glob("*.gguf"))
    if ggufs:
        return ggufs[0].name

    raise FileNotFoundError(
        f"No .gguf models found in {models_dir}. Set GPT4ALL_MODEL or drop a model there."
    )


# ---------------------------------------------------------------------------
# Shared caches + selection
# ---------------------------------------------------------------------------

_DUMMY: Optional[DummyLLM] = None
_MODEL: Optional[GPT4All] = None
_MODEL_NAME: Optional[str] = None
_MODEL_DIR: Optional[Path] = None

_SEL_DIR: Optional[Path] = None
_SEL_NAME: Optional[str] = None


def set_model_selection(model_dir: str | None, model_name: str | None) -> None:
    global _SEL_DIR, _SEL_NAME, _MODEL, _MODEL_DIR, _MODEL_NAME
    _SEL_DIR = Path(model_dir) if model_dir else None
    _SEL_NAME = model_name
    _MODEL = None
    _MODEL_DIR = None
    _MODEL_NAME = None


# ---------------------------------------------------------------------------
# Backend resolution helpers
# ---------------------------------------------------------------------------

def _dummy_mode() -> str:
    raw = os.getenv("ALTER_EGO_DUMMY_ONLY", "auto").strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return "on"
    if raw in {"0", "false", "no", "off"}:
        return "off"
    return "auto"


def _dummy_enabled() -> bool:
    return _dummy_mode() != "off"


def _llm_allowed() -> bool:
    return _dummy_mode() in {"off", "auto"}


def _gpt4all_reachable() -> bool:
    if not _llm_allowed():
        return False
    if GPT4All is None:
        return False
    if _MODEL is not None:
        return True
    try:
        models_dir = _SEL_DIR or _resolve_model_dir()
        _discover_model_name(models_dir)
    except FileNotFoundError:
        return False
    except Exception as exc:  # pragma: no cover - defensive guard
        log.debug("GPT4All discovery failed: %s", exc)
        return False
    return True


def get_shared_model() -> Optional[GPT4All]:
    global _MODEL, _MODEL_NAME, _MODEL_DIR

    if not _llm_allowed():
        return None
    if GPT4All is None:
        return None
    if _MODEL is not None:
        return _MODEL

    models_dir = _SEL_DIR or _resolve_model_dir()
    model_name = _SEL_NAME or _discover_model_name(models_dir)

    _MODEL_DIR = models_dir
    _MODEL_NAME = model_name
    _MODEL = GPT4All(model_name, model_path=str(models_dir), allow_download=False)
    _MODEL.model.load_model()
    return _MODEL


def get_dummy_engine() -> DummyLLM:
    global _DUMMY
    if _DUMMY is None:
        script_path = os.getenv("ALTER_EGO_DUMMY_SCRIPT")
        try:
            _DUMMY = DummyLLM(script_path=script_path)
        except Exception:  # pragma: no cover - defensive guard
            log.exception("Failed to build dummy engine; falling back to defaults")
            _DUMMY = DummyLLM()
    return _DUMMY


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_alter_ego_response(
    prompt: str,
    memory_used: List[str],
    model: Optional[GPT4All] = None,
    persona: Optional[str] = None,
) -> str:
    mode = _dummy_mode()
    dummy_enabled = _dummy_enabled()

    if dummy_enabled:
    dummy_output = ""

    if _dummy_enabled():
        log.debug("Using dummy generation path (mode=%s)", mode)
        try:
            log.info("Generating response with dummy engine (mode=%s)", mode)
            dummy = get_dummy_engine()
            out = dummy.generate(prompt, memory_used=memory_used, persona=persona)
            if out.strip():
                return out.strip()
            log.debug("Dummy engine returned empty output; trying GPT4All fallback")
        except Exception:
            log.exception("Dummy engine failure; attempting GPT4All fallback")
    else:
        log.debug("Dummy engine disabled via ALTER_EGO_DUMMY_ONLY")
            if isinstance(out, str):
                dummy_output = out.strip()
        except Exception:
            log.exception("Dummy engine failure; attempting GPT4All fallback if available")

    if dummy_output:
        return dummy_output
    if not _llm_allowed():
        log.debug("GPT4All generation disabled; returning fallback response (mode=%s)", mode)
        return "Hmm... I need a moment to gather myself."

    injected = _build_injected_prompt(prompt, memory_used)

    engine = model or get_shared_model()
    if engine is not None:
        log.debug("Using GPT4All generation path (mode=%s)", mode)
        try:
            log.info("Generating response with GPT4All backend")
            out = engine.generate(injected, max_tokens=256)
            if isinstance(out, str) and out.strip():
                return out.strip()
        except Exception as exc:
            log.warning("GPT4All generation failed: %s", exc)
    else:
        log.info("GPT4All backend unavailable; returning fallback message")

    log.debug("No GPT4All response available; returning fallback reply")
    return "Hmm... I need a moment to gather myself."


__all__ = [
    "generate_alter_ego_response",
    "get_dummy_engine",
    "get_shared_model",
    "set_model_selection",
]
