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
# Load SMTP Credentials from parent directory smtp_config.json
SMTP_CONFIG_PATH = PARENT_DIR / "smtp_config.json"

def get_raw_smtp_data():
    if SMTP_CONFIG_PATH.exists():
        try:
            with open(SMTP_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def list_smtp_profiles():
    data = get_raw_smtp_data()
    if "profiles" in data:
        return data["profiles"], data.get("active_profile", "gmail")
    # Fallback to single account
    return {
        "default": {
            "name": "Default Account",
            "email": data.get("email", "alorialabs@gmail.com"),
            "password": data.get("password", ""),
            "smtp_server": data.get("smtp_server", "smtp.gmail.com"),
            "smtp_port": data.get("smtp_port", 587),
            "sender_name": "Shriyansh Aloria — Aloria Labs",
            "reply_to": "info@alorialabs.in"
        }
    }, "default"

def get_smtp_config(profile_name=None):
    data = get_raw_smtp_data()
    if "profiles" in data:
        target = profile_name or data.get("active_profile", "gmail")
        if target in data["profiles"]:
            return data["profiles"][target]
        # Return first profile if requested not found
        first_key = list(data["profiles"].keys())[0]
        return data["profiles"][first_key]
    
    # Flat format fallback
    return {
        "email": data.get("email", "alorialabs@gmail.com"),
        "password": data.get("password", ""),
        "smtp_server": data.get("smtp_server", "smtp.gmail.com"),
        "smtp_port": data.get("smtp_port", 587),
        "sender_name": "Shriyansh Aloria — Aloria Labs",
        "reply_to": "info@alorialabs.in"
    }

def set_active_smtp_profile(profile_key):
    data = get_raw_smtp_data()
    if "profiles" in data and profile_key in data["profiles"]:
        data["active_profile"] = profile_key
        try:
            with open(SMTP_CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception:
            return False
    return False
