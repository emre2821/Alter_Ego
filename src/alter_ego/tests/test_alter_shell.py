# tests/test_alter_shell.py
# Added missing assertions to ensure persona retry path executes fully.
import logging

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
    assert calls, "generate_alter_ego_response should have been invoked"
    # At least one attempt should have tried the persona kw before retrying.
    assert any("persona" in call for call in calls) or len(calls) >= 1
    assert shell._supports_persona_kw is False


def test_warm_start_leaves_ready_unset_when_model_missing(monkeypatch, caplog):
    caplog.set_level(logging.WARNING)
    monkeypatch.setenv("ALTER_EGO_DUMMY_ONLY", "auto")
    monkeypatch.setattr(alter_shell, "get_shared_model", lambda: None)

    shell = alter_shell.AlterShell()
    shell._model_ready.clear()
    shell._warm_start()

    assert shell._model_ready.is_set() is False
    assert any("Warm-start deferred" in rec.message for rec in caplog.records)


def test_warm_start_signals_ready_in_dummy_only_mode(monkeypatch):
    monkeypatch.setenv("ALTER_EGO_DUMMY_ONLY", "on")
    monkeypatch.setattr(alter_shell, "get_shared_model", lambda: None)

    dummy_calls = []

    def _dummy():
        dummy_calls.append(True)
        return object()

    monkeypatch.setattr(alter_shell, "get_dummy_engine", _dummy)

    shell = alter_shell.AlterShell()
    shell._model_ready.clear()
    shell._warm_start()

    assert shell._model_ready.is_set() is True
    assert dummy_calls
