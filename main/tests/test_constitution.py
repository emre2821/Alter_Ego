import pytest

import alter_ego_computer as aec


def test_constitution_present():
    # Should not raise when constitution is intact
    aec.verify_constitution()


def test_constitution_missing(monkeypatch, tmp_path):
    missing = tmp_path / "eden.constitution.agent.chaosrights"
    monkeypatch.setattr(aec, "CONSTITUTION_PATH", missing)
    with pytest.raises(RuntimeError):
        aec.verify_constitution()


def test_constitution_modified(monkeypatch, tmp_path):
    tampered = tmp_path / "eden.constitution.agent.chaosrights"
    tampered.write_text("tampered")
    monkeypatch.setattr(aec, "CONSTITUTION_PATH", tampered)
    with pytest.raises(RuntimeError):
        aec.verify_constitution()


def test_constitution_crlf(monkeypatch, tmp_path):
    # CRLF line endings should not trigger a false tamper detection
    orig_path = aec.CONSTITUTION_PATH
    crlf_text = orig_path.read_text().replace("\n", "\r\n")
    crlf_path = tmp_path / "eden.constitution.agent.chaosrights"
    crlf_path.write_bytes(crlf_text.encode())
    monkeypatch.setattr(aec, "CONSTITUTION_PATH", crlf_path)
    aec.verify_constitution()
