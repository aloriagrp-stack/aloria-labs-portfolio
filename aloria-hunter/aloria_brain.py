import os
import json
import re
import logging

logger = logging.getLogger("AloriaBrain")

# Path discovery for aloria_outreach_intelligence_library_v2.json
POSSIBLE_PATHS = [
    os.path.join(os.path.dirname(__file__), "..", "aloria_outreach_intelligence_library_v2.json"),
    os.path.join(os.path.dirname(__file__), "aloria_outreach_intelligence_library_v2.json"),
    os.path.abspath("aloria_outreach_intelligence_library_v2.json"),
    r"d:\alorialabs.in\aloria_outreach_intelligence_library_v2.json"
]

_LIBRARY_CACHE = None
_NICHE_INDEX = {}
_ALL_PROBLEMS = []

FRENCH_COUNTRIES = {
    "algeria", "algerie", "france", "morocco", "maroc", "tunisia", "tunisie",
    "belgium", "belgique", "senegal", "ivory coast", "cote d'ivoire", "madagascar",
    "cameroon", "cameroun", "mali", "congo"
}

def load_intelligence_library():
    global _LIBRARY_CACHE, _NICHE_INDEX, _ALL_PROBLEMS
    if _LIBRARY_CACHE is not None:
        return _LIBRARY_CACHE

    target_path = None
    for p in POSSIBLE_PATHS:
        if os.path.exists(p):
            target_path = os.path.abspath(p)
            break

    if not target_path:
        logger.error(f"Intelligence library JSON not found in any known paths: {POSSIBLE_PATHS}")
        return None

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        _LIBRARY_CACHE = data
        _NICHE_INDEX = {}
        _ALL_PROBLEMS = []

        niches = data.get("niches", [])
        for niche_obj in niches:
            problems = niche_obj.get("problems", [])
            if not problems:
                continue

            first_p_id = problems[0].get("problem_id", "")
            prefix = first_p_id.rsplit("_", 1)[0] if "_" in first_p_id else niche_obj.get("niche", "general").lower()

            _NICHE_INDEX[prefix] = {
                "niche_name": prefix.replace("_", " ").title(),
                "description": niche_obj.get("description", ""),
                "target_roles": niche_obj.get("target_roles", []),
                "problems": problems
            }

            for p in problems:
                p_copy = dict(p)
                p_copy["niche_prefix"] = prefix
                _ALL_PROBLEMS.append(p_copy)

        logger.info(f"Loaded {len(_NICHE_INDEX)} niches and {len(_ALL_PROBLEMS)} problem playbooks into Aloria Brain.")
        return _LIBRARY_CACHE
    except Exception as e:
        logger.error(f"Error loading intelligence library from {target_path}: {e}")
        return None

def detect_language(country="India", city=""):
    c = (country or "").lower().strip()
    ci = (city or "").lower().strip()
    if c in FRENCH_COUNTRIES or "algiers" in ci or "oran" in ci or "paris" in ci or "lyon" in ci or "casablanca" in ci:
        return "fr"
    return "en"

def match_niche(lead_niche=""):
    load_intelligence_library()
    if not _NICHE_INDEX:
        return None

    norm = re.sub(r'[^a-zA-Z0-9\s]', ' ', (lead_niche or "").lower()).strip()
    tokens = set(norm.split())

    # Exact key match
    if norm.replace(" ", "_") in _NICHE_INDEX:
        return norm.replace(" ", "_")

    # Keyword scoring across all niches
    best_niche = None
    best_score = 0

    for prefix, info in _NICHE_INDEX.items():
        score = 0
        prefix_tokens = set(prefix.split("_"))
        # Intersection with prefix
        score += len(tokens.intersection(prefix_tokens)) * 3

        # Description match
        desc_lower = info["description"].lower()
        for t in tokens:
            if len(t) > 3 and t in desc_lower:
                score += 1

        if score > best_score:
            best_score = score
            best_niche = prefix

    if best_score > 0:
        return best_niche

    # Fallback to general industrial/manufacturing or first available
    if "industrial_machinery" in _NICHE_INDEX:
        return "industrial_machinery"
    return list(_NICHE_INDEX.keys())[0] if _NICHE_INDEX else None

