import sys
from pathlib import Path

# make `import core` work under plain `pytest` (repo root on sys.path)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
