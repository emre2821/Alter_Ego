# persona_builder.py
# Wizard to generate new persona config files

import json
from pathlib import Path
from datetime import datetime, timezone

SAVE_DIR = Path("./personas")
SAVE_DIR.mkdir(exist_ok=True)

def build_persona():
    print("👤 Persona Builder — Let her speak for herself.")
    name = input("Name: ").strip()
    tone = input("Tone (e.g., gentle, fierce, soft-logic): ").strip()
    keywords = input("Comma-separated keywords (optional): ").split(',')
    phrases = input("Signature phrases (comma-separated): ").split(',')
    overrides = {}
    print("Enter word replacements (e.g., try=attempt). Leave blank to finish.")
    while True:
        pair = input("Override: ").strip()
        if not pair:
            break
        if '=' in pair:
            key, val = pair.split('=', 1)
            overrides[key.strip()] = val.strip()

    data = {
        "name": name,
        "tone": tone,
        "keywords": [k.strip() for k in keywords if k.strip()],
        "phrases": [p.strip() for p in phrases if p.strip()],
        "overrides": overrides,
        "created_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    }

    file_path = SAVE_DIR / f"{name}.chaos"
    file_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
    print(f"✨ Persona '{name}' saved to {file_path}")

if __name__ == "__main__":
    build_persona()
