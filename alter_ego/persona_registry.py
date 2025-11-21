# persona_registry.py
# Keeps record of all known personas and metadata

import json
from pathlib import Path

REGISTRY_PATH = Path("./personas/persona_registry.json")

class PersonaRegistry:
    def __init__(self):
        self.registry = {}
        self.load()

    def load(self):
        if REGISTRY_PATH.exists():
            self.registry = json.loads(REGISTRY_PATH.read_text(encoding='utf-8'))
        else:
            self.registry = {}

    def save(self):
        REGISTRY_PATH.write_text(json.dumps(self.registry, indent=2), encoding='utf-8')

    def register(self, name, source_file, tone="neutral"):
        self.registry[name] = {
            "source": source_file,
            "tone": tone,
            "uses": 0
        }
        self.save()

    def increment_use(self, name):
        if name in self.registry:
            self.registry[name]["uses"] += 1
            self.save()

    def list_personas(self):
        return list(self.registry.keys())

    def get(self, name):
        return self.registry.get(name, None)

if __name__ == "__main__":
    pr = PersonaRegistry()
    pr.register("Naoto", "./personas/Naoto.chaos", "analytical")
    print(pr.list_personas())
