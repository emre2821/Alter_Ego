# persona_simulator.py
# Reads CHAOS/DCA/mirror files and simulates voice/persona tones for AI output

import json
from pathlib import Path

from configuration import get_persona_root
# Use local adapter which can delegate to Lyss if available
from chaos_parser_core import parse_chaos_file
if __package__:
    from .configuration import get_persona_root
else:
    from configuration import get_persona_root

class Persona:
    def __init__(self, name, tone, keywords, phrases, overrides):
        self.name = name
        self.tone = tone
        self.keywords = keywords
        self.phrases = phrases
        self.overrides = overrides

    def style_response(self, raw_text):
        styled = raw_text
        for key, val in self.overrides.items():
            styled = styled.replace(key, val)
        return styled + f"\n-- [{self.name}]"

class PersonaSimulator:
    def __init__(self, persona_dir: str | Path | None = None):
        if persona_dir is None:
            persona_dir = get_persona_root()
        self.persona_dir = Path(persona_dir)
        self.personas = self.load_all_personas()

    def load_all_personas(self):
        personas = {}
        # search recursively to support shared persona roots
        for file in self.persona_dir.rglob("*.chaos"):
            data = parse_chaos_file(file)
            name = data.get("name") or data.get("persona") or file.stem
            tone = data.get("tone", "neutral")
            keywords = data.get("keywords", [])
            phrases = data.get("phrases", [])
            overrides = data.get("overrides", {})
            personas[name] = Persona(name, tone, keywords, phrases, overrides)
        for file in self.persona_dir.rglob("*.json"):
            if 'mirror' in file.stem:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                name = data.get("name", file.stem)
                tone = data.get("tone", "neutral")
                keywords = data.get("keywords", [])
                phrases = data.get("phrases", [])
                overrides = data.get("overrides", {})
                personas[name] = Persona(name, tone, keywords, phrases, overrides)
        return personas

    def simulate(self, persona_name, llm_text):
        if persona_name not in self.personas:
            return f"[Error: Persona '{persona_name}' not found.]"
        persona = self.personas[persona_name]
        return persona.style_response(llm_text)

# === Example ===
if __name__ == "__main__":
    sim = PersonaSimulator()
    sample = "I think we should try something else."
    print(sim.simulate("Rhea", sample))
