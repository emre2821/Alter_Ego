# tests/test_alter_shell.py
import alter_shell


def test_interact_boot_message(monkeypatch):
    monkeypatch.setattr(alter_shell.AlterShell, "_warm_start", lambda self: None)
    shell = alter_shell.AlterShell()
    shell._model_ready.clear()
    msg = shell.interact("hi")
    assert "Booting" in msg


def test_interact_handles_memory_failure(monkeypatch):
    monkeypatch.setattr(alter_shell.AlterShell, "_warm_start", lambda self: None)
    shell = alter_shell.AlterShell()
    shell._model_ready.set()

    def boom(*args, **kwargs):
        raise RuntimeError("db broke")

    monkeypatch.setattr(alter_shell, "search", boom)
    monkeypatch.setattr(alter_shell, "mem_add", lambda *a, **k: None)
    monkeypatch.setattr(alter_shell, "autosave_prompt", lambda *a, **k: None)
    monkeypatch.setattr(alter_shell, "generate_alter_ego_response", lambda p, memory_used, model: "llm")

    class DummyEcho:
        def respond(self, user_input, llm_output):
            return "final", {}
    shell.echo_response = DummyEcho()

    out = shell.interact("test")
    assert out == "final"


def test_interact_skips_persona_for_stub_without_kwarg(monkeypatch):
    monkeypatch.setattr(alter_shell.AlterShell, "_warm_start", lambda self: None)
    shell = alter_shell.AlterShell()
    shell._model_ready.set()

    monkeypatch.setattr(alter_shell, "search", lambda *a, **k: [])
    monkeypatch.setattr(alter_shell, "mem_add", lambda *a, **k: None)
    monkeypatch.setattr(alter_shell, "autosave_prompt", lambda *a, **k: None)

    captured = {}

    def stub_generate(prompt, memory_used, model):
        captured["called"] = True
        captured["memory_used"] = memory_used
        captured["model"] = model
        return "llm"

    monkeypatch.setattr(alter_shell, "generate_alter_ego_response", stub_generate)

    class DummyEcho:
        def respond(self, user_input, llm_output):
            return "final", {}

    shell.echo_response = DummyEcho()

    out = shell.interact("hello")

    assert out == "final"
    assert captured.get("called") is True
    assert shell._supports_persona_kw is False


def test_interact_retries_when_persona_kw_is_rejected(monkeypatch):
    monkeypatch.setattr(alter_shell.AlterShell, "_warm_start", lambda self: None)
    shell = alter_shell.AlterShell()
    shell._model_ready.set()

    monkeypatch.setattr(alter_shell, "search", lambda *a, **k: [])
    monkeypatch.setattr(alter_shell, "mem_add", lambda *a, **k: None)
    monkeypatch.setattr(alter_shell, "autosave_prompt", lambda *a, **k: None)

    calls = []

    def stub_generate(prompt, memory_used, model, **kwargs):
        calls.append(kwargs)
        if "persona" in kwargs:
            raise TypeError("persona not supported here")
        return "llm"

    monkeypatch.setattr(alter_shell, "generate_alter_ego_response", stub_generate)

    class DummyEcho:
        def respond(self, user_input, llm_output):
            return "final", {}

    shell.echo_response = DummyEcho()

    out = shell.interact("retry")

    assert out == "final"
    assert calls[0] == {"persona": shell.fronting.get_active() or "Rhea"}
    assert calls[1] == {}
    assert shell._supports_persona_kw is False
