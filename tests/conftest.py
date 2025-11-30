import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
ALTER_EGO_DIR = SRC_DIR / "alter_ego"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

if str(ALTER_EGO_DIR) not in sys.path:
    sys.path.insert(0, str(ALTER_EGO_DIR))
