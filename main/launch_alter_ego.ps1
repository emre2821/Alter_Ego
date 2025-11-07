# STEP 1: Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# STEP 2: Upgrade pip and install only needed dependencies for GPT4All
pip install -U pip

pip install chromadb sentence-transformers rich typer watchdog pydantic pyyaml markdown2 requests numpy scikit-learn nltk pyttsx3 gpt4all

# STEP 3: First-run init (creates DB and data folders if needed)
python alter_ego_computer.py init

# STEP 4: Ingest core system paths (you can add more later)
  python alter_ego_computer.py ingest "C:\EdenOS_Origin\dreambearer_notes\private_notes\Alter_Ego_AI"

# STEP 5: Ask a memory-based question using GPT4All model
python alter_ego_computer.py ask "what lives in what_the_fuck_even_is_life.chaos?" --backend gpt4all --model_name "DeepSeek-R1-Distill-Qwen-1.5B-Q4_0.gguf"

# STEP 6: Optional cleanup scan
python alter_ego_computer.py scan-dupes

# STEP 7: Launch the GUI (set overrides only if you keep assets elsewhere)
# Example overrides:
# $env:PERSONA_ROOT = "D:\Shared\Personas"
# $env:GPT4ALL_MODEL_DIR = "D:\Models\GPT4All"
# $env:MEMORY_DB = "D:\AlterEgo\memory.db"
# STEP 7: Launch the GUI (defaults to .\main\personas and .\main\models)
# Uncomment these lines if you want to point at custom folders:
# $env:PERSONA_ROOT = "C:\path\to\your\personas"
# $env:GPT4ALL_MODEL_DIR = "D:\models\gpt4all"
# $env:GPT4ALL_MODEL = "DeepSeek-R1-Distill-Qwen-1.5B-Q4_0.gguf"
# $env:ENABLE_TTS = '0'
python alter_ego_computer.py launch
