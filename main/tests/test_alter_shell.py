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
