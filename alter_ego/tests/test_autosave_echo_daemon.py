# tests/test_autosave_echo_daemon.py
import io
import autosave_echo_daemon as aed


def test_format_entry_whisper():
    entry = aed.format_chaos_entry("hi", {"whisper": "psst"})
    assert "-- Whisper: psst" in entry


def test_autosave_prompt_dir_error(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(aed, "ECHO_LOG_PATH", str(tmp_path / "no_dir" / "log.chaos"))
    monkeypatch.setattr(aed.Path, "exists", lambda self: False)

    def boom(self, parents=False, exist_ok=False):
        raise OSError("fail")
    monkeypatch.setattr(aed.Path, "mkdir", boom)
    monkeypatch.setattr("builtins.open", lambda *a, **k: io.StringIO())

    aed.autosave_prompt("hello", {})
    captured = capsys.readouterr()
    assert "[autosave_warning]" in captured.out
