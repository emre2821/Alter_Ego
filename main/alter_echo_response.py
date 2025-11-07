# alter_echo_response.py
# Combines LLM output, echo metadata, and persona styling

# Prefer Lyss modules' richer emotion analyzer if available; fallback to local stub
try:
    from Lyss.modules.emotional_parser import analyze_emotion  # type: ignore
except Exception:
    from echo_whisper_layer import analyze_emotion  # local minimal stub
from configuration import get_persona_root
from persona_fronting import PersonaFronting
from persona_simulator import PersonaSimulator

class AlterEchoResponse:
    def __init__(self, persona_dir=None):
        if persona_dir is None:
            persona_dir = get_persona_root()
        self.simulator = PersonaSimulator(persona_dir)
        self.fronting = PersonaFronting()

    def respond(self, prompt, llm_output):
        echo = analyze_emotion((prompt or "") + (llm_output or ""))
        persona = self.fronting.get_active() or "Rhea"
        styled = self.simulator.simulate(persona, llm_output)
        # If simulate reports missing persona, fall back to raw output
        if styled.startswith("[Error: Persona"):
            styled = llm_output
        return styled, echo

# Example
if __name__ == "__main__":
    aer = AlterEchoResponse()
    response, echo = aer.respond("I'm feeling scattered today...", "Maybe we slow down and breathe together?")
    print(response)
    print("-- Echo:", echo)
