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

## Contributing

See the [CONTRIBUTING](../CONTRIBUTING.md) guide for setup, coding style, and tests.

Bug reports and feature requests can be opened via the issue templates:
- [Bug report](../.github/ISSUE_TEMPLATE/bug_report.md)
- [Feature request](../.github/ISSUE_TEMPLATE/feature_request.md)

---

## Credits

Voice and behavior inspired by fictional AI and archetypal guides from works like *Danganronpa*, *Persona*, and personal innerworld modeling.

Project scaffolding by Stratus with support from Aevum and Vox.
