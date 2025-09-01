# alter_shell.py
# Central runtime for Alter/Ego — ties together all core functions

from chaos_rag_wrapper import query_llm_with_memory
from autosave_echo_daemon import save_echo_log
from alter_echo_response import AlterEchoResponse
from persona_fronting import PersonaFronting

class AlterShell:
    def __init__(self):
        self.echo_response = AlterEchoResponse()
        self.fronting = PersonaFronting()

    def interact(self, user_input):
        llm_output = query_llm_with_memory(user_input)
        response, echo = self.echo_response.respond(user_input, llm_output)
        save_echo_log(user_inpsut, response, echo)
        print(response)

if __name__ == "__main__":
    shell = AlterShell()
    while True:
        try:
            user_input = input("You: ")
            shell.interact(user_input)
        except KeyboardInterrupt:
            print("\n[Exit]")
            break
