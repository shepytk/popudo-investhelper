import os
import sys
from pathlib import Path

os.environ.setdefault("INVESTHELPER_DATABASE_URL", "sqlite:///./test.db")

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
