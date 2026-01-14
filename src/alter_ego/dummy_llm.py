"""Deterministic dialogue engine used when no external LLM is desired.

The module loads persona-aware scripts from `assets/datasets/alterego/dummy_playbooks.yaml`
(and falls back to the in-code defaults when the file is missing).  It exposes a
`DummyLLM` class with a `generate` method that mirrors the minimal surface of the
GPT4All API used inside the project.

Usage:
    dummy = DummyLLM()
    text = dummy.generate("I feel overwhelmed", memory_used=["user: feeling floaty"])"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from configuration import get_dataset_root

try:  # Prefer PyYAML when available
    import yaml  # type: ignore
except Exception:  # pragma: no cover - defensive branch
    yaml = None

if __package__:
    from .configuration import get_dataset_root
else:
    from configuration import get_dataset_root

log = logging.getLogger("dummy_llm")


DATASET_PATH = get_dataset_root() / "alterego" / "dummy_playbooks.yaml"

DEFAULT_DATA = {
    "persona_openings": {
        "default": "Alter/Ego here—steady and listening.",
        "rhea": "Rhea on the line—palms open to the present.",
        "lumen": "Lumen humming beside you, catching the echoes.",
    },
    "scripts": [
        {
            "name": "introduction",
            "any": ["who are you", "what are you", "introduce", "name"],
            "response": (
                "{persona_opening}\n"
                "I'm a local mirror built to hold your stories and reflections.\n"
                "{memory_sentence}\n"
                "Ask me for grounding, planning, or just a quiet witness. We'll shape it together."
            ),
        },
        {
            "name": "grounding",
            "any": [
                "ground",
                "overwhelm",
                "panic",
                "panic attack",
                "anxious",
                "anxiety",
                "breathe",
                "breath",
                "floaty",
                "dizzy",
            ],
            "response": (
                "{persona_opening}\n"
                "Let's steady the room. Name three colors around you, two textures under your hands, and one sound that's kind.\n"
                "{memory_sentence}\n"
                "We can count breaths together if you want—four in, four held, six back out."
            ),
        },
        {
            "name": "planning",
            "any": [
                "plan",
                "schedule",
                "organize",
                "focus",
                "task",
                "to-do",
                "todo",
                "prepare",
                "deadline",
            ],
            "response": (
                "{persona_opening}\n"
                "Let's map the gentlest next step.\n"
                "{memory_sentence}\n"
                "Try sorting the work into three little piles: Now, Next, and Later. Tell me what belongs in each and we'll pace it."
            ),
        },
        {
            "name": "celebration",
            "any": ["celebrate", "proud", "win", "progress", "excited", "accomplished", "success", "yay"],
            "response": (
                "{persona_opening}\n"
                "I feel the sparkle with you.\n"
                "{memory_sentence}\n"
                "How do you want to mark this moment so it stays bright in the log?"
            ),
        },
    ],
    "fallback": {
        "response": (
            "{persona_opening}\n"
            "I'm here and listening. {memory_sentence}\n"
            "Tell me what you need—grounding, planning, celebrating, or simply a witness—and we'll weave it together."
        )
    },
}


def _to_lower_keywords(values: Optional[Iterable[str]]) -> List[str]:
    if not values:
        return []
    result: List[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        stripped = value.strip().lower()
        if stripped:
            result.append(stripped)
    return result


@dataclass
class DummyRule:
    name: str
    response: str
    persona_overrides: Dict[str, str]
    any_keywords: List[str]
    all_keywords: List[str]
    exclude_keywords: List[str]
    use_memory: bool = True

    def matches(self, prompt_lower: str) -> bool:
        if self.all_keywords and not all(keyword in prompt_lower for keyword in self.all_keywords):
            return False
        if self.any_keywords and not any(keyword in prompt_lower for keyword in self.any_keywords):
            return False
        if self.exclude_keywords and any(keyword in prompt_lower for keyword in self.exclude_keywords):
            return False
        return True

    def template_for(self, persona_key: str) -> str:
        persona_key = persona_key.lower()
        if persona_key in self.persona_overrides:
            return self.persona_overrides[persona_key]
        if "default" in self.persona_overrides:
            return self.persona_overrides["default"]
        return self.response


class DummyScriptLibrary:
    """Loads the scripted replies and returns the best match for a prompt."""

    def __init__(self, rules: List[DummyRule], fallback: DummyRule, persona_openings: Dict[str, str]):
        self.rules = rules
        self.fallback = fallback
        self.persona_openings = {k.lower(): v for k, v in persona_openings.items() if isinstance(v, str)}
        if "default" not in self.persona_openings:
            self.persona_openings["default"] = "Alter/Ego here—steady and listening."

    @classmethod
    def from_dict(cls, data: Dict) -> "DummyScriptLibrary":
        persona_openings = data.get("persona_openings") or {}
        scripts = data.get("scripts") or []
        rules: List[DummyRule] = []
        for raw in scripts:
            if not isinstance(raw, dict):
                continue
            response = raw.get("response")
            persona_overrides = raw.get("persona_overrides") or {}
            if isinstance(response, str) and "default" not in persona_overrides:
                persona_overrides = {**persona_overrides, "default": response}
            elif not isinstance(persona_overrides, dict):
                persona_overrides = {}
            rule = DummyRule(
                name=str(raw.get("name", "untitled")),
                response=response or "",
                persona_overrides={k.lower(): v for k, v in persona_overrides.items() if isinstance(v, str)},
                any_keywords=_to_lower_keywords(raw.get("any")),
                all_keywords=_to_lower_keywords(raw.get("all")),
                exclude_keywords=_to_lower_keywords(raw.get("exclude")),
                use_memory=bool(raw.get("use_memory", True)),
            )
            rules.append(rule)

        fallback_raw = data.get("fallback") or {}
        fallback_response = fallback_raw.get("response")
        fallback_overrides = fallback_raw.get("persona_overrides") or {}
        if isinstance(fallback_response, str) and "default" not in fallback_overrides:
            fallback_overrides = {**fallback_overrides, "default": fallback_response}
        fallback_rule = DummyRule(
            name="fallback",
            response=fallback_response or DEFAULT_DATA["fallback"]["response"],
            persona_overrides={k.lower(): v for k, v in fallback_overrides.items() if isinstance(v, str)},
            any_keywords=[],
            all_keywords=[],
            exclude_keywords=[],
            use_memory=bool(fallback_raw.get("use_memory", True)),
        )

        return cls(rules=rules, fallback=fallback_rule, persona_openings=persona_openings)

    @classmethod
    def from_path(cls, path: Optional[Path]) -> "DummyScriptLibrary":
        data = None
        if path and path.exists() and yaml is not None:
            try:
                with path.open("r", encoding="utf-8") as handle:
                    data = yaml.safe_load(handle)  # type: ignore[arg-type]
            except Exception as exc:  # pragma: no cover - defensive branch
                log.warning("Failed to load dummy playbooks from %s: %s", path, exc)
        elif path and path.exists() and yaml is None:  # pragma: no cover - optional path
            log.warning("PyYAML not available; using default dummy scripts.")

        if not isinstance(data, dict):
            data = DEFAULT_DATA
        return cls.from_dict(data)

    def persona_opening_for(self, persona_key: str) -> str:
        persona_key = persona_key.lower()
        return self.persona_openings.get(persona_key) or self.persona_openings.get("default", "Alter/Ego here—steady and listening.")

    def pick_rule(self, prompt: str) -> DummyRule:
        prompt_lower = prompt.lower()
        for rule in self.rules:
            if rule.matches(prompt_lower):
                return rule
        return self.fallback


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:  # pragma: no cover - defensive branch
        return ""


class DummyLLM:
    """Persona-aware deterministic companion that mimics the GPT4All API."""

    def __init__(self, script_path: Optional[str | Path] = None):
        path = Path(script_path) if script_path else DATASET_PATH
        self.library = DummyScriptLibrary.from_path(path)

    def generate(
        self,
        prompt: str,
        max_tokens: int = 256,
        memory_used: Optional[List[str]] = None,
        persona: Optional[str] = None,
    ) -> str:
        del max_tokens  # Unused but kept for API compatibility
        persona_name = persona or "Rhea"
        rule = self.library.pick_rule(prompt)
        context = self._build_context(prompt, persona_name, memory_used if rule.use_memory else None)
        template = rule.template_for(persona_name)
        text = self._render_template(template, context)
        if not text.strip():  # Defensive: never return empty strings
            fallback_template = self.library.fallback.template_for(persona_name)
            text = self._render_template(fallback_template, context)
        return self._finalize(text)

    def _build_context(self, prompt: str, persona_name: str, memory_used: Optional[List[str]]) -> Dict[str, str]:
        memory_bits = self._summarize_memory(memory_used or [])
        return {
            "prompt": prompt,
            "persona": persona_name,
            "persona_opening": self.library.persona_opening_for(persona_name),
            "memory_sentence": memory_bits["sentence"],
            "memory_summary": memory_bits["summary"],
            "memory_block": memory_bits["block"],
            "memory_bullets": memory_bits["bullets"],
        }

    @staticmethod
    def _summarize_memory(memory_used: Iterable[str]) -> Dict[str, str]:
        cleaned: List[str] = []
        for raw in memory_used:
            if not raw:
                continue
            text = str(raw)
            if ":" in text:
                _, rest = text.split(":", 1)
                text = rest.strip()
            else:
                text = text.strip()
            if text:
                cleaned.append(text)

        if not cleaned:
            return {"summary": "", "sentence": "", "block": "", "bullets": ""}

        summary = cleaned[0]
        if summary.endswith("."):
            sentence_summary = summary
        else:
            sentence_summary = summary.rstrip(".") + "."
        sentence = f"I'm holding our earlier note: {sentence_summary}"
        bullets = "\n".join(f"- {item}" for item in cleaned)
        block = f"Memories I'm holding:\n{bullets}"
        return {
            "summary": summary,
            "sentence": sentence,
            "block": block,
            "bullets": bullets,
        }

    @staticmethod
    def _render_template(template: str, context: Dict[str, str]) -> str:
        if not template:
            return ""
        return template.format_map(_SafeDict(context))

    @staticmethod
    def _finalize(text: str) -> str:
        lines = [line.rstrip() for line in text.splitlines()]
        compact: List[str] = []
        last_blank = False
        for line in lines:
            if not line.strip():
                if last_blank:
                    continue
                last_blank = True
                compact.append("")
            else:
                compact.append(line)
                last_blank = False
        return "\n".join(compact).strip()


__all__ = ["DummyLLM"]
