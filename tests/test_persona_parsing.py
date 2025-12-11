import persona_fronting
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
