import builtins
import importlib
import sys
import types


def import_without_yaml(monkeypatch, module_name: str):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("No module named 'yaml'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)
    monkeypatch.delitem(sys.modules, "yaml", raising=False)
    monkeypatch.setitem(
        sys.modules,
        "alter_ego_computer",
        types.SimpleNamespace(
            load_config=lambda path: None,
            MemoryBank=object,
            Embedder=object,
            ingest_path=lambda *args, **kwargs: None,
            watch_path=lambda *args, **kwargs: None,
        ),
    )
    monkeypatch.delitem(sys.modules, module_name, raising=False)
    return importlib.import_module(module_name)


def test_ingest_module_loads_without_pyyaml(monkeypatch, tmp_path):
    module = import_without_yaml(monkeypatch, "ingest_entire_system")

    missing_config = tmp_path / "symbolic_config.yaml"
    assert module.load_symbolic_config(missing_config) == {}


def test_watchdog_module_loads_without_pyyaml(monkeypatch, tmp_path):
    module = import_without_yaml(monkeypatch, "chaos_watchdog")

    missing_config = tmp_path / "symbolic_config.yaml"
    assert module.load_symbolic_config(missing_config) == {}
