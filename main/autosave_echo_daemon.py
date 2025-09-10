# autosave_echo_daemon.py

"""
Listens for new user prompts or reflections.
Appends CHAOS-formatted entries into a rotating echo log.
Optionally triggers rituals or check-ins.
"""

from datetime import datetime, timezone
import os
from pathlib import Path

ECHO_LOG_PATH = "chaos_echo_log.chaos"


def format_chaos_entry(prompt: str, echo_metadata: dict) -> str:
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    entry = [
        f"[EVENT]: autosave_echo",
        f"[TIME]: {now}",
        f"[CONTEXT]: prompt_catch",
        f"[SIGNIFICANCE]: MEDIUM",
    ]

    if echo_metadata.get("tremor_detected"):
        entry.append("[EMOTION:ANXIETY:HIGH]")
    if echo_metadata.get("file_overload_detected"):
        entry.append("[SYMBOL:LOOP:STRONG]")

    entry.append("{")
    entry.append(prompt.strip())
    if echo_metadata.get("whisper"):
        entry.append("\n\n-- Whisper: " + echo_metadata["whisper"])
    entry.append("}\n")

    return "\n".join(entry)


def autosave_prompt(prompt: str, echo_metadata: dict):
    """
    Saves the given prompt and echo metadata to a rotating CHAOS echo log.
    """
    entry = format_chaos_entry(prompt, echo_metadata)

    # Ensure parent directory exists, if any
    p = Path(ECHO_LOG_PATH)
    if p.parent and not p.parent.exists():
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"[autosave_warning] cannot create log dir: {e}")
    with open(p, "a", encoding="utf-8") as f:
        f.write(entry + "\n\n")

    print("[Autosave] Echo entry recorded.")
