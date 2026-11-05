import sys
from pathlib import Path

# Automatically ensure both project root and src/ are in sys.path for pytest and VS Code
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"

for path in [str(ROOT_DIR), str(SRC_DIR)]:
    if path not in sys.path:
        sys.path.insert(0, path)

