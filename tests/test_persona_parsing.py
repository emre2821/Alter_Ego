import json

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
