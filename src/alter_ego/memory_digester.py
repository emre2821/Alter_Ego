# memory_digester.py
# Ritual scanner for chunked emotional parsing of memory folders

import os
import time
from pathlib import Path
from persona_simulator import PersonaSimulator
from datetime import datetime, timezone

class MemoryDigester:
    def __init__(self, root_path, persona_sim: PersonaSimulator, pace=1.5):
        self.root_path = Path(root_path)
        self.sim = persona_sim
        self.pace = pace
        self.digest_log = []

    def digest_file(self, file_path, persona_name):
        try:
            if file_path.suffix in ['.txt', '.md', '.chaos', '.json']:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                styled = self.sim.simulate(persona_name, f"Reading file: {file_path.name}\n{content[:500]}...")
                timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                entry = {
                    'timestamp': timestamp,
                    'persona': persona_name,
                    'file': str(file_path),
                    'echo': styled
                }
                self.digest_log.append(entry)
                print(styled)
                time.sleep(self.pace)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    def walk_folder(self, persona_name):
        for root, dirs, files in os.walk(self.root_path):
            for name in files:
                file_path = Path(root) / name
                self.digest_file(file_path, persona_name)

    def save_log(self, out_path="memory_digest.chaos"):
        with open(out_path, 'w', encoding='utf-8') as f:
            for entry in self.digest_log:
                f.write(f"[{entry['timestamp']}] <{entry['persona']}> read {entry['file']}\n-- {entry['echo']}\n\n")

# Example usage (remove or wrap for GUI integration)
if __name__ == "__main__":
    sim = PersonaSimulator("./personas")
    digester = MemoryDigester("./memorybank", sim, pace=1.0)
    digester.walk_folder("Naoto")
    digester.save_log()
