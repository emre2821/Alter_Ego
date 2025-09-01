import os
import yaml
from pathlib import Path
from alter_ego_computer import load_config, MemoryBank, Embedder, ingest_path

def load_symbolic_config(path):
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}

def should_ignore(path, symbolic_cfg):
    ignore_globs = symbolic_cfg.get("symbolic_paths", {}).get("ignored", [])
    return any(Path(path).match(glob) for glob in ignore_globs)

def main():
    cfg = load_config(Path("alter_ego_config.yaml"))
    symbolic_cfg = load_symbolic_config(Path("symbolic_config.yaml"))
    home_dir = Path(os.path.expanduser("~"))

    print(f"[Ingest] Scanning {home_dir} recursively...")
    bank = MemoryBank(cfg)
    embedder = Embedder(cfg.embed_model_name)

    for path in home_dir.rglob("*"):
        if path.is_file() and not should_ignore(str(path), symbolic_cfg):
            try:
                ingest_path(cfg, bank, embedder, path)
            except Exception as e:
                print(f"[Skip] {path} -> {e}")

if __name__ == "__main__":
    main()
