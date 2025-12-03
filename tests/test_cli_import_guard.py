import builtins
import importlib
import sys


def test_import_without_typer(monkeypatch):
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "typer":
            raise ImportError("typer missing")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    sys.modules.pop("alter_ego_computer", None)

    module = importlib.import_module("alter_ego_computer")

    assert module.TYPER_OK is False
    assert module.app is None
    assert module.parse_embed_model_name("fastembed:model") == ("fastembed", "model")

    sys.modules.pop("alter_ego_computer", None)
