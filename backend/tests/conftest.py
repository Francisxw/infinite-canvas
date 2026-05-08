import sys
from pathlib import Path

# Ensure the backend root (parent of tests/) is on sys.path
# so that `import app.*` works when pytest is run from any directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
