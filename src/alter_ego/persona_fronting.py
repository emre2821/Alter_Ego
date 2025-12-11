# persona_fronting.py
# Tracks and updates current active persona for Alter/Ego

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from configuration import get_switch_log_path

class PersonaFronting:
    def __init__(self):
        self.current = None
        self._switch_log: Optional[Path] = None

    @staticmethod
    def _resolve_switch_log_path(create: bool = False) -> Path:
        switch_log = get_switch_log_path(create=create)
        if create:
            switch_log.parent.mkdir(parents=True, exist_ok=True)
        return switch_log

    @property
    def switch_log(self) -> Path:
        if self._switch_log is None:
            self._switch_log = self._resolve_switch_log_path(create=True)
            print(f"Persona switch log: {self._switch_log}")
        return self._switch_log

    def refresh_switch_log(self) -> Path:
        self._switch_log = self._resolve_switch_log_path(create=True)
        print(f"Persona switch log refreshed: {self._switch_log}")
        return self._switch_log

    def front(self, persona, trigger_type="prompted", comment=""):
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        log_entry = [timestamp, persona, trigger_type, comment]
        with open(self.switch_log, 'a', encoding='utf-8') as f:
            f.write(f"- {json.dumps(log_entry)}\n")
        self.current = persona
        print(f"Now fronting as {persona} ({trigger_type})")

    def get_active(self):
        return self.current

if __name__ == "__main__":
    pf = PersonaFronting()
    pf.front("Rhea", "autonomous", "Felt symbolic sync with last prompt.")
