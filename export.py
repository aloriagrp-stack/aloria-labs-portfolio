"""
Aloria Hunter - Outreach Data Exporter (Root Workspace Runner)
Allows running `python export.py` from repository root.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
HUNTER_DIR = ROOT_DIR / "aloria-hunter"
if str(HUNTER_DIR) not in sys.path:
    sys.path.insert(0, str(HUNTER_DIR))

from exporter import (
    clean_email,
    generate_outreach_exports,
    main
)

if __name__ == "__main__":
    main()
