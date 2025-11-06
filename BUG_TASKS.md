# Bug Fix Task List

1. **Let `AlterShell` tolerate persona-agnostic generators.**
   - Location: `main/alter_shell.py`
   - Summary: `AlterShell.interact` unconditionally forwards a `persona=` keyword argument, causing tests that inject simplified stubs for `generate_alter_ego_response` to crash with `TypeError`. Detect signature support (or retry without the keyword) so persona-agnostic callables still work.
   - Validation: Extend `main/tests/test_alter_shell.py` to confirm interaction succeeds when the stub lacks the `persona` parameter.

2. **Respect fallback text when GPT4All is unavailable.**
   - Location: `main/chaos_rag_wrapper.py`
   - Summary: In auto mode, the dummy-engine fallback still overrides the explicit "Hmm…" guardrail if no GPT4All backend or model is reachable. Bypass the dummy path when the real model is missing so the textual fallback propagates.
   - Validation: Cover this branch in `main/tests/test_chaos_rag_wrapper.py` to ensure the "Hmm…" message appears when GPT4All cannot be loaded.

3. **Make `alter_ego_computer` resilient to missing Typer.**
   - Location: `main/alter_ego_computer.py`
   - Summary: Importing the module raises `ModuleNotFoundError` when Typer isn't installed, even for callers that only need non-CLI utilities. Guard the import (as done for `watchdog`) so the module remains usable without Typer.
   - Validation: Add tests that import the module with Typer patched out, ensuring a graceful fallback path.

4. **Allow `ingest_entire_system` to load without PyYAML.**
   - Location: `main/ingest_entire_system.py`
   - Summary: A top-level `import yaml` prevents the module from loading when PyYAML is absent, despite most helpers not requiring YAML. Defer or guard the import so path utilities stay available without the dependency.
   - Validation: Cover the adjusted behavior with tests that simulate PyYAML's absence.

5. **Stop `autosave_prompt` from writing after mkdir failure.**
   - Location: `main/autosave_echo_daemon.py`
   - Summary: When directory creation fails, the function logs a warning but still attempts to open the same path, leading to a second exception. Short-circuit the write path once directory setup has failed.
   - Validation: Add unit tests ensuring the function returns cleanly when the autosave directory cannot be created.
