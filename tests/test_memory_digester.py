# tests/test_memory_digester.py
from memory_digester import MemoryDigester
from persona_simulator import PersonaSimulator
import os


def test_memory_digest_log(tmp_path):
    mem_dir = tmp_path / "mem"
    mem_dir.mkdir()
    test_file = mem_dir / "note.chaos"
    test_file.write_text("I remember the ocean.")

    sim = PersonaSimulator("./personas")
    digester = MemoryDigester(mem_dir, sim, pace=0)
    digester.walk_folder("Rhea")

    assert len(digester.digest_log) == 1
