# alter_echo_response.py
# Combines LLM output, echo metadata, and persona styling

# Prefer Lyss modules' richer emotion analyzer if available; fallback to local stub
try:
    from Lyss.modules.emotional_parser import analyze_emotion  # type: ignore
except Exception:
    from echo_whisper_layer import analyze_emotion  # local minimal stub
from persona_simulator import PersonaSimulator
from persona_fronting import PersonaFronting

class AlterEchoResponse:
    def __init__(self, persona_dir=None):
        # Default to Lyss/all_daemons persona tree if present, else local ./personas
        from pathlib import Path
        import os
        if persona_dir is None:
            env_root = os.getenv('PERSONA_ROOT')
            if env_root:
                candidate = Path(env_root)
            else:
                candidate = Path(r"C:\EdenOS_Origin\all_daemons")
            persona_dir = candidate if candidate.exists() else Path("./personas")
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