def clean_company_name(raw_name):
    if not raw_name:
        return "Your Company"
    name = raw_name.strip()
    patterns = [
        r"(?i)\s*(pvt\.?\s*ltd\.?|private\s+limited|ltd\.?|limited)$",
        r"(?i)\s*(llc|inc\.?|corp\.?|corporation|gmbh|co\.?)$",
        r"(?i)\s*(sarl|eurl|spa|snc)$",
    ]
    for p in patterns:
        name = re.sub(p, "", name).strip()
    return name or raw_name.strip()

def select_problem(lead):
    """
    Finds the optimal problem from the 500 playbooks for this lead
    based on lead's niche and audit signals.
    """
    load_intelligence_library()
    if not _ALL_PROBLEMS:
        return None

    lead_niche = lead.get("niche") or ""
    audit_text = (lead.get("audit_summary") or "").lower()
    prefix = match_niche(lead_niche)

    candidate_problems = _NICHE_INDEX.get(prefix, {}).get("problems", [])
    if not candidate_problems:
        candidate_problems = _ALL_PROBLEMS[:10]

    # Try matching audit signals to problems
    best_problem = None
    highest_signal_matches = 0

    for prob in candidate_problems:
        signals = prob.get("audit_signals_to_look_for", [])
        disqualifiers = prob.get("do_not_use_if", [])

        # Check disqualifiers
        disqualified = False
        for dis in disqualifiers:
            if any(term in audit_text for term in dis.lower().split() if len(term) > 4):
                disqualified = True
                break
        if disqualified:
            continue

        match_count = 0
        for sig in signals:
            words = [w.strip() for w in sig.lower().split() if len(w.strip()) > 3]
            for w in words:
                if w in audit_text:
                    match_count += 1

        if match_count > highest_signal_matches:
            highest_signal_matches = match_count
            best_problem = prob

    if not best_problem:
        # If no specific audit signal matched, choose a problem distributing across the 10 playbooks
        lead_id = lead.get("id") or 1
        idx = (lead_id - 1) % len(candidate_problems)
        best_problem = candidate_problems[idx]

    b_name = lead.get("business_name", "Lead")
    p_id = best_problem.get("problem_id", "unknown")
    p_title = best_problem.get("problem", "General Operations")
    print(f"  \033[92m[🧠 ALORIA BRAIN]\033[0m Matched \033[97m{b_name}\033[0m ({lead_niche}) \u2192 \033[96m{p_title}\033[0m [\033[90m{p_id}\033[0m]")

    return best_problem

