import time
import yaml
from pathlib import Path
from alter_ego_computer import load_config, MemoryBank, Embedder, watch_path

def load_symbolic_config(path):
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}

def main():
    cfg = load_config(Path("alter_ego_config.yaml"))
    symbolic_cfg = load_symbolic_config(Path("symbolic_config.yaml"))
    watch_root = Path(os.path.expanduser("~"))

    print(f"[Watchdog] Watching {watch_root}...")
    bank = MemoryBank(cfg)
    embedder = Embedder(cfg.embed_model_name)

    watch_path(cfg, bank, embedder, watch_root, symbolic_cfg)

if __name__ == "__main__":
    main()
