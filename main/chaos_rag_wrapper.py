# chaos_rag_wrapper.py
# Centralizes GPT4All prompt build + shared model cache (CPU-only by default).
from __future__ import annotations
from typing import List, Optional
import logging
import os
from pathlib import Path

from dummy_llm import DummyLLM
from configuration import get_model_name, get_models_dir

os.environ.setdefault("GPT4ALL_NO_CUDA", "1")
log = logging.getLogger("chaos_rag_wrapper")

try:
    from gpt4all import GPT4All  # type: ignore
except Exception as e:
    GPT4All = None  # type: ignore
    logging.error("gpt4all not installed: %s", e)

# ---------- Prompt build ----------
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

def _discover_models_dir() -> Path:
    return get_models_dir()


def _resolve_model_name(models_dir: Path) -> str:
    configured = os.getenv("GPT4ALL_MODEL") or get_model_name()
    if configured and (models_dir / configured).exists():
        return configured

    ggufs = sorted(models_dir.glob("*.gguf"))
    if not ggufs:
        raise FileNotFoundError(
            f"No .gguf models found in {models_dir}. Set GPT4ALL_MODEL or drop a model there."
        )
    return ggufs[0].name


def _discover_model_name(models_dir: Path) -> str:
    return _resolve_model_name(models_dir)

# ---------- Shared model cache + selection ----------
# Dummy engine cache (shared across calls)
_DUMMY: Optional[DummyLLM] = None

_MODEL: Optional[GPT4All] = None
_MODEL_NAME: Optional[str] = None
_MODEL_DIR: Optional[Path] = None

# GUI selection (dir/name); if unset, we auto-discover
_SEL_DIR: Optional[Path] = None
_SEL_NAME: Optional[str] = None


def set_model_selection(model_dir: str | None, model_name: str | None):
    """Called by AlterShell when the user picks a model (or clears selection)."""
    global _SEL_DIR, _SEL_NAME, _MODEL, _MODEL_DIR, _MODEL_NAME
    _SEL_DIR = Path(model_dir) if model_dir else None
    _SEL_NAME = model_name
    # Clear cached engine so the next request rebuilds using the new selection.
    _MODEL = None
    _MODEL_DIR = None
    _MODEL_NAME = None


def _dummy_mode() -> str:
    """Return configured dummy mode: 'on', 'off', or 'auto'."""
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
    """Best-effort detection that a GPT4All backend/model can be used."""

    if not _llm_allowed():
        return False

    if _MODEL is not None:
        return True

    if GPT4All is None:
        return False

    try:
        models_dir = _SEL_DIR or get_models_dir()
        _ = _SEL_NAME or _resolve_model_name(models_dir)
    except FileNotFoundError:
        return False
    except Exception as exc:  # pragma: no cover - defensive guard
        logging.debug("GPT4All discovery failed: %s", exc)
        return False

    return True


def get_shared_model() -> Optional[GPT4All]:
    """Build/reuse a single GPT4All instance respecting the current selection."""
    global _MODEL, _MODEL_NAME, _MODEL_DIR

    if not _llm_allowed():
        return None
    if GPT4All is None:
        return None
    if _MODEL is not None:
        return _MODEL

    models_dir = _SEL_DIR or get_models_dir()
    model_name = _SEL_NAME or _resolve_model_name(models_dir)

    _MODEL_DIR = models_dir
    _MODEL_NAME = model_name
    _MODEL = GPT4All(_MODEL_NAME, model_path=str(_MODEL_DIR), allow_download=False)
    # Explicit warm load so first token is snappy
    _MODEL.model.load_model()
    return _MODEL


def get_dummy_engine() -> DummyLLM:
    global _DUMMY
    if _DUMMY is None:
        script_path = os.getenv("ALTER_EGO_DUMMY_SCRIPT")
        try:
            _DUMMY = DummyLLM(script_path=script_path)
        except Exception:  # pragma: no cover - defensive guard
            logging.exception("Failed to build dummy engine; falling back to defaults")
            _DUMMY = DummyLLM()
    return _DUMMY

# ---------- Public API ----------
def generate_alter_ego_response(
    prompt: str,
    memory_used: List[str],
    model: Optional[GPT4All] = None,
    persona: Optional[str] = None,
) -> str:
    mode = _dummy_mode()
    gpt4all_available = model is not None or _gpt4all_reachable()
    dummy_allowed = mode == "on" or (mode == "auto" and gpt4all_available)

    if mode == "auto" and not gpt4all_available:
        logging.debug(
            "Auto mode fallback: no GPT4All backend/model reachable; skipping dummy engine"
        )

    if dummy_allowed:
        try:
            dummy = get_dummy_engine()
            out = dummy.generate(prompt, memory_used=memory_used, persona=persona)
            if out.strip():
                return out.strip()
        except Exception:
            logging.exception("Dummy engine failure; attempting GPT4All fallback")

    injected = _build_injected_prompt(prompt, memory_used)

    engine = model or get_shared_model()
    if engine is not None:
        try:
            out = engine.generate(injected, max_tokens=256)
            if isinstance(out, str) and out.strip():
                return out.strip()
        except Exception as e:
            logging.warning("[gpt4all_warning] %s", e)

    # Fallback stub
    return f"Hmm... That stirred something. Let's sit with it a moment. (Prompt was: '{prompt}')"
