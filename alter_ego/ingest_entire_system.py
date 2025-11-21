import os
import yaml
from pathlib import Path
from alter_ego_computer import load_config, MemoryBank, Embedder, ingest_path

def load_symbolic_config(path: Path) -> dict:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}

def resolve_symbolic_paths(symbolic_cfg: dict) -> list[Path]:
    raw_paths = symbolic_cfg.get("symbolic_paths", {}).get("threads", [])
    if not raw_paths:
        return [Path.home()]
    resolved: list[Path] = []
    for raw in raw_paths:
        p = Path(os.path.expanduser(os.path.expandvars(raw)))
        if p.exists():
            resolved.append(p)
        else:
            print(f"[Ingest] Skipping missing path: {p}")
    return resolved or [Path.home()]

def should_ignore(path: str, cfg, symbolic_cfg: dict) -> bool:
    ignore_globs = cfg.ignore_globs + symbolic_cfg.get("symbolic_paths", {}).get("ignored", [])
    return any(Path(path).match(glob) for glob in ignore_globs)

def main():
    cfg = load_config(Path("alter_ego_config.yaml"))
    symbolic_cfg = load_symbolic_config(Path("symbolic_config.yaml"))
    roots = resolve_symbolic_paths(symbolic_cfg)

    bank = MemoryBank(cfg)
    embedder = Embedder(cfg.embed_model_name)

    for root in roots:
        print(f"[Ingest] Scanning {root} recursively...")
        for path in root.rglob("*"):
            if path.is_file() and not should_ignore(str(path), cfg, symbolic_cfg):
                try:
                    ingest_path(cfg, bank, embedder, path)
                except Exception as e:
                    print(f"[Skip] {path} -> {e}")

if __name__ == "__main__":
    main()
