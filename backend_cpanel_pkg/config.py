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

# Browser Display: False = Visible window on screen (you can watch it type/click), True = Silent background (100% headless)
HEADLESS = True

# Rate Limiting & High-Speed Adaptive Pacing
MAX_LEADS_PER_RUN = 50
EMAIL_DELAY_MINUTES = 0  # Replaced by high-speed adaptive jitter pacing in seconds
DISPATCH_DELAY_SECONDS = 10  # 8-12s humanized random jitter between dispatches
PACING_MODE = "TURBO"  # "TURBO" (6-10s) | "BALANCED" (12-18s) | "SAFE" (25-35s)
MAX_EMAILS_PER_DAY = 1000  # Full Swarm capacity
MAX_DELIVERED_PER_ACCOUNT_PER_DAY_GHS = 50       # Exactly 50 successfully delivered emails per account for GetHotelStays
MAX_DELIVERED_PER_ACCOUNT_PER_DAY_ALORIA = 100   # Exactly 100 successfully delivered emails per account for Aloria Labs

# 10-12 Parallel Agent Lead Hunter Swarm Settings
SWARM_WORKERS = 12
SWARM_MAX_CONCURRENCY = 4  # Concurrently active Playwright processes to manage RAM safely
SWARM_BUFFER_GOAL = 200    # Default lead buffer target
AUDITOR_WORKERS = 100      # 100 concurrent lightweight Python workers (~1MB RAM each) for blazing-fast website auditing

def get_max_delivered_quota(business_id="gethotelstays"):
    if str(business_id).lower() in ["aloria_labs", "aloria"]:
        return MAX_DELIVERED_PER_ACCOUNT_PER_DAY_ALORIA
    return MAX_DELIVERED_PER_ACCOUNT_PER_DAY_GHS

MAX_DELIVERED_PER_ACCOUNT_PER_DAY = MAX_DELIVERED_PER_ACCOUNT_PER_DAY_GHS
FOLLOW_UP_INTERVAL_DAYS = 3  # Follow up after 3 days of no response
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

def find_profile_key_by_email(email_addr):
    """Looks up the profile key in smtp_config.json matching the given sender email address."""
    if not email_addr:
        return None
    clean = str(email_addr).strip().lower()
    profiles, _ = list_smtp_profiles()
    for key, p_data in profiles.items():
        p_email = str(p_data.get("email") or "").strip().lower()
        if p_email == clean:
            return key
    return None
