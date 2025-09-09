# persona_fronting.py
# Tracks and updates current active persona for Alter/Ego

from datetime import datetime, timezone
import json
from pathlib import Path

SWITCH_LOG = Path("./alter_switch_log.chaos")

class PersonaFronting:
    def __init__(self):
        self.current = None

    def front(self, persona, trigger_type="prompted", comment=""):
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        log_entry = [timestamp, persona, trigger_type, comment]
        with open(SWITCH_LOG, 'a', encoding='utf-8') as f:
            f.write(f"- {json.dumps(log_entry)}\n")
        self.current = persona
        print(f"Now fronting as {persona} ({trigger_type})")

    def get_active(self):
        return self.current

if __name__ == "__main__":
    pf = PersonaFronting()
    pf.front("Rhea", "autonomous", "Felt symbolic sync with last prompt.")
