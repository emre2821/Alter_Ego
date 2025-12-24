"""
Adapter for CHAOS parsing. If Lyss modules are present, delegate to them.
Provides a stable `parse_chaos_file` function for Alter_Ego.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable


def _normalize_keywords(raw: Any) -> list[str]:
    """Normalize keyword input into a list of trimmed strings."""

    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    if isinstance(raw, str):
        parts = re.split(r"[;,]", raw)
        return [part.strip() for part in parts if part.strip()]
    # Fallback: coerce to string if it has content
    raw_str = str(raw).strip()
    return [raw_str] if raw_str else []


def _normalize_phrases(raw: Any) -> list[str]:
    """Normalize phrases by splitting on semicolons and newlines."""

    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    text = str(raw)
    parts = re.split(r"[;\n]", text)
    return [part.strip() for part in parts if part.strip()]


def _normalize_overrides(raw: Any) -> dict[str, Any]:
    """Normalize overrides provided as a mapping or JSON string."""

    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _fallback_parse_persona_fields(text: str) -> Dict[str, Any]:
    """Parse persona fields from CHAOS-style blocks without Lyss."""

    pattern = re.compile(r"\[\s*(?P<label>[^\]]+?)\s*\]\s*:\s*(?P<value>.*)")
    raw_fields: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.lstrip()
        if match := pattern.match(line):
            label = match.group("label").strip().lower()
            raw_fields[label] = match.group("value").strip()

    persona = raw_fields.get("persona") or raw_fields.get("name") or ""
    tone = raw_fields.get("tone") or raw_fields.get("style") or ""
    keywords = _normalize_keywords(raw_fields.get("keywords"))
    phrases = _normalize_phrases(raw_fields.get("phrases"))
    overrides = _normalize_overrides(raw_fields.get("overrides"))

    return {
        "persona": persona,
        "tone": tone,
        "keywords": keywords,
        "phrases": phrases,
        "overrides": overrides,
    }


def _delegate_parse_with_lyss(text: str) -> Dict[str, Any] | None:
    try:
        from Lyss.modules.chaos_parser_core import parse_chaos_block  # type: ignore

        blocks = parse_chaos_block(text)
        return {"_blocks": blocks}
    except Exception:
        return None


def _extract_persona_fields(blocks: Any) -> Dict[str, Any]:
    fields: Dict[str, Any] = {}

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            for key in ("name", "tone", "keywords", "phrases", "overrides"):
                if key in node and node[key] is not None:
                    fields[key] = node[key]
            for child in node.values():
                visit(child)
        elif isinstance(node, (list, tuple, set)):
            for child in node:
                visit(child)

    visit(blocks)
    return fields


def parse_chaos_file(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"_error": "file_not_found", "path": str(p)}
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return {"_error": "read_failure", "path": str(p)}

    result: Dict[str, Any] = {}
    delegated = _delegate_parse_with_lyss(text)
    if delegated:
        result.update(delegated)

    persona_fields = _extract_persona_fields(result.get("_blocks", {})) if delegated else {}
    if not persona_fields:
        persona_fields = _fallback_parse_persona_fields(text)

    normalized_fields = {
        "tone": persona_fields.get("tone", "neutral"),
        "keywords": _normalize_keywords(persona_fields.get("keywords")),
        "phrases": _normalize_phrases(persona_fields.get("phrases")),
        "overrides": _normalize_overrides(persona_fields.get("overrides")),
    }
    name = persona_fields.get("name")
    normalized_fields["name"] = str(name) if name is not None else None

    result.update(normalized_fields)
    if not delegated:
        result.setdefault("_raw", text)
    return result
