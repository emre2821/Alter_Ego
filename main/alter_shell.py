# alter_shell.py
# Central runtime for Alter/Ego — ties core functions together.
# Warm-starts GPT4All in a background thread so the GUI never blocks.

from __future__ import annotations
import inspect
import os
import logging
import threading

from pathlib import Path

from sqlite_memory import init_db, search, add as mem_add
from autosave_echo_daemon import autosave_prompt
from alter_echo_response import AlterEchoResponse
from persona_fronting import PersonaFronting
from chaos_rag_wrapper import generate_alter_ego_response, get_shared_model
from configuration import get_memory_db_path

log = logging.getLogger("alter_shell")


class AlterShell:
    def __init__(self):
        self.echo_response = AlterEchoResponse()
        self.fronting = PersonaFronting()

        # SQLite DB path for embeddings.
        default_db = get_memory_db_path()
        env_override = os.getenv("MEMORY_DB")
        self.db_path = str(Path(env_override).expanduser()) if env_override else str(default_db)
        init_db(self.db_path)

        # Shared LLM instance loaded in background
        self._model = None
        self._model_ready = threading.Event()
        threading.Thread(target=self._warm_start, daemon=True).start()
        self._supports_persona_kw = None

    def _warm_start(self):
        try:
            self._model = get_shared_model()  # caches internally
            self._model_ready.set()
            logging.info("LLM warm-start complete.")
        except Exception:
            logging.exception("Warm-start failed")

    def select_model(self, model_dir: str | None, model_name: str | None):
        """GUI calls this when user picks a model; we rebuild in the background."""
        from chaos_rag_wrapper import set_model_selection  # local import to avoid cycles
        set_model_selection(model_dir, model_name)
        self._model = None
        self._model_ready.clear()
        threading.Thread(target=self._warm_start, daemon=True).start()

    def interact(self, user_input: str) -> str:
        # 1) retrieve memories (never block or crash the GUI)
        try:
            mems = search(self.db_path, user_input, k=3)
        except Exception as e:
            logging.warning("memory search error: %s", e)
            mems = []

        # 2) if model still loading, give immediate feedback
        if not self._model_ready.is_set():
            return "Booting model… give me a few seconds."

        # 3) generate LLM output with our preloaded instance
        persona = self.fronting.get_active() or "Rhea"

        if self._supports_persona_kw is None:
            try:
                sig = inspect.signature(generate_alter_ego_response)
            except (TypeError, ValueError):
                # built-in or otherwise uninspectable object — optimistically assume persona is ok
                self._supports_persona_kw = True
            else:
                params = sig.parameters.values()
                has_kwargs = any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params)
                self._supports_persona_kw = has_kwargs or ("persona" in sig.parameters)

        call_kwargs = {
            "memory_used": mems,
            "model": self._model,
        }

        if self._supports_persona_kw:
            call_kwargs["persona"] = persona

        try:
            llm_output = generate_alter_ego_response(
                user_input,
                **call_kwargs,
            )
        except TypeError as exc:
            if "persona" in call_kwargs:
                logging.info("generate_alter_ego_response rejected persona kwarg; retrying without it")
                call_kwargs.pop("persona", None)
                self._supports_persona_kw = False
                try:
                    llm_output = generate_alter_ego_response(
                        user_input,
                        **call_kwargs,
                    )
                except TypeError:
                    # Restore caller visibility of the original failure — this wasn't about persona.
                    raise exc
            else:
                raise

        # 4) post-process echo
        response, echo = self.echo_response.respond(user_input, llm_output)

        # 5) autosave echo
        try:
            autosave_prompt(user_input, echo)
        except Exception as e:
            logging.warning("[autosave_warning] %s", e)

        # 6) optional memory write-through
        try:
            mem_add(self.db_path, f"user:{user_input}")
            mem_add(self.db_path, f"echo:{echo}")
        except Exception:
            pass

        return response


if __name__ == "__main__":
    shell = AlterShell()
    print("Alter/Ego shell — type 'exit' to quit.")
    while True:
        try:
            s = input("> ").strip()
            if s.lower() in {"exit", "quit"}:
                break
            print(shell.interact(s))
        except KeyboardInterrupt:
            break
