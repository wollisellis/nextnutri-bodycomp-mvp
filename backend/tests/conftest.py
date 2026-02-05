from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root is importable when running pytest from anywhere.
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
