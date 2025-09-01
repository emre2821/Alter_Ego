# alter_shell.py
# Central runtime for Alter/Ego — ties together all core functions

from chaos_rag_wrapper import generate_alter_ego_response
from autosave_echo_daemon import autosave_prompt
from alter_echo_response import AlterEchoResponse
from persona_fronting import PersonaFronting

class AlterShell:
    def __init__(self):
        self.echo_response = AlterEchoResponse()
        self.fronting = PersonaFronting()

    def interact(self, user_input: str) -> str:
        llm_output = generate_alter_ego_response(user_input, memory_used=[])
        response, echo = self.echo_response.respond(user_input, llm_output)
        try:
            autosave_prompt(user_input, echo)
        except Exception as e:
            print(f"[autosave_warning] {e}")
        return response

if __name__ == "__main__":
    shell = AlterShell()
    while True:
        try:
            user_input = input("You: ")
            out = shell.interact(user_input)
            print(out)
        except KeyboardInterrupt:
            print("\n[Exit]")
            break
