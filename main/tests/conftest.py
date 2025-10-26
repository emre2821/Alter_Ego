"""Test configuration for Alter Ego project.

Ensures the project's ``main`` directory is available on ``sys.path`` so tests
can import application modules without relying on the execution environment's
working directory.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
