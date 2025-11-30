"""Runtime shell that orchestrates Alter/Ego interactions."""

from __future__ import annotations

import inspect
import logging
import os
import threading
from typing import Optional

from autosave_echo_daemon import autosave_prompt
from alter_echo_response import AlterEchoResponse
from chaos_rag_wrapper import (
    generate_alter_ego_response,
    get_dummy_engine,
    get_shared_model,
    set_model_selection,
)
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
        self._model_warning: Optional[str] = None

        threading.Thread(target=self._warm_start, daemon=True).start()

    # ------------------------------------------------------------------
    def _mark_backend_ready(self, model: object, message: str) -> None:
        self._model = model
        self._model_warning = None
        self._model_ready.set()
        log.info(message)

    # ------------------------------------------------------------------
    def _get_dummy_backend(self) -> object | None:
        try:
            return get_dummy_engine()
        except Exception:
            log.exception("Dummy engine warm-start check failed")
            return None

    # ------------------------------------------------------------------
    def _warm_start(self) -> None:
        dummy_mode = os.getenv("ALTER_EGO_DUMMY_ONLY", "auto").strip().lower()

        try:
            self._model = get_shared_model()
        except Exception:
            log.warning("Warm-start failed during model discovery/loading", exc_info=True)
            self._model_warning = "Model discovery failed; check logs for details."
            return
        else:
            if self._model is not None:
                self._model_ready.set()
                self._model_warning = None
                log.info("LLM warm-start complete.")
                return

        if dummy_mode in {"1", "true", "yes", "on"}:
            try:
                get_dummy_engine()
            except Exception:
                log.warning("Warm-start failed: dummy backend unavailable", exc_info=True)
                self._model_warning = "Dummy backend unavailable; check logs for details."
            else:
                # Intentionally avoid storing the dummy backend on self._model so the
                # downstream call path continues to route through GPT4All when it
                # eventually becomes available.
                self._model_ready.set()
                self._model_warning = None
                log.info("Dummy-only mode active; warm-start complete without GPT4All.")
            return

        log.warning("Warm-start deferred: no model ready; continuing to boot")
            model = get_shared_model()
        except Exception:
            log.exception("Warm-start failed")
            self._model_warning = "Model discovery failed; check logs for details."
            return

        self._model = model
        if self._model is not None:
            self._mark_backend_ready(self._model, "LLM warm-start complete.")
            return

        dummy_backend = self._get_dummy_backend()
        if dummy_backend is not None:
            self._mark_backend_ready(dummy_backend, "Dummy engine available; skipping GPT4All warm-start")
            return

        self._model_warning = "No model available yet; still booting backend."
        log.warning("Warm-start deferred: no model ready; continuing to boot")

    # ------------------------------------------------------------------
    def select_model(self, model_dir: str | None, model_name: str | None) -> None:
        """Called by the GUI when the user picks a model."""

        set_model_selection(model_dir, model_name)
        self._model = None
        self._model_ready.clear()
        self._model_warning = None
        threading.Thread(target=self._warm_start, daemon=True).start()

    # ------------------------------------------------------------------
    def interact(self, user_input: str) -> str:
        try:
            mems = search(self.db_path, user_input, k=3)
        except Exception as exc:
            log.warning("memory search error: %s", exc)
            mems = []

        if not self._model_ready.is_set():
            if self._model_warning:
                return f"Booting model… {self._model_warning}"
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
