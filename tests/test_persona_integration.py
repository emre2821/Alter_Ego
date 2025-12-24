# Integration-style persona tests separated for clarity after earlier concatenation.
import pytest

import configuration
import persona_fronting
from chaos_parser_core import (
    _fallback_parse_persona_fields,
    _normalize_keywords,
    _normalize_overrides,
    _normalize_phrases,
    parse_chaos_file,
)
from persona_fronting import PersonaFronting
from persona_simulator import PersonaSimulator


def test_chaos_persona_attributes_applied(tmp_path):
    chaos_persona = """[PERSONA]: Blaze
[TONE]: fiery
[KEYWORDS]: blaze, spark;ember
[PHRASES]: Ignite now;Feel the heat
[OVERRIDES]: {\"hello\": \"hiya\", \"yes\": \"yep\"}
"""

    persona_file = tmp_path / "Blaze.chaos"
    persona_file.write_text(chaos_persona, encoding="utf-8")

    simulator = PersonaSimulator(persona_dir=tmp_path)
    persona = simulator.personas["Blaze"]

    assert persona.tone == "fiery"
    assert persona.keywords == ["blaze", "spark", "ember"]
    assert persona.phrases == ["Ignite now", "Feel the heat"]
    assert persona.overrides == {"hello": "hiya", "yes": "yep"}

    styled = persona.style_response("hello and yes")
    assert "hiya and yep" in styled
    assert styled.endswith("[Blaze]")


def test_resolve_switch_log_path_respects_create_flag(tmp_path, monkeypatch):
    target = tmp_path / "nested" / "switch.chaos"

    def fake_get_switch_log_path(create: bool = True):
        if create:
            target.parent.mkdir(parents=True, exist_ok=True)
        return target

    monkeypatch.setattr(persona_fronting, "get_switch_log_path", fake_get_switch_log_path)

    assert not target.parent.exists()

    resolved = PersonaFronting._resolve_switch_log_path(create=False)
    assert resolved == target
    assert not target.parent.exists()

    pf = PersonaFronting()
    pf.refresh_switch_log()
    assert target.parent.exists()


def test_switch_log_creates_custom_path_parent(monkeypatch, tmp_path):
    custom_path = tmp_path / "nested" / "switch.chaos"
    monkeypatch.setenv("ALTER_EGO_SWITCH_LOG", str(custom_path))

    pf = PersonaFronting()

    assert not custom_path.parent.exists()

    resolved = pf.switch_log

    assert resolved == custom_path
    assert custom_path.parent.exists()


def test_switch_log_creates_default_path_parent(monkeypatch, tmp_path):
    monkeypatch.delenv("ALTER_EGO_SWITCH_LOG", raising=False)

    root = tmp_path / "app_root"
    monkeypatch.setattr(configuration, "APP_ROOT", root)
    monkeypatch.setattr(configuration, "CONFIG_FILE", root / "alter_ego_config.yaml")
    configuration.load_configuration.cache_clear()

    pf = PersonaFronting()

    expected = root / "alter_switch_log.chaos"
    assert not expected.parent.exists()

    resolved = pf.switch_log

    assert resolved == expected
    assert expected.parent.exists()

    configuration.load_configuration.cache_clear()


def test_parse_chaos_file_merges_delegate_and_fallback(monkeypatch, tmp_path):
    chaos_content = """[PERSONA]: Base Name
[TONE]: mellow
[KEYWORDS]: base, keywords
[PHRASES]: hello;world
[OVERRIDES]: {\"tone\": \"friendly\"}
"""

    chaos_file = tmp_path / "persona.chaos"
    chaos_file.write_text(chaos_content, encoding="utf-8")

    fallback_persona = _fallback_parse_persona_fields(chaos_content)
    expected_normalized = {
        "tone": fallback_persona.get("tone", "neutral"),
        "keywords": _normalize_keywords(fallback_persona.get("keywords")),
        "phrases": _normalize_phrases(fallback_persona.get("phrases")),
        "overrides": _normalize_overrides(fallback_persona.get("overrides")),
        "name": fallback_persona.get("name"),
    }

    delegated_result = {
        "_blocks": {},
        "tone": "delegated tone",  # should be overridden by normalized fallback field
        "delegate_only_field": "value",
    }

    def fake_delegate(text: str):
        return delegated_result

    monkeypatch.setattr("chaos_parser_core._delegate_parse_with_lyss", fake_delegate)

    result = parse_chaos_file(str(chaos_file))

    assert result["delegate_only_field"] == "value"
    assert result["tone"] == expected_normalized["tone"]
    assert result["keywords"] == expected_normalized["keywords"]
    assert result["phrases"] == expected_normalized["phrases"]
    assert result["overrides"] == expected_normalized["overrides"]
    assert result["name"] == expected_normalized["name"]


def test_parse_chaos_file_uses_fallback_when_delegate_falsey(monkeypatch, tmp_path):
    chaos_content = """[PERSONA]: Fallback Only
[TONE]: focused
[KEYWORDS]: only, fallback
[PHRASES]: just;fallback
[OVERRIDES]: {\"tone\": \"serious\"}
"""

    chaos_file = tmp_path / "persona_fallback_only.chaos"
    chaos_file.write_text(chaos_content, encoding="utf-8")

    monkeypatch.setattr("chaos_parser_core._delegate_parse_with_lyss", lambda _: None)

    result = parse_chaos_file(str(chaos_file))

    fallback_persona = _fallback_parse_persona_fields(chaos_content)
    expected_normalized = {
        "tone": fallback_persona.get("tone", "neutral"),
        "keywords": _normalize_keywords(fallback_persona.get("keywords")),
        "phrases": _normalize_phrases(fallback_persona.get("phrases")),
        "overrides": _normalize_overrides(fallback_persona.get("overrides")),
        "name": fallback_persona.get("name"),
    }

    assert result == {
        **expected_normalized,
        "_raw": chaos_content,
    }
