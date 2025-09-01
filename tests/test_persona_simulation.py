# tests/test_persona_simulation.py
import pytest
from persona_simulator import PersonaSimulator

@pytest.fixture
def simulator():
    return PersonaSimulator("./personas")

def test_simulation_rhea(simulator):
    sample = "This is a trial prompt."
    styled = simulator.simulate("Rhea", sample)
    assert "Rhea" in styled
    assert sample in styled
	