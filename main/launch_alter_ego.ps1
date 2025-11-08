# Bootstrap a local environment for Alter/Ego on Windows PowerShell.

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -U pip
pip install -r requirements.txt

# Create default folders + memory database (safe to re-run).
python alter_ego_computer.py init

# Optional: ingest a starter folder of notes or echoes.
# python alter_ego_computer.py ingest "C:\Path\To\Your\Memories"

# Launch the GUI. Runtime paths now resolve via configuration.py, so
# override them by editing alter_ego_config.yaml or exporting env vars
# like PERSONA_ROOT / GPT4ALL_MODEL_DIR only when you need to deviate
# from the defaults documented in the README.
python alter_ego_computer.py launch
