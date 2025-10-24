# Alter/Ego

**Alter/Ego** is a fully local, emotionally intelligent assistant tailored for systems, plurals, and neurodivergent users. It listens deeply, speaks with nuanced tone, and reflects through symbolic memory. Built to honor multiplicity and adaptive identity.

---

## Features

* **Memory-Enhanced LLM** — Recalls context using semantic embedding and retrieval
* **Dummy Dialogue Engine** — Persona-aware scripts keep Alter/Ego speaking even without heavyweight models
* **Persona Simulation** — Seamlessly simulate internal roles, voices, or alters
* **Echo Layer** — Detects emotional tremors, dissociation cues, symbolic pattern loops
* **Voice Output** — Local text-to-speech with modifiable tone per persona
* **Accessible GUI** — Clean, soft interface for safe engagement
* **Symbolic Logging** — CHAOS-based `.chaos` memory files for expressive recall

---

## Quickstart

1. **Install dependencies** — Using `requirements.txt` is the recommended approach for a reproducible local setup:

   ```bash
   pip install -r requirements.txt
   ```

   If you prefer the lighter [FastEmbed](https://github.com/qdrant/fastembed) runtime for embeddings, install it alongside or instead of `sentence-transformers`:

   ```bash
   pip install fastembed
   python alter_ego_computer.py config --set-embed-model fastembed:BAAI/bge-small-en-v1.5
   ```

   When you exclusively rely on FastEmbed models you can safely remove `sentence-transformers` from `requirements.txt` (or your environment) to slim the install.

   If you prefer to use the project metadata directly, you can install via `pyproject.toml`:

   ```bash
   pip install .
   ```

2. **Run the application:**

   ```bash
   python alter_ego_gui.py
   ```

   or, from the CLI steward, launch with helpful environment toggles:

   ```bash
   python alter_ego_computer.py launch --persona-root ./personas --dummy-only
   ```

3. **Begin interacting.** The assistant will respond with adaptive tone and whisper when it detects emotional load.
3. **Begin interacting.** The assistant will respond with adaptive tone and whisper when it detects emotional load.

### Lightweight embeddings (no PyTorch)

Alter/Ego now accepts ONNX-based embeddings through [`fastembed`](https://github.com/qdrant/fastembed) for systems that cannot host PyTorch. Install the optional dependency and point the config at a supported model:

```bash
pip install fastembed
```

Then either edit `alter_ego_config.yaml` or export `ALTER_EGO_EMBED_MODEL` before launch so it reads, for example, `fastembed:BAAI/bge-small-en-v1.5`. When you use the `fastembed:` prefix, PyTorch and `sentence-transformers` are no longer required; you may safely remove them from `requirements.txt` or your environment to keep the install tiny.

### Dummy Dialogue Engine

Alter/Ego now wakes with a deterministic "dummy" companion so sessions can begin without downloading any GPT models.

* Scripts live in `datasets/alterego/dummy_playbooks.yaml`. Tweak or extend them to teach new rituals or tones.
* Set `ALTER_EGO_DUMMY_SCRIPT=/path/to/custom.yaml` to load an alternate script bundle.
* To force GPT4All instead, export `ALTER_EGO_DUMMY_ONLY=off` before launching.
* If you want only the dummy engine (never touching GPT files), use `ALTER_EGO_DUMMY_ONLY=on`.

### GUI Screenshot

This repository does not include a static `gui_screenshot.png`.

To generate a screenshot at runtime:

1. Launch the GUI with `python alter_ego_gui.py`.
2. Use your operating system's screenshot tool (or any capture utility) to save the window.

An example screenshot is hosted externally at [this image](https://via.placeholder.com/800x600.png?text=Alter/Ego+GUI). If the link ever fades, simply capture your own.

### Themes

The GUI looks for JSON theme files in `themes/` relative to `alter_ego_gui.py` (or a custom path via the `THEME_DIR` environment variable).
If no external themes are found, Alter/Ego falls back to its built-in styles such as `eden`, `dark`, and `light`.
You can override the palette for a single session by setting `ALTER_EGO_THEME` or passing `--theme` to `python alter_ego_computer.py launch`.

---

## File Structure

* `alter_ego_gui.py` — GUI interface
* `alter_shell.py` — Main runtime logic
* `alter_echo_response.py` — Formats LLM + echo output
* `autosave_echo_daemon.py` — Logs prompts, responses, and emotional metadata
* `chaos_rag_wrapper.py` — Retrieves memory and injects prompt structure
* `persona_fronting.py` — Tracks and retrieves current fronted persona
* `persona_registry.py` — Maintains list and metadata of all known personas
* `persona_builder.py` — CLI wizard to create new identities
* `/personas/` — Directory for persona config files and echo style preferences

---

## Storage & Persistence

* **Memory Files** — Saved as `.chaos` logs using symbolic syntax
* **Memory DB** — Embedding store in `alter_ego_memory.db`; override path with `MEMORY_DB`
* **Personas** — Defined in `.json` and `.mirror` formats
* **Echo Logs** — Captures emotional states, fronting history, tremor patterns

## Configuring symbolic paths

Edit `symbolic_config.yaml` to point symbolic path sets like `threads`, `tender`, or `sacred` to your own folders.
Paths may use `~` or environment variables such as `${PROJECTS}` so the file can move between systems.
During ingestion or watchdog runs, any listed directories that do not exist are skipped automatically.

---

## Example Interaction

Prompt:

> "I’m tired but need to keep going. Who’s still with me?"

System:

* Detects emotional load
* Responds with protector tone
* Logs fatigue pattern as whisper
* Stores memory in `.chaos` with emotional metadata

---

## Local-Only Execution

No internet or remote calls. Runs entirely on your machine for privacy, safety, and ownership of memory.

---

## Contributing

See the [CONTRIBUTING](../CONTRIBUTING.md) guide for setup, coding style, and tests.

Bug reports and feature requests can be opened via the issue templates:
- [Bug report](../.github/ISSUE_TEMPLATE/bug_report.md)
- [Feature request](../.github/ISSUE_TEMPLATE/feature_request.md)

---

## Credits

Voice and behavior inspired by fictional AI and archetypal guides from works like *Danganronpa*, *Persona*, and personal innerworld modeling.

### Example CHAOS Session

An abbreviated session log lives in `example_session.chaos`. The full contents are mirrored below:

```
[EVENT]: session_start
[TIME]: 2024-01-01T12:00:00Z
[CONTEXT]: system_init
[SIGNIFICANCE]: LOW
{
Session begins.
}

[EVENT]: user_prompt
[TIME]: 2024-01-01T12:01:00Z
[CONTEXT]: prompt_catch
[SIGNIFICANCE]: MEDIUM
{
Hello, Alter/Ego.
}

[EVENT]: session_end
[TIME]: 2024-01-01T12:05:00Z
[CONTEXT]: system_shutdown
[SIGNIFICANCE]: LOW
{
Closing session.
}

```

Project scaffolding by Stratus with support from Aevum and Vox.
