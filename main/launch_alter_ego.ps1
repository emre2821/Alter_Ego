# STEP 1: Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# STEP 2: Upgrade pip and install only needed dependencies for GPT4All
pip install -U pip

pip install chromadb sentence-transformers rich typer watchdog pydantic pyyaml markdown2 requests numpy scikit-learn nltk pyttsx3 gpt4all

# STEP 3: First-run init (creates DB and data folders if needed)
python alter_ego_computer.py init --data .\my_files --db .\emma_memory.db

# STEP 4: Ingest core system paths (you can add more later)
python alter_ego_computer.py ingest "C:\EdenOS_Origin\dreambearer_notes\private_notes\Emmas_Computer_AI"

# STEP 5: Ask a memory-based question using GPT4All model
python alter_ego_computer.py ask "what lives in what_the_fuck_even_is_life.chaos?" --backend gpt4all --model_name "DeepSeek-R1-Distill-Qwen-1.5B-Q4_0.gguf"

# STEP 6: Optional cleanup scan
python alter_ego_computer.py scan-dupes

# STEP 7: Set persona root and launch the GUI
$env:PERSONA_ROOT = "C:\EdenOS_Origin\all_daemons"
# Point to local GPT4All models directory (adjust if needed)
$env:GPT4ALL_MODELS_DIR = "C:\Users\emmar\AppData\Local\nomic.ai\GPT4All"
# Optional: set a specific model filename found in that directory, e.g.:
# $env:GPT4ALL_MODEL = "DeepSeek-R1-Distill-Qwen-1.5B-Q4_0.gguf"
# Optional: disable TTS by setting to 0
# $env:ENABLE_TTS = '1'
python alter_ego_gui.py
