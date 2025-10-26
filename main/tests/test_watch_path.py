from pathlib import Path

import alter_ego_computer as ae


def test_watch_path_graceful_without_watchdog(monkeypatch, capsys):
    monkeypatch.setattr(ae, "WATCHDOG_OK", False)
    cfg = ae.Config()
    ae.watch_path(cfg, bank=None, embedder=None, path=Path('.'))
    captured = capsys.readouterr()
    assert "watchdog is not installed" in captured.out
