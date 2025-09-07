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
