import os
from pathlib import Path
from alter_ego_computer import load_config, MemoryBank, Embedder, watch_path

def load_symbolic_config(path: Path) -> dict:
    try:
        import yaml  # type: ignore
    except Exception:
        return {}

    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}

def resolve_watch_root(symbolic_cfg: dict) -> Path:
    paths = symbolic_cfg.get("symbolic_paths", {}).get("threads", [])
    for raw in paths:
        p = Path(os.path.expanduser(os.path.expandvars(raw)))
        if p.exists():
            return p
        print(f"[Watchdog] Skipping missing path: {p}")
    return Path.home()

def main():
    cfg = load_config(Path("alter_ego_config.yaml"))
    symbolic_cfg = load_symbolic_config(Path("symbolic_config.yaml"))
    cfg.ignore_globs.extend(symbolic_cfg.get("symbolic_paths", {}).get("ignored", []))
    watch_root = resolve_watch_root(symbolic_cfg)

    print(f"[Watchdog] Watching {watch_root}...")
    bank = MemoryBank(cfg)
    embedder = Embedder(cfg.embed_model_name)

    watch_path(cfg, bank, embedder, watch_root)

if __name__ == "__main__":
    main()
