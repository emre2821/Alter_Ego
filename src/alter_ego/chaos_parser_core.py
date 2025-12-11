"""
Adapter for CHAOS parsing. If Lyss modules are present, delegate to them.
Provides a stable `parse_chaos_file` function for Alter_Ego.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable


def _delegate_parse_with_lyss(text: str) -> Dict[str, Any] | None:
    try:
        from Lyss.modules.chaos_parser_core import parse_chaos_block  # type: ignore

        blocks = parse_chaos_block(text)
        return {"_blocks": blocks}
    except Exception:
        return None


def _normalize_keywords(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        parts = re.split(r"[;,]", value)
        return [p.strip() for p in parts if p.strip()]
    return []


def _normalize_phrases(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [s for v in value if (s := str(v).strip())]
    if isinstance(value, str):
        parts = re.split(r"[;\n]", value)
        return [p.strip() for p in parts if p.strip()]
    return []


def _normalize_overrides(value: Any) -> Dict[str, str]:
    if isinstance(value, dict):
        return {str(k): str(v) for k, v in value.items()}
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return {str(k): str(v) for k, v in parsed.items()}
        except Exception:
            pass
    return {}


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


def _fallback_parse_persona_fields(text: str) -> Dict[str, Any]:
    fields: Dict[str, Any] = {}
    patterns: Iterable[tuple[str, str]] = (
        ("tone", r"^[\[]?TONE[\]]?\s*:\s*(.+)$"),
        ("keywords", r"^[\[]?KEYWORDS[\]]?\s*:\s*(.+)$"),
        ("phrases", r"^[\[]?PHRASES[\]]?\s*:\s*(.+)$"),
        ("overrides", r"^[\[]?OVERRIDES[\]]?\s*:\s*(.+)$"),
        ("name", r"^[\[]?PERSONA[\]]?\s*:\s*(.+)$"),
    )

    for line in text.splitlines():
        for key, pattern in patterns:
            match = re.match(pattern, line.strip(), flags=re.IGNORECASE)
            if match:
                fields[key] = match.group(1).strip()

    if "tone" in fields:
        fields["tone"] = str(fields["tone"])
    if "keywords" in fields:
        fields["keywords"] = _normalize_keywords(fields["keywords"])
    if "phrases" in fields:
        fields["phrases"] = _normalize_phrases(fields["phrases"])
    if "overrides" in fields:
        fields["overrides"] = _normalize_overrides(fields["overrides"])
    if "name" in fields:
        fields["name"] = str(fields["name"])

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
    if name is not None:
        normalized_fields["name"] = str(name)

    result.update(normalized_fields)
    if not delegated:
        result.setdefault("_raw", text)
    return result

