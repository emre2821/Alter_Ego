# tests/test_memory_digester.py
import configuration
from configuration import (
    describe_data_locations,
    get_assets_root,
    get_config_path,
    get_constitution_path,
    get_dataset_root,
    get_gui_config_path,
    get_persona_root,
    get_symbolic_config_path,
    get_theme_root,
    load_config,
    save_config,
)
from memory_digester import MemoryDigester
from persona_simulator import PersonaSimulator


def test_memory_digest_log(tmp_path):
    mem_dir = tmp_path / "memories"
    mem_dir.mkdir(parents=True, exist_ok=True)

    test_file = mem_dir / "note.chaos"
    test_file.write_text("I remember the ocean.")

    sim = PersonaSimulator(get_persona_root())
    digester = MemoryDigester(mem_dir, sim, pace=0)
    digester.walk_folder("Rhea")

    assert len(digester.digest_log) == 1


def _assert_under_assets_root(path, assets_root):
    assert path == assets_root or assets_root in path.parents


def test_configuration_helpers_resolve_under_assets_root():
    assets_root = get_assets_root(create=False)

    paths = [
        get_persona_root(create=False),
        get_config_path(),
        get_symbolic_config_path(),
        get_gui_config_path(),
        get_dataset_root(create=False),
        get_theme_root(create=False),
        get_constitution_path(),
    ]

    for path in paths:
        _assert_under_assets_root(path, assets_root)

    locations = describe_data_locations()
    assert "assets_root" in locations
    assert locations["assets_root"] == assets_root


def test_load_and_save_config_create_missing_parent_dirs(tmp_path, monkeypatch):
    nested_config_path = tmp_path / "nested" / "deeper" / "config.yaml"

    monkeypatch.setattr(configuration, "CONFIG_PATH", nested_config_path, raising=False)

    data = {"foo": "bar"}

    save_config(data)
    assert nested_config_path.exists()
    assert nested_config_path.parent.is_dir()

    loaded = load_config()
    assert isinstance(loaded, dict)
    assert loaded.get("foo") == "bar"
