import json
from pathlib import Path

CONFIG_FILE = Path(__file__).resolve().parent / "businesses.json"

def load_businesses_config() -> dict:
    if not CONFIG_FILE.exists():
        return {"active_business_id": "aloria_labs", "businesses": {}}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {"active_business_id": "aloria_labs", "businesses": {}}
    except Exception:
        return {"active_business_id": "aloria_labs", "businesses": {}}

def save_businesses_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_active_business_id() -> str:
    cfg = load_businesses_config()
    return str(cfg.get("active_business_id", "aloria_labs"))

def get_active_business() -> dict:
    cfg = load_businesses_config()
    active_id = cfg.get("active_business_id", "aloria_labs")
    businesses = cfg.get("businesses", {})
    if isinstance(businesses, dict):
        biz = businesses.get(active_id)
        if isinstance(biz, dict):
            return biz
        # Fallback to first business in list if present
        if businesses:
            first_key = list(businesses.keys())[0]
            first_val = businesses.get(first_key)
            if isinstance(first_val, dict):
                return first_val
    return {
        "name": "Aloria Labs",
        "tagline": "Autonomous Web Infrastructure",
        "niche": "Software & Web Infrastructure",
        "default_niches": ["Restaurants", "Hotels"],
        "country": "Algeria",
        "cities": ["Algiers"],
        "sender_profile": "gmail",
        "sender_display_name": "Shriyansh Aloria — Aloria Labs"
    }

def set_active_business(biz_id):
    cfg = load_businesses_config()
    businesses = cfg.get("businesses", {})
    if isinstance(businesses, dict) and biz_id in businesses:
        cfg["active_business_id"] = biz_id
        save_businesses_config(cfg)
        return True
    return False

def list_businesses():
    cfg = load_businesses_config()
    businesses = cfg.get("businesses", {})
    if not isinstance(businesses, dict):
        businesses = {}
    return businesses, cfg.get("active_business_id", "aloria_labs")

def get_business(biz_id: str) -> dict:
    cfg = load_businesses_config()
    businesses = cfg.get("businesses", {})
    if isinstance(businesses, dict):
        biz = businesses.get(biz_id)
        if isinstance(biz, dict):
            return biz
    return {}

def get_pitch_template(biz_id, pitch_key):
    biz = get_business(biz_id)
    if biz and "pitches" in biz and pitch_key in biz["pitches"]:
        return biz["pitches"][pitch_key]
    return None

def get_target_settings(biz_id):
    biz = get_business(biz_id)
    if not biz:
        return {"country": "", "city": "", "niche": ""}
    return {
        "country": biz.get("target_country", ""),
        "city": biz.get("target_city", ""),
        "niche": biz.get("target_niche", "")
    }

def set_target_settings(biz_id, country=None, city=None, niche=None):
    cfg = load_businesses_config()
    if biz_id in cfg.get("businesses", {}):
        if country is not None:
            cfg["businesses"][biz_id]["target_country"] = country.strip()
        if city is not None:
            cfg["businesses"][biz_id]["target_city"] = city.strip()
        if niche is not None:
            cfg["businesses"][biz_id]["target_niche"] = niche.strip()
        save_businesses_config(cfg)
        return True
    return False

def get_sender_profile(biz_id):
    biz = get_business(biz_id)
    if biz:
        return biz.get("sender_profile")
    return None

def set_sender_profile(biz_id, profile_key):
    cfg = load_businesses_config()
    if biz_id in cfg.get("businesses", {}):
        cfg["businesses"][biz_id]["sender_profile"] = profile_key
        save_businesses_config(cfg)
        return True
    return False


