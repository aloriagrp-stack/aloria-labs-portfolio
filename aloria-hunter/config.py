import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PARENT_DIR = BASE_DIR.parent

# Playwright browser path on D drive
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "D:\\playwright-browsers"

# Targeting Configuration
DEFAULT_COUNTRY = "Algeria"
DEFAULT_NICHES = [
    "Restaurants",
    "Hotels",
    "Cafes",
    "Dental Clinics",
    "Real Estate Agencies"
]
DEFAULT_CITIES = [
    "Algiers",
    "Oran",
    "Constantine",
    "Annaba"
]

# Browser Display: False = Visible window on screen (you can watch it type/click), True = Silent background
HEADLESS = False

# Rate Limiting & Safety
MAX_LEADS_PER_RUN = 30
EMAIL_DELAY_MINUTES = 8  # Wait 8 minutes between emails to maintain 100% deliverability
MAX_EMAILS_PER_DAY = 40
FOLLOW_UP_INTERVAL_DAYS = 2  # Follow up after 2 days of no response
MAX_FOLLOW_UPS = 2  # Total follow-ups (Initial + Follow-up 1 + Follow-up 2)

# Load SMTP Credentials from parent directory smtp_config.json
SMTP_CONFIG_PATH = PARENT_DIR / "smtp_config.json"

def get_smtp_config():
    if SMTP_CONFIG_PATH.exists():
        try:
            with open(SMTP_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "email": "alorialabs@gmail.com",
        "password": "",
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587
    }
