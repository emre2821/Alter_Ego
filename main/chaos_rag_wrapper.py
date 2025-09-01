# chaos_rag_wrapper.py

"""
Retrieves memory, injects tone and persona, and returns LLM output.
Prefers local GPT4All models if available; otherwise falls back to a stub.
"""

from typing import List, Optional
from pathlib import Path
import os


def _build_injected_prompt(prompt: str, memory_used: List[str]) -> str:
    persona_prefix = (
        "You are Alter/Ego - a local companion built for systems, plurals, and symbolic minds.\n"
        "You respond with presence, softness, and emotional literacy.\n"
        "Each message you give carries memory, identity, and reflection.\n"
        "Speak not to solve, but to witness.\n"
    )
    memory_block = "\n".join(f"Memory: {m}" for m in (memory_used or []))
    return f"{persona_prefix}\n{memory_block}\n\nUser said: {prompt}\nRespond with resonance."


def _try_gpt4all(injected_prompt: str) -> Optional[str]:
    try:
        from gpt4all import GPT4All  # type: ignore
    except Exception:
        return None

    models_dir = os.getenv("GPT4ALL_MODELS_DIR", r"C:\\Users\\emmar\\AppData\\Local\\nomic.ai\\GPT4All")
    model_hint = os.getenv("GPT4ALL_MODEL")  # e.g., DeepSeek-*.gguf
    mdir = Path(models_dir)
    if not mdir.exists():
        return None

    model_name: Optional[str] = None
    if model_hint:
        hint_path = mdir / model_hint
        # Accept exact filename or just basename present in dir
        if hint_path.exists():
            model_name = hint_path.name
        else:
            # If only basename provided and exists, accept
            for cand in mdir.glob("*.gguf"):
                if cand.name == model_hint:
                    model_name = cand.name
                    break

    if not model_name:
        ggufs = sorted(mdir.glob("*.gguf"))
        if ggufs:
            model_name = ggufs[0].name

    if not model_name:
        return None

    try:
        engine = GPT4All(model_name, model_path=str(mdir), allow_download=False)
        out = engine.generate(injected_prompt, max_tokens=256)
        return (out or "").strip()
    except Exception as e:
        print(f"[gpt4all_warning] {e}")
        return None


def generate_alter_ego_response(prompt: str, memory_used: List[str]) -> str:
    injected_prompt = _build_injected_prompt(prompt, memory_used)

    # Try GPT4All if available and a model exists in the configured dir
    out = _try_gpt4all(injected_prompt)
    if isinstance(out, str) and out.strip():
        return out

    # Fallback stub
    return f"Hmm... That stirred something. Let's sit with it a moment. (Prompt was: '{prompt}')"
