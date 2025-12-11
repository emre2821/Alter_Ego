import json

import pytest

from chaos_parser_core import (
    _fallback_parse_persona_fields,
    _normalize_keywords,
    _normalize_overrides,
    _normalize_phrases,
)


def test_normalize_keywords_handles_list_and_string_and_none():
    # list inputs are preserved
    assert _normalize_keywords(["blaze", "spark"]) == ["blaze", "spark"]

    # delimited strings are split and trimmed
    keywords = _normalize_keywords("blaze, spark;ember")
    assert keywords == ["blaze", "spark", "ember"]

    # None becomes an empty list
    assert _normalize_keywords(None) == []

    # whitespace-only string yields no keywords
    assert _normalize_keywords("   ") == []

    # mixed list values are trimmed, whitespace-only entries dropped, and non-strings coerced
    assert _normalize_keywords([" foo ", " ", 123]) == ["foo", "123"]

    # non-list / non-string inputs are coerced to string and wrapped in a list
    assert _normalize_keywords(12345) == ["12345"]


def test_normalize_phrases_splits_on_semicolons_and_newlines():
    text = "Ignite now;Feel the heat\nLine three"
    phrases = _normalize_phrases(text)
    assert phrases == ["Ignite now", "Feel the heat", "Line three"]


def test_normalize_overrides_accepts_dict_and_json_string_and_invalid_json():
    overrides_dict = {"hello": "hiya", "yes": "yep"}
    assert _normalize_overrides(overrides_dict) == overrides_dict

    overrides_json = json.dumps(overrides_dict)
    parsed = _normalize_overrides(overrides_json)
    assert parsed == overrides_dict

    invalid_json = "{not: valid"
    parsed_invalid = _normalize_overrides(invalid_json)
    assert isinstance(parsed_invalid, dict)
    assert parsed_invalid == {}


@pytest.mark.parametrize(
    "label_variant",
    ["persona", "PERSONA", "PeRsOnA"],
)
def test_fallback_parse_persona_fields_mixed_case_labels(label_variant):
    chaos_persona = (
        f"[{label_variant}]: Blaze\n"
        "[tOnE]: Fiery\n"
        "[Keywords]: blaze, spark;ember\n"
        "[phrases]: Ignite now;Feel the heat\n"
        "[Overrides]: {\"hello\": \"hiya\", \"yes\": \"yep\"}\n"
    )

    fields = _fallback_parse_persona_fields(chaos_persona)

    assert fields["persona"] == "Blaze"
    assert fields["tone"].lower() == "fiery"
    assert fields["keywords"] == ["blaze", "spark", "ember"]
    assert fields["phrases"] == ["Ignite now", "Feel the heat"]
    assert fields["overrides"] == {"hello": "hiya", "yes": "yep"}
import persona_fronting
from alter_ego.chaos_parser_core import _normalize_overrides
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


def test_normalize_overrides_accepts_dict_and_json_string_and_invalid_json():
    overrides_dict = {"hello": "hiya", "yes": "yep"}
    assert _normalize_overrides(overrides_dict) == overrides_dict

    overrides_json = json.dumps(overrides_dict)
    parsed = _normalize_overrides(overrides_json)
    assert parsed == overrides_dict

    invalid_json = "{not: valid"
    parsed_invalid = _normalize_overrides(invalid_json)
    assert isinstance(parsed_invalid, dict)
    assert parsed_invalid == {}

    none_overrides = _normalize_overrides(None)
    assert isinstance(none_overrides, dict)
    assert none_overrides == {}

    non_dict_json = _normalize_overrides("[1, 2]")
    assert isinstance(non_dict_json, dict)
    assert non_dict_json == {}

    non_string_input = _normalize_overrides(123)
    assert isinstance(non_string_input, dict)
    assert non_string_input == {}
