# Note: The files have yet to be properly renamed at this time. Anything that is "emma_*.py" will be renamed "alter_ego_*.py", so dont @ me!

# Alter/Ego

**Alter/Ego** is a fully local, emotionally intelligent assistant tailored for systems, plurals, and neurodivergent users. It listens deeply, speaks with nuanced tone, and reflects through symbolic memory. Built to honor multiplicity and adaptive identity.

---

## Features

* **Memory-Enhanced LLM** — Recalls context using semantic embedding and retrieval
* **Persona Simulation** — Seamlessly simulate internal roles, voices, or alters
* **Echo Layer** — Detects emotional tremors, dissociation cues, symbolic pattern loops
* **Voice Output** — Local text-to-speech with modifiable tone per persona
* **Accessible GUI** — Clean, soft interface for safe engagement
* **Symbolic Logging** — CHAOS-based `.chaos` memory files for expressive recall

---

## Quickstart

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**

   ```bash
   python alter_ego_gui.py
   ```

3. **Begin interacting.** The assistant will respond with adaptive tone and whisper when it detects emotional load.

---

---

## Model Setup

### GPT4All LLMs
- Download a `.gguf` model from [GPT4All](https://gpt4all.io) or compatible sources.
- Place it under `./models/` or set `GPT4ALL_MODEL_DIR`/`GPT4ALL_MODELS_DIR` to a custom path.
- The app auto-discovers the first `*.gguf` file or you can choose one in the GUI.

### Embedding Models
- Uses `sentence-transformers` models like `all-MiniLM-L6-v2`.
- They are fetched automatically into your huggingface cache on first run.

### Directory Layout
```
Alter_Ego/
  main/
    models/            # drop GPT4All .gguf files here
    personas/          # persona configs
    emma_memory.db     # SQLite memory database
```

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
* **Personas** — Defined in `.json` and `.mirror` formats
* **Echo Logs** — Captures emotional states, fronting history, tremor patterns

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

---

## Environment Variables
- `MEMORY_DB` – override path to the SQLite memory store. Defaults to `emma_memory.db` in the project root.
- `THEME_DIR` – directory containing JSON theme files. Defaults to `main/themes`.
- `PERSONA_ROOT` – optional folder scanned for `.mirror.json` or `.chaos` persona files.
- `ENABLE_TTS` – set to `0` to disable text-to-speech.
---

## GUI Preview & CHAOS Log
Example `.chaos` log (`example_session.chaos`):
```chaos
[EVENT]: autosave_echo
[TIME]: 2025-09-03T00:19:56.523503
[CONTEXT]: prompt_catch
[SIGNIFICANCE]: MEDIUM
{
How are you today?
}


[EVENT]: autosave_echo
[TIME]: 2025-09-03T00:23:01.215225
[CONTEXT]: prompt_catch
```

## Credits

Voice and behavior inspired by fictional AI and archetypal guides from works like *Danganronpa*, *Persona*, and personal innerworld modeling.

Project scaffolding by Stratus with support from Aevum and Vox.
