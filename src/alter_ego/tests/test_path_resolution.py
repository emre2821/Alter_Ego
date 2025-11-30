from ingest_entire_system import resolve_symbolic_paths


def test_resolve_symbolic_paths_skips_missing(tmp_path):
    existing = tmp_path / "exists"
    missing = tmp_path / "missing"
    existing.mkdir()
    cfg = {"symbolic_paths": {"threads": [str(existing), str(missing)]}}
    paths = resolve_symbolic_paths(cfg)
    assert existing in paths
    assert missing not in paths
