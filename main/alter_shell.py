"""Runtime shell that orchestrates Alter/Ego interactions."""

from __future__ import annotations

import inspect
import logging
import threading

from autosave_echo_daemon import autosave_prompt
from alter_echo_response import AlterEchoResponse
from chaos_rag_wrapper import generate_alter_ego_response, get_shared_model, set_model_selection
from configuration import get_memory_db_path
from persona_fronting import PersonaFronting
from sqlite_memory import add as mem_add, init_db, search

log = logging.getLogger("alter_shell")


class AlterShell:
    """High-level runtime coordinator used by both GUI and CLI."""

    def __init__(self) -> None:
        self.echo_response = AlterEchoResponse()
        self.fronting = PersonaFronting()
        self.db_path = str(get_memory_db_path())
        init_db(self.db_path)

        self._model = None
        self._model_ready = threading.Event()
        self._supports_persona_kw: bool | None = None

        threading.Thread(target=self._warm_start, daemon=True).start()

    # ------------------------------------------------------------------
    def _warm_start(self) -> None:
        try:
            self._model = get_shared_model()
            self._model_ready.set()
            log.info("LLM warm-start complete.")
        except Exception:
            log.exception("Warm-start failed")

    # ------------------------------------------------------------------
    def select_model(self, model_dir: str | None, model_name: str | None) -> None:
        """Called by the GUI when the user picks a model."""

        set_model_selection(model_dir, model_name)
        self._model = None
        self._model_ready.clear()
        threading.Thread(target=self._warm_start, daemon=True).start()

    # ------------------------------------------------------------------
    def interact(self, user_input: str) -> str:
        try:
            mems = search(self.db_path, user_input, k=3)
        except Exception as exc:
            log.warning("memory search error: %s", exc)
            mems = []

        if not self._model_ready.is_set():
            return "Booting model… give me a few seconds."

        persona = self.fronting.get_active() or "Rhea"

        if self._supports_persona_kw is None:
            try:
                sig = inspect.signature(generate_alter_ego_response)
            except (TypeError, ValueError):
                self._supports_persona_kw = True
            else:
                params = sig.parameters.values()
                has_kwargs = any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params)
                self._supports_persona_kw = has_kwargs or ("persona" in sig.parameters)

        call_kwargs = {"memory_used": mems, "model": self._model}
        if self._supports_persona_kw:
            call_kwargs["persona"] = persona

        try:
            llm_output = generate_alter_ego_response(user_input, **call_kwargs)
        except TypeError as exc:
            if "persona" in call_kwargs:
                log.info("generate_alter_ego_response rejected persona kwarg; retrying without it")
                call_kwargs.pop("persona", None)
                self._supports_persona_kw = False
                llm_output = generate_alter_ego_response(user_input, **call_kwargs)
            else:
                raise exc

        response, echo = self.echo_response.respond(user_input, llm_output)

        try:
            autosave_prompt(user_input, echo)
        except Exception as exc:
            log.warning("[autosave_warning] %s", exc)

        try:
            mem_add(self.db_path, f"user:{user_input}")
            mem_add(self.db_path, f"echo:{echo}")
        except Exception:
            pass

        return response


if __name__ == "__main__":  # pragma: no cover - manual smoke test helper
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
