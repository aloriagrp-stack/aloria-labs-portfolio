"""
Aloria Hunter - Outreach Data Exporter (CLI / Module Alias)
Direct alias to exporter.py for backward compatibility and intuitive naming.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from exporter import (
    clean_email,
    generate_outreach_exports,
    main
)

if __name__ == "__main__":
    main()
