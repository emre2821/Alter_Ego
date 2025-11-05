# tests/test_chaos_rag_wrapper.py
import pytest
import chaos_rag_wrapper as crw


def test_discover_model_name_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        crw._discover_model_name(tmp_path)


def test_generate_response_without_model(monkeypatch):
    monkeypatch.setattr(crw, "GPT4All", None)
    monkeypatch.setattr(crw, "get_shared_model", lambda: None)
    out = crw.generate_alter_ego_response("hi", [])
    assert "Hmm..." in out


def test_auto_mode_skips_dummy_when_no_gpt4all(monkeypatch):
    monkeypatch.setenv("ALTER_EGO_DUMMY_ONLY", "auto")
    monkeypatch.setattr(crw, "_gpt4all_reachable", lambda: False)
    monkeypatch.setattr(crw, "get_shared_model", lambda: None)
    monkeypatch.setattr(crw, "get_dummy_engine", lambda: pytest.fail("dummy should not run"))

    out = crw.generate_alter_ego_response("hello", [])
    assert "Hmm..." in out


def test_auto_mode_fallback_persists_without_backends(monkeypatch):
    monkeypatch.setenv("ALTER_EGO_DUMMY_ONLY", "auto")
    monkeypatch.setattr(crw, "_gpt4all_reachable", lambda: False)
    monkeypatch.setattr(crw, "get_shared_model", lambda: None)

    out = crw.generate_alter_ego_response("echo", [])
    assert out.startswith("Hmm...")
