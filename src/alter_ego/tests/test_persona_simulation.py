# tests/test_persona_simulation.py
import pytest
from configuration import get_persona_root
from persona_simulator import PersonaSimulator

@pytest.fixture
def simulator():
    return PersonaSimulator(get_persona_root())

def test_simulation_rhea(simulator):
    sample = "This is a trial prompt."
    styled = simulator.simulate("Rhea", sample)
    assert "Rhea" in styled
    assert sample in styled
	
