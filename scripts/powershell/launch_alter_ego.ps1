# Bootstrap a local environment for Alter/Ego on Windows PowerShell.

# Change to repository root (two levels up from scripts/powershell/)
$RepoRoot = Join-Path $PSScriptRoot "..\..\"
Set-Location -LiteralPath $RepoRoot

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -U pip
pip install -r requirements.txt

# Create default folders + memory database (safe to re-run).
python src/alter_ego/alter_ego_computer.py init

# Optional: ingest a starter folder of notes or echoes.
# python src/alter_ego/alter_ego_computer.py ingest "C:\Path\To\Your\Memories"

# Launch the GUI via the CLI entrypoint. Runtime paths resolve through
# configuration.py, so prefer editing alter_ego_config.yaml. Environment
# variables such as PERSONA_ROOT or GPT4ALL_MODEL_DIR remain available
# for one-off overrides when you need to diverge from the documented
# defaults.
python src/alter_ego/alter_ego_computer.py launch
