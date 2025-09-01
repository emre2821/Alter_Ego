# alter_echo_response.py
# Combines LLM output, echo metadata, and persona styling

from echo_whisper_layer import analyze_emotion
from persona_simulator import PersonaSimulator
from persona_fronting import PersonaFronting

class AlterEchoResponse:
    def __init__(self, persona_dir="./personas"):
        self.simulator = PersonaSimulator(persona_dir)
        self.fronting = PersonaFronting()

    def respond(self, prompt, llm_output):
        echo = analyze_emotion(prompt + llm_output)
        persona = self.fronting.get_active() or "default"
        styled = self.simulator.simulate(persona, llm_output)
        return styled, echo

# Example
if __name__ == "__main__":
    aer = AlterEchoResponse()
    response, echo = aer.respond("I'm feeling scattered today...", "Maybe we slow down and breathe together?")
    print(response)
    print("-- Echo:", echo)
