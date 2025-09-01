"""
Adapter for CHAOS parsing. If Lyss modules are present, delegate to them.
Provides a stable `parse_chaos_file` function for Alter_Ego.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


def _delegate_parse_with_lyss(text: str) -> Dict[str, Any]:
    try:
        from Lyss.modules.chaos_parser_core import parse_chaos_block  # type: ignore

        blocks = parse_chaos_block(text)
        # Normalize into a dict schema expected by PersonaSimulator
        # Minimal extraction: tone/keywords/phrases/overrides if found
        data: Dict[str, Any] = {"_blocks": blocks}
        return data
    except Exception:
        return {"_raw": text}


def parse_chaos_file(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"_error": "file_not_found", "path": str(p)}
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return {"_error": "read_failure", "path": str(p)}

    delegated = _delegate_parse_with_lyss(text)
    if delegated:
        return delegated
    return {"_raw": text}