def generate_dynamic_email(lead, email_type="INITIAL"):
    """
    Generates tailored email subject, plain text body, and responsive HTML
    using the 500-problem intelligence library for Aloria Labs.
    """
    load_intelligence_library()

    problem = select_problem(lead)
    if not problem:
        return None, None, None, None

    country = lead.get("country") or "India"
    city = lead.get("city") or "Mumbai"
    lang = detect_language(country, city)

    raw_comp_name = lead.get("business_name") or "Your Company"
    company_name = clean_company_name(raw_comp_name)
    first_name = "Team" if lang == "en" else "l'équipe"
    sender_name = "Shriyansh Aloria"
    website = "https://alorialabs.in"

    if email_type == "INITIAL":
        emails = problem.get("emails", {})
        email_data = emails.get(lang) or emails.get("en") or emails.get("fr")
        if not email_data:
            return None, None, None, None

        raw_subject = email_data.get("subject", "A question regarding digital operations")
        raw_body = email_data.get("body", "")

        subject = raw_subject.replace("{company}", company_name)\
                             .replace("{first_name}", first_name)\
                             .replace("{city}", city)

        body = raw_body.replace("{first_name}", first_name)\
                       .replace("{company}", company_name)\
                       .replace("{sender_name}", sender_name)\
                       .replace("{website}", website)\
                       .replace("{city}", city)

        if lang == "en":
            # Translate the 3 known raw French impact snippets into fluent professional English
            body = body.replace("des erreurs, des délais supplémentaires et une difficulté à suivre la performance",
                                "costly operational errors, processing delays, and difficulty tracking performance across teams")\
                       .replace("des retards de traitement, un manque de visibilité et davantage de travail manuel",
                                "processing bottlenecks, lack of end-to-end visibility, and excessive manual overhead")\
                       .replace("des pertes de temps, des informations dispersées et des relances difficiles à piloter",
                                "lost productivity, fragmented information across tools, and manual tracking that is hard to manage")

    elif email_type.startswith("FOLLOW_UP"):
        follow_ups = problem.get("follow_up_sequence", [])
        # Step 1 = follow_up_1 (Day 4), Step 3 = follow_up_3 (Day 12)
        step_key = "follow_up_1" if email_type == "FOLLOW_UP_1" else "follow_up_3"

        selected_step = None
        for step in follow_ups:
            if step.get("step") == step_key and step.get("channel") == "email":
                selected_step = step
                break

        if not selected_step and follow_ups:
            selected_step = follow_ups[0]

        prob_name = problem.get("problem", "operational workflows")
        if lang == "fr":
            subject = f"Courte relance — {prob_name}"
            raw_body = selected_step.get("body", "") if selected_step else f"Bonjour {first_name}, courte relance concernant {prob_name}."
        else:
            subject = f"Brief follow-up regarding {prob_name}"
            # Translate or adapt to English if needed
            raw_body = f"Hello {first_name},\n\nFollowing up briefly regarding {prob_name} at {company_name}. Is this an active area of focus for your operations team, or do you already have systems in place?\n\nBest regards,\n{sender_name}\nAloria Labs"

        body = raw_body.replace("{first_name}", first_name)\
                       .replace("{company}", company_name)\
                       .replace("{sender_name}", sender_name)\
                       .replace("{website}", website)
    else:
        subject = f"Operational inquiry regarding {company_name}"
        body = f"Hello {first_name},\n\nReaching out from Aloria Labs regarding {company_name} digital systems.\n\nBest regards,\n{sender_name}"

    html_body = f"""<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b; line-height: 1.65; max-width: 620px; font-size: 15px; white-space: pre-line;">{body}</div>"""

    meta = {
        "problem_id": problem.get("problem_id"),
        "problem_title": problem.get("problem"),
        "language": lang,
        "niche_prefix": problem.get("niche_prefix")
    }

    return subject, body, html_body, meta

def generate_dynamic_whatsapp(lead):
    """
    Generates tailored conversational WhatsApp message from the matched problem playbook.
    """
    load_intelligence_library()
    problem = select_problem(lead)
    if not problem:
        return None

    country = lead.get("country") or "India"
    city = lead.get("city") or "Mumbai"
    lang = detect_language(country, city)

    company_name = lead.get("business_name") or "Your Company"
    first_name = "Team"
    sender_name = "Shriyansh Aloria"
    prob_title = problem.get("problem", "operational workflows")

    wa_data = problem.get("whatsapp", {})
    if isinstance(wa_data, dict):
        raw_msg = wa_data.get("body", "")
    else:
        raw_msg = str(wa_data)

    if not raw_msg or (lang == "en" and wa_data.get("language") == "fr"):
        # English fallback
        raw_msg = f"Hi {first_name}, this is {sender_name} from Aloria Labs. Reaching out briefly regarding {prob_title} at {company_name}. We build custom operational systems and automations for modern teams. Would you be open to a quick 5-min chat to see how we tackle this?"

    msg = raw_msg.replace("{first_name}", first_name)\
                 .replace("{company}", company_name)\
                 .replace("{sender_name}", sender_name)\
                 .replace("{city}", city)

    return msg
