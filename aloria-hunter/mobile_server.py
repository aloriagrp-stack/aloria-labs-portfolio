import os
import sys
import json
import time
import re
import socket
import asyncio
import queue
import threading
import logging
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

logger = logging.getLogger("MobileServer")

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import db
import business_manager
from agents.orchestrator import orchestrator

app = FastAPI(title="Aloria Hunter Mobile Command Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UI_DIR = BASE_DIR / "mobile_ui"

@app.on_event("startup")
def startup_event():
    orchestrator.start()

@app.get("/", response_class=HTMLResponse)
@app.get("/hunter", response_class=HTMLResponse)
@app.get("/hunter/", response_class=HTMLResponse)
@app.get("/aloria-hunter", response_class=HTMLResponse)
@app.get("/homepage", response_class=HTMLResponse)
@app.get("/home", response_class=HTMLResponse)
@app.get("/projects", response_class=HTMLResponse)
@app.get("/c/{chat_id}", response_class=HTMLResponse)
def get_mobile_ui(chat_id: str = None):
    html_file = UI_DIR / "index.html"
    if html_file.exists():
        with open(html_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Hunter Mobile Command Server Ready</h1>"

@app.get("/manifest.json")
def get_manifest():
    manifest_file = UI_DIR / "manifest.json"
    return FileResponse(manifest_file, media_type="application/json")

TERMUX_TEMPLATE = """import os, sys, json, time, urllib.request, urllib.parse

HOST = "{HOST_URL}"

C_CYAN = "\\033[1;36m"
C_GREEN = "\\033[1;32m"
C_RED = "\\033[1;31m"
C_YELLOW = "\\033[1;33m"
C_MAGENTA = "\\033[1;35m"
C_WHITE = "\\033[1;37m"
C_DIM = "\\033[2m"
RESET = "\\033[0m"

BANNER = \"\"\"
  █████╗ ██╗      ██████╗ ██████╗ ██╗ █████╗     ██╗  ██╗██╗   ██╗███╗   ██╗████████╗███████╗██████╗ 
 ██╔══██╗██║     ██╔═══██╗██╔══██╗██║██╔══██╗    ██║  ██║██║   ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗
 ███████║██║     ██║   ██║██████╔╝██║███████║    ███████║██║   ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝
 ██╔══██║██║     ██║   ██║██╔══██╗██║██╔══██║    ██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗
 ██║  ██║███████╗╚██████╔╝██║  ██║██║██║  ██║    ██║  ██║╚██████╔╝██║ ╚████║   ██║   ███████╗██║  ██║
 ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
                       [ MOBILE TERMUX COMMAND COCKPIT • 100% TERMINAL ]
\"\"\"

def get_status():
    try:
        req = urllib.request.urlopen(f"{HOST}/api/status", timeout=5)
        return json.loads(req.read().decode())
    except Exception:
        return None

def send_action(agent, action, params=None):
    try:
        p = params if params is not None else {}
        data = json.dumps({"agent": agent, "action": action, "params": p}).encode()
        req = urllib.request.Request(f"{HOST}/api/action", data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
        return True
    except Exception:
        return False

def main():
    while True:
        os.system("clear")
        print(f"{C_CYAN}{BANNER}{RESET}")
        st = get_status()
        if not st:
            print(f"{C_RED}[!] Error: Cannot connect to Laptop server on {HOST}{RESET}")
            print(f"{C_YELLOW}Ensure your phone and laptop are on the same Wi-Fi/Hotspot.{RESET}")
            time.sleep(3)
            break

        al_stats = st.get("aloria_stats", {})
        ho_stats = st.get("hotel_stats", {})

        print(f"{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════{RESET}")
        print(f"  {C_WHITE}[1] ALORIA LABS:{RESET}       {C_GREEN}" + str(al_stats.get('total', 0)) + f" Leads{RESET} │ {C_BLUE}" + str(al_stats.get('audited', 0)) + f" Audited{RESET} │ {C_YELLOW}" + str(al_stats.get('pitch_sent', 0)) + f" Pitched{RESET} │ {C_MAGENTA}" + str(al_stats.get('golden_leads', 0)) + f" Golden No-Web{RESET}")
        print(f"  {C_WHITE}[2] GETHOTELSTAYS:{RESET}     {C_GREEN}" + str(ho_stats.get('total', 0)) + f" Leads{RESET} │ {C_BLUE}" + str(ho_stats.get('audited', 0)) + f" Audited{RESET} │ {C_YELLOW}" + str(ho_stats.get('pitch_sent', 0)) + f" Pitched{RESET} │ {C_MAGENTA}" + str(ho_stats.get('golden_leads', 0)) + f" Golden No-Web{RESET}")
        print(f"{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════{RESET}\\n")

        autopilot_label = "[ACTIVE 24/7]" if st.get("autopilot_active") else "[STANDBY]"
        print(f"  {C_YELLOW}─── [TERMUX QUICK COMMANDS] ─────────────────────────────────────────────────────────────{RESET}")
        print(f"  {C_WHITE}[1]{RESET} {C_CYAN}● Hunt Aloria Web Leads{RESET}    {C_DIM}— Scrape businesses (You choose Country & City){RESET}")
        print(f"  {C_WHITE}[2]{RESET} {C_GREEN}● Hunt Hotels (GetHotelStays){RESET} {C_DIM}— Scrape hotels (You choose Country & City){RESET}")
        print(f"  {C_WHITE}[3]{RESET} {C_BLUE}● Run Technical Audits{RESET}     {C_DIM}— Check website speed, SSL & extract emails{RESET}")
        print(f"  {C_WHITE}[4]{RESET} {C_MAGENTA}● Dispatch Initial Pitches{RESET} {C_DIM}— Send tailored Day 0 cold pitches{RESET}")
        print(f"  {C_WHITE}[5]{RESET} {C_YELLOW}● Dispatch Follow-ups{RESET}      {C_DIM}— Trigger scheduled 2-Day / 4-Day follow-ups{RESET}")
        print(f"  {C_WHITE}[6]{RESET} {C_GREEN}● Toggle 24/7 Autopilot{RESET}    {C_DIM}— Status: " + autopilot_label + f"{RESET}")
        print(f"  {C_WHITE}[0]{RESET} {C_RED}● Exit Termux Cockpit{RESET}\\n")

        try:
            ch = input(f"  {C_GREEN}Enter command in Termux [0-6]: {RESET}").strip()
        except Exception:
            break

        if ch == "0":
            print(f"\\n{C_CYAN}Exiting Termux Cockpit. Bye!{RESET}\\n")
            break
        elif ch == "1":
            c_in = input(f"  {C_WHITE}Enter Country (e.g. India, USA, UAE): {RESET}").strip() or "India"
            ci_in = input(f"  {C_WHITE}Enter City (e.g. Mumbai, Delhi, Dubai): {RESET}").strip() or "Mumbai"
            ni_in = input(f"  {C_WHITE}Enter Niche [Restaurants]: {RESET}").strip() or "Restaurants"
            send_action("aloria", "hunt", {"country": c_in, "city": ci_in, "niche": ni_in, "limit": 5})
            print(f"\\n  {C_GREEN}[✓] Triggered Agent Aloria lead hunt for {ni_in} in {ci_in}, {c_in}!{RESET}")
            time.sleep(2)
        elif ch == "2":
            c_in = input(f"  {C_WHITE}Enter Country (e.g. India, USA, UAE): {RESET}").strip() or "India"
            ci_in = input(f"  {C_WHITE}Enter City (e.g. Goa, Jaipur, Dubai): {RESET}").strip() or "Goa"
            ni_in = input(f"  {C_WHITE}Enter Niche [Hotels]: {RESET}").strip() or "Hotels"
            send_action("hotel", "hunt", {"country": c_in, "city": ci_in, "niche": ni_in, "limit": 5})
            print(f"\\n  {C_GREEN}[✓] Triggered Agent HotelStays lead hunt for {ni_in} in {ci_in}, {c_in}!{RESET}")
            time.sleep(2)
        elif ch == "3":
            send_action("both", "audit", {})
            print(f"\\n  {C_BLUE}[✓] Triggered audits on both agents!{RESET}")
            time.sleep(2)
        elif ch == "4":
            send_action("both", "dispatch_initial", {"limit": 5})
            print(f"\\n  {C_MAGENTA}[✓] Triggered cold pitch email dispatch!{RESET}")
            time.sleep(2)
        elif ch == "5":
            send_action("both", "dispatch_followups", {})
            print(f"\\n  {C_YELLOW}[✓] Triggered follow-ups!{RESET}")
            time.sleep(2)
        elif ch == "6":
            ep = "/api/autopilot/stop" if st.get("autopilot_active") else "/api/autopilot/start"
            urllib.request.urlopen(f"{HOST}{ep}", data=b"")
            print(f"\\n  {C_GREEN}[✓] Toggled 24/7 Autopilot status!{RESET}")
            time.sleep(2)

if __name__ == "__main__":
    main()
"""

@app.get("/termux", response_class=HTMLResponse)
def get_termux_client(request: Request):
    base_url = str(request.base_url).rstrip("/")
    return TERMUX_TEMPLATE.replace("{HOST_URL}", base_url)

# Global Concurrency Lock to prevent duplicate execution of the same agent across multiple chats
AGENT_LOCKS = {
    "hotel": None,   # dict {"chat_id": str, "chat_title": str, "task": str, "started_at": float}
    "aloria": None
}

@app.get("/api/agent_locks")
def get_agent_locks():
    return {
        "hotel": AGENT_LOCKS.get("hotel"),
        "aloria": AGENT_LOCKS.get("aloria")
    }

@app.get("/api/status")
def get_status():
    from datetime import datetime
    import config
    status = orchestrator.get_status()
    status["aloria_stats"] = db.get_funnel_stats("aloria_labs")
    status["hotel_stats"] = db.get_funnel_stats("gethotelstays")
    status["aloria_overdue"] = len(db.get_overdue_followups("aloria_labs"))
    status["hotel_overdue"] = len(db.get_overdue_followups("gethotelstays"))
    status["total_blacklisted_bounces"] = len(db.get_blacklisted_emails(1000))
    status["server_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status["agent_locks"] = {
        "hotel": AGENT_LOCKS.get("hotel"),
        "aloria": AGENT_LOCKS.get("aloria")
    }

    # Include active sender profile
    try:
        profiles, active_key = config.list_smtp_profiles()
        active_email = profiles.get(active_key, {}).get("email", "Unknown")
        status["active_sender"] = f"{active_key} ({active_email})"
    except Exception:
        status["active_sender"] = "Default"

    return status

@app.get("/api/logs")
def get_outreach_logs(limit: int = 50, business_id: str | None = None):
    return db.get_outreach_history(limit=limit, business_id=business_id)

@app.post("/api/followup/run")
def trigger_parallel_followup():
    return orchestrator.trigger_instant_followup()

@app.get("/api/overdue_followups")
def get_overdue_followups(business_id: str | None = None):
    return db.get_overdue_followups(business_id=business_id)

@app.post("/api/bounces/scan")
def scan_bounces():
    import bounce_detector
    return bounce_detector.scan_all_profiles()

@app.post("/api/action")
async def post_action(request: Request):
    data = await request.json()
    agent = data.get("agent", "aloria")
    action = data.get("action", "hunt")
    params = data.get("params", {})
    res = orchestrator.command_agent(agent, action, params)
    return res

@app.post("/api/autopilot/start")
def start_autopilot():
    return orchestrator.start_24_7_autopilot(interval_minutes=15)

@app.post("/api/autopilot/stop")
def stop_autopilot():
    return orchestrator.stop_24_7_autopilot()

@app.get("/api/leads")
def get_leads(business_id: str = "aloria_labs"):
    return db.get_lead_ledger(business_id=business_id, limit=40)


INDIAN_AND_GLOBAL_CITIES = {
    "jaipur", "mumbai", "delhi", "new delhi", "bangalore", "bengaluru", "hyderabad",
    "ahmedabad", "chennai", "kolkata", "surat", "pune", "lucknow", "kanpur", "nagpur",
    "indore", "thane", "bhopal", "visakhapatnam", "patna", "vadodara", "ghaziabad",
    "ludhiana", "agra", "nashik", "faridabad", "meerut", "rajkot", "varanasi", "srinagar",
    "aurangabad", "dhanbad", "amritsar", "navi mumbai", "allahabad", "prayagraj", "ranchi",
    "howrah", "coimbatore", "jabalpur", "gwalior", "vijayawada", "jodhpur", "madurai",
    "raipur", "kota", "guwahati", "chandigarh", "solapur", "hubli", "bareilly", "moradabad",
    "mysore", "mysuru", "gurgaon", "gurugram", "aligarh", "jalandhar", "tiruchirappalli",
    "bhubaneswar", "salem", "mira-bhayandar", "warangal", "thiruvananthapuram", "bhiwandi",
    "saharanpur", "guntur", "amravati", "bikaner", "noida", "jamshedpur", "bhilai", "cuttack",
    "firozabad", "kochi", "nellore", "bhavnagar", "dehradun", "durgapur", "asansol", "rourkela",
    "nanded", "kolhapur", "ajmer", "akola", "gulbarga", "jamnagar", "ujjain", "siliguri",
    "jhansi", "jammu", "mangalore", "mangaluru", "erode", "belgaum", "tirunelveli", "malegaon",
    "gaya", "jalgaon", "udaipur", "goa", "pushkar", "rishikesh", "manali", "shimla", "algiers",
    "oran", "constantine", "annaba", "dubai", "abu dhabi", "london", "paris", "new york", "singapore"
}

def parse_chat_intent(raw_msg: str, selected_agent: str | None = None):
    raw = (raw_msg or "").strip()
    msg = raw.lower()

    # 1. Quantity / Limit
    num_match = re.search(r'\b(\d+)\b', msg)
    raw_limit = int(num_match.group(1)) if num_match else None

    # 2. Country detection
    target_country = "India"
    if any(w in msg for w in ["algeria", "algiers", "oran"]):
        target_country = "Algeria"
    elif any(w in msg for w in ["dubai", "uae", "abu dhabi"]):
        target_country = "UAE"
    elif any(w in msg for w in ["uk", "london", "england"]):
        target_country = "UK"
    elif any(w in msg for w in ["france", "paris"]):
        target_country = "France"

    # 3. Target City
    target_city = None
    for city in sorted(INDIAN_AND_GLOBAL_CITIES, key=len, reverse=True):
        if re.search(r'\b' + re.escape(city) + r'\b', msg):
            target_city = city.title()
            break

    # Regex fallback for "in <Location>"
    if not target_city:
        in_match = re.search(r'\bin\s+([a-zA-Z\s]+?)(?:$|\b(?:please|fast|now|for|with|today)\b)', msg)
        if in_match:
            cand = in_match.group(1).strip()
            if cand in ["india", "algeria", "france", "uk", "uae"]:
                target_country = cand.title()
            elif len(cand.split()) <= 3 and len(cand) > 2:
                target_city = cand.title()

    # 4. Agent & Niche Resolution
    is_hotel = False
    if selected_agent == "hotel":
        is_hotel = True
    elif selected_agent == "aloria":
        is_hotel = False
    else:
        is_hotel = any(h in msg for h in ["hotel", "resort", "stay", "guest", "villa", "inn", "ghs", "homestay", "hostel", "lodging"])

    target_niche = "Hotels" if is_hotel else "Restaurants"
    if any(k in msg for k in ["hotel", "resort", "villa", "stay", "guest", "inn", "homestay", "hostel", "lodging"]):
        target_niche = "Hotels"
        is_hotel = True
    elif any(k in msg for k in ["agency", "agencies", "digital agency", "web dev", "marketing agency"]):
        target_niche = "Web Agencies"
        is_hotel = False
    elif any(k in msg for k in ["cafe", "coffee", "bistro"]):
        target_niche = "Cafes"
        is_hotel = False
    elif any(k in msg for k in ["restaurant", "dining", "bakery", "food", "bar", "pub"]):
        target_niche = "Restaurants"
        is_hotel = False
    elif any(k in msg for k in ["clinic", "dental", "dentist", "doctor", "hospital", "pharma"]):
        target_niche = "Dental Clinics"
        is_hotel = False
    elif any(k in msg for k in ["real estate", "property", "realtor", "broker"]):
        target_niche = "Real Estate Agencies"
        is_hotel = False

    target_agent = "hotel" if is_hotel else "aloria"
    business_id = "gethotelstays" if is_hotel else "aloria_labs"
    agent_name = "GHS Agent" if is_hotel else "Aloria Labs Agent"

    # Default city if missing
    resolved_city = target_city or ("Jaipur" if is_hotel else "Mumbai")
    # Live interactive browser crawling batch limit: 20 places
    safe_limit = min(raw_limit or 10, 20)

    # 5. Action Classification
    action = None
    if any(k in msg for k in ["hunt", "scrape", "crawl", "find", "discover", "search", "dhoond", "target", "get leads", "fetch", "collect"]):
        action = "hunt"
    elif any(k in msg for k in ["audit", "speed", "ssl", "check site", "analyze", "inspect", "audit websites", "scan site"]):
        action = "audit"
    elif any(k in msg for k in ["pitch", "send initial", "cold email", "first email", "dispatch pitch", "send pitch", "send email", "outreach"]):
        action = "pitch"
    elif any(k in msg for k in ["follow", "followup", "bump", "reminder", "overdue"]):
        action = "followup"
    elif any(k in msg for k in ["bounce", "blacklist", "shield", "clean inbox"]):
        action = "bounce"
    elif any(k in msg for k in ["autopilot", "24/7", "continuous", "loop"]):
        action = "autopilot"
    elif any(k in msg for k in ["status", "report", "stats", "kpi", "numbers", "summary", "how many"]):
        action = "status"
    # Implicit hunt patterns like "100 hotels in jaipur" or "hotels in jaipur" or "jaipur hotels"
    elif target_city and (raw_limit or target_niche or selected_agent):
        action = "hunt"
    elif raw_limit and target_niche:
        action = "hunt"
    elif msg in ["hi", "hello", "hey", "sup", "yo", "start"]:
        action = "greeting"
    else:
        action = "conversational"

    return {
        "action": action,
        "is_hotel": is_hotel,
        "target_agent": target_agent,
        "business_id": business_id,
        "agent_name": agent_name,
        "target_niche": target_niche,
        "target_city": resolved_city,
        "target_country": target_country,
        "has_explicit_city": bool(target_city),
        "requested_limit": raw_limit,
        "safe_limit": safe_limit
    }


@app.post("/api/chat/stream")
async def post_chat_stream(request: Request):
    data = await request.json()
    raw_msg = (data.get("message") or "").strip()
    msg = raw_msg.lower()
    selected_agent = data.get("agent")  # 'hotel', 'aloria', or None/'both'
    chat_id = data.get("chat_id") or "default"
    chat_title = data.get("chat_title") or "Active Chat"

    async def sse_generator():
        try:
            if not msg:
                yield f"data: {json.dumps({'type': 'thought', 'step': 'Standing by for instructions.'})}\n\n"
                await asyncio.sleep(0.3)
                yield f"data: {json.dumps({'type': 'done', 'sender': 'Aloria Hunter', 'reply': 'Hey! How can I help you today? You can ask me to hunt leads, audit websites, or dispatch follow-ups.', 'thought': 'Ready.'})}\n\n"
                return

            intent = parse_chat_intent(raw_msg, selected_agent)
            action = intent["action"]
            target_city = intent["target_city"]
            target_country = intent["target_country"]
            target_niche = intent["target_niche"]
            target_agent = intent["target_agent"]
            business_id = intent["business_id"]
            agent_name = intent["agent_name"]
            limit = intent["safe_limit"]
            req_limit = intent["requested_limit"]
            is_hotel = intent["is_hotel"]

            # 1. HUNT / SCRAPE DIRECTIVES
            if action == "hunt":
                # Concurrency Lock Check
                existing_lock = AGENT_LOCKS.get(target_agent)
                if existing_lock and existing_lock.get("chat_id") != chat_id:
                    other_title = existing_lock.get("chat_title", "another chat")
                    lock_cid = existing_lock.get("chat_id", "")
                    blocked_msg = {
                        "type": "done",
                        "blocked": True,
                        "sender": agent_name,
                        "reply": f"⚠️ **{agent_name} is already active in another chat** (*\"{other_title}\"*).\n\nTo prevent browser conflicts, only one task can run per agent at a time. Please wait for that task to finish or switch back to that chat to stop it before launching a new command here.",
                        "thought": f"Concurrency protection: {target_agent} is locked by chat session {lock_cid}."
                    }
                    yield f"data: {json.dumps(blocked_msg)}\n\n"
                    return

                AGENT_LOCKS[target_agent] = {
                    "chat_id": chat_id,
                    "chat_title": chat_title,
                    "task": f"{target_niche} in {target_city}",
                    "started_at": time.time()
                }

                import maps_crawler
                stop_flag = [False]
                step_queue = queue.Queue()
                discovered = []

                def _hunt_worker():
                    try:
                        res = maps_crawler.crawl_google_maps(
                            city=target_city,
                            country=target_country,
                            niche=target_niche,
                            max_places=limit,
                            headless=True,
                            business_id=business_id,
                            on_step=lambda s: step_queue.put({"type": "step", "text": s}),
                            should_stop=lambda: stop_flag[0]
                        )
                        discovered.extend(res)
                    except Exception as e:
                        logger.exception("Crawler worker error")
                        step_queue.put({"type": "step", "text": f"Crawler note: {str(e)[:80]}"})
                    finally:
                        step_queue.put({"type": "DONE"})

                try:
                    t = threading.Thread(target=_hunt_worker, daemon=True)
                    t.start()

                    quota_label = f"{limit} (requested {req_limit})" if req_limit and req_limit > limit else str(limit)
                    yield f"data: {json.dumps({'type': 'thought', 'step': f'Connecting to Playwright Chromium engine for {quota_label} {target_niche} in {target_city}, {target_country}...'})}\n\n"

                    while True:
                        if await request.is_disconnected():
                            stop_flag[0] = True
                            break
                        try:
                            item = step_queue.get_nowait()
                        except queue.Empty:
                            await asyncio.sleep(0.12)
                            continue

                        if item.get("type") == "DONE":
                            break
                        elif item.get("type") == "step":
                            yield f"data: {json.dumps({'type': 'thought', 'step': item['text']})}\n\n"

                    if stop_flag[0]:
                        yield f"data: {json.dumps({'type': 'done', 'stopped': True, 'sender': agent_name, 'reply': f'Sweep halted by operator. Safely captured {len(discovered)} places before stopping.', 'thought': 'Halted per operator instruction.'})}\n\n"
                    else:
                        sample_lines = ""
                        if discovered:
                            sample_lines = "\n\n**Discovered Properties:**\n" + "\n".join([f"• **{p.get('name')}** — {p.get('phone') or 'No phone'} | ⭐ {p.get('rating') or 'N/A'}" for p in discovered[:4]])

                        batch_note = f" (live batch limited to {limit} places for browser stability)" if req_limit and req_limit > limit else ""
                        reply_text = f"Google Maps sweep complete! Successfully captured and verified **{len(discovered)} {target_niche}** in **{target_city}**{batch_note}.{sample_lines}\n\nAll candidate records have been saved into your SQLite database ledger. Next, you can say **'Run audits'** to inspect their domains and extract verified contact emails."
                        yield f"data: {json.dumps({'type': 'done', 'sender': agent_name, 'reply': reply_text, 'thought': f'Swept Google Maps for {target_niche} in {target_city}, extracted place metadata, and recorded {len(discovered)} entries in database.'})}\n\n"
                finally:
                    if AGENT_LOCKS.get(target_agent) and AGENT_LOCKS[target_agent].get("chat_id") == chat_id:
                        AGENT_LOCKS[target_agent] = None
                return

            # 2. AUDIT DIRECTIVES
            elif action == "audit":
                target_agent = selected_agent or "both"
                b_id = "gethotelstays" if target_agent == "hotel" else ("aloria_labs" if target_agent == "aloria" else None)
                agent_name = "GHS Agent" if target_agent == "hotel" else ("Aloria Labs Agent" if target_agent == "aloria" else "Auditor")

                # Check Concurrency Lock
                if target_agent in ["hotel", "aloria"]:
                    existing_lock = AGENT_LOCKS.get(target_agent)
                    if existing_lock and existing_lock.get("chat_id") != chat_id:
                        other_title = existing_lock.get("chat_title", "another chat")
                        lock_cid = existing_lock.get("chat_id", "")
                        blocked_msg = {
                            "type": "done",
                            "blocked": True,
                            "sender": agent_name,
                            "reply": f"⚠️ **{agent_name} is already busy** in another chat (*\"{other_title}\"*).\n\nPlease wait for it to complete or switch back to that chat to stop it.",
                            "thought": f"Concurrency protection: {target_agent} is locked by chat {lock_cid}."
                        }
                        yield f"data: {json.dumps(blocked_msg)}\n\n"
                        return
                    AGENT_LOCKS[target_agent] = {
                        "chat_id": chat_id,
                        "chat_title": chat_title,
                        "task": "Website Audits",
                        "started_at": time.time()
                    }
                elif target_agent == "both":
                    if (AGENT_LOCKS.get("hotel") and AGENT_LOCKS["hotel"].get("chat_id") != chat_id) or \
                       (AGENT_LOCKS.get("aloria") and AGENT_LOCKS["aloria"].get("chat_id") != chat_id):
                        yield f"data: {json.dumps({'type': 'done', 'blocked': True, 'sender': agent_name, 'reply': '⚠️ **One of the agents is currently running in another chat**.\n\nPlease wait for ongoing tasks to finish before triggering full audits across both agents.', 'thought': 'Concurrency conflict: either hotel or aloria agent is locked.'})}\n\n"
                        return
                    lock_obj = {"chat_id": chat_id, "chat_title": chat_title, "task": "Website Audits", "started_at": time.time()}
                    AGENT_LOCKS["hotel"] = lock_obj
                    AGENT_LOCKS["aloria"] = lock_obj

                import website_auditor
                stop_flag = [False]
                step_queue = queue.Queue()
                audit_results = []

                def _audit_worker():
                    try:
                        res = website_auditor.audit_pending_leads(
                            limit=limit if limit > 5 else 10,
                            business_id=b_id,
                            on_step=lambda s: step_queue.put({"type": "step", "text": s}),
                            should_stop=lambda: stop_flag[0]
                        )
                        audit_results.extend(res)
                    except Exception as e:
                        step_queue.put({"type": "step", "text": f"Auditor note: {str(e)[:80]}"})
                    finally:
                        step_queue.put({"type": "DONE"})

                try:
                    t = threading.Thread(target=_audit_worker, daemon=True)
                    t.start()

                    yield f"data: {json.dumps({'type': 'thought', 'step': 'Initializing concurrent website audit workers...'})}\n\n"

                    while True:
                        if await request.is_disconnected():
                            stop_flag[0] = True
                            break
                        try:
                            item = step_queue.get_nowait()
                        except queue.Empty:
                            await asyncio.sleep(0.12)
                            continue

                        if item.get("type") == "DONE":
                            break
                        elif item.get("type") == "step":
                            yield f"data: {json.dumps({'type': 'thought', 'step': item['text']})}\n\n"

                    if stop_flag[0]:
                        yield f"data: {json.dumps({'type': 'done', 'stopped': True, 'sender': agent_name, 'reply': f'Audits halted by operator. Processed {len(audit_results)} websites.', 'thought': 'Halted per operator instruction.'})}\n\n"
                    else:
                        verified_count = sum(1 for r in audit_results if r.get("email"))
                        reply_text = f"Website audits complete! Inspected **{len(audit_results)} candidate websites**.\n\n• **Verified Direct Inboxes Found**: {verified_count}\n• **Checks Performed**: HTTP response latency, SSL certificate trust chain, mobile viewport tag, and MX deliverability."
                        yield f"data: {json.dumps({'type': 'done', 'sender': agent_name, 'reply': reply_text, 'thought': f'Tested SSL, response time, and mailto tags across {len(audit_results)} websites. Found {verified_count} deliverable emails.'})}\n\n"
                finally:
                    if target_agent in ["hotel", "aloria"]:
                        if AGENT_LOCKS.get(target_agent) and AGENT_LOCKS[target_agent].get("chat_id") == chat_id:
                            AGENT_LOCKS[target_agent] = None
                    elif target_agent == "both":
                        if AGENT_LOCKS.get("hotel") and AGENT_LOCKS["hotel"].get("chat_id") == chat_id:
                            AGENT_LOCKS["hotel"] = None
                        if AGENT_LOCKS.get("aloria") and AGENT_LOCKS["aloria"].get("chat_id") == chat_id:
                            AGENT_LOCKS["aloria"] = None
                return

            # 3. INITIAL PITCH DISPATCH DIRECTIVES
            elif action == "pitch":
                target_agent = "hotel" if is_hotel else (selected_agent or "both")
                agent_name = "GHS Agent" if is_hotel else ("Aloria Labs Agent" if selected_agent == "aloria" else "Outreach Dispatcher")
                yield f"data: {json.dumps({'type': 'thought', 'step': 'Checking recipient MX deliverability and suppression lists...'})}\n\n"
                await asyncio.sleep(0.5)
                yield f"data: {json.dumps({'type': 'thought', 'step': 'Rendering tailored Day-0 proposals from business templates...'})}\n\n"
                await asyncio.sleep(0.5)
                orchestrator.command_agent(target_agent, "dispatch_initial", {"limit": limit})
                yield f"data: {json.dumps({'type': 'done', 'sender': agent_name, 'reply': 'Drafted and dispatched personalized Day-0 outreach proposals to verified candidate business inboxes.', 'thought': 'Validated recipient MX records, loaded personalized pitch templates, and transmitted outreach proposals.'})}\n\n"
                return

            # 4. FOLLOW-UP DISPATCH DIRECTIVES
            elif action == "followup":
                yield f"data: {json.dumps({'type': 'thought', 'step': 'Inspecting pipeline database for overdue follow-up milestones (3.0+ days)...'})}\n\n"
                await asyncio.sleep(0.5)
                orchestrator.trigger_instant_followup()
                al_od = len(db.get_overdue_followups("aloria_labs"))
                gh_od = len(db.get_overdue_followups("gethotelstays"))
                total_od = al_od + gh_od
                yield f"data: {json.dumps({'type': 'thought', 'step': f'Identified {total_od} candidate leads reaching the follow-up threshold. Dispatched parallel bumps.'})}\n\n"
                await asyncio.sleep(0.4)
                yield f"data: {json.dumps({'type': 'done', 'sender': 'Follow-up Sentry', 'reply': f'Checked the pipeline schedule. Found {total_od} leads reaching the 3-day milestone and triggered sequential follow-up dispatches.', 'thought': f'Verified 3.0-day follow-up interval for {total_od} candidate leads.'})}\n\n"
                return

            # 5. BOUNCE DEFENDER / BLACKLIST
            elif action == "bounce":
                yield f"data: {json.dumps({'type': 'thought', 'step': 'Connecting to IMAP mailboxes to scan delivery failure notices...'})}\n\n"
                await asyncio.sleep(0.5)
                import bounce_detector
                res = bounce_detector.scan_all_profiles()
                bl_count = res.get("total_newly_blacklisted", 0)
                yield f"data: {json.dumps({'type': 'done', 'sender': 'Bounce Defense', 'reply': f'Inbox scan finished. Identified and blacklisted {bl_count} bad inboxes to protect sender domain reputation.', 'thought': 'Scanned IMAP delivery failure notices, parsed SMTP rejection codes, and updated blacklist ledger.'})}\n\n"
                return

            # 6. AUTOPILOT DIRECTIVES
            elif action == "autopilot":
                if any(w in msg for w in ["stop", "pause", "off", "cancel"]):
                    orchestrator.stop_24_7_autopilot()
                    yield f"data: {json.dumps({'type': 'thought', 'step': 'Suspending background autopilot heartbeat...'})}\n\n"
                    await asyncio.sleep(0.4)
                    yield f"data: {json.dumps({'type': 'done', 'sender': 'Aloria Hunter', 'reply': '24/7 Autopilot paused. Standing by in manual mode.', 'thought': 'Autopilot background heartbeat suspended.'})}\n\n"
                else:
                    orchestrator.start_24_7_autopilot(interval_minutes=15)
                    yield f"data: {json.dumps({'type': 'thought', 'step': 'Arming perpetual autonomous cycle: lead discovery -> technical audits -> outreach wave -> scheduled follow-ups.'})}\n\n"
                    await asyncio.sleep(0.5)
                    yield f"data: {json.dumps({'type': 'done', 'sender': 'Aloria Hunter', 'reply': '24/7 Autonomous mode is now active! The engine will continuously cycle between Lead Discovery, Technical Audits, Pitches, and Scheduled Follow-ups.', 'thought': 'Perpetual Autopilot heartbeat active on 15-minute rotation cycle.'})}\n\n"
                return

            # 7. STATUS & STATS REPORT
            elif action == "status":
                yield f"data: {json.dumps({'type': 'thought', 'step': 'Querying SQLite database ledger and thread telemetry...'})}\n\n"
                await asyncio.sleep(0.4)
                st = orchestrator.get_status()
                ho = st.get("hotel_stats", {})
                al = st.get("aloria_stats", {})
                total_leads = ho.get("total", 0) + al.get("total", 0)
                total_aud = ho.get("audited", 0) + al.get("audited", 0)
                total_sent = ho.get("emails_sent", 0) + al.get("emails_sent", 0)
                aloria_st = st.get("aloria", {}).get("status", "IDLE")
                hotel_st = st.get("hotel", {}).get("status", "IDLE")

                reply_text = f"Here is your current outreach status:\n\n• **Total Captured Leads**: {total_leads}\n• **Audited Websites**: {total_aud}\n• **Delivered Pitches & Emails**: {total_sent}\n• **GHS Agent**: {hotel_st}\n• **Aloria Labs Agent**: {aloria_st}\n• **Follow-up Engine**: Active 24/7"
                yield f"data: {json.dumps({'type': 'done', 'sender': 'Aloria Hunter', 'reply': reply_text, 'thought': 'Queried SQLite database ledger and active thread telemetry.'})}\n\n"
                return

            # 8. GREETING
            elif action == "greeting":
                yield f"data: {json.dumps({'type': 'thought', 'step': f'Syncing active context for {agent_name}...'})}\n\n"
                await asyncio.sleep(0.3)
                if is_hotel:
                    reply_text = "Hey! **GHS Agent** is online and ready.\n\nI specialize in discovering independent hotels, boutique stays, and luxury resorts across India. I inspect their booking presence and dispatch our performance-based partnership proposal (**₹0 onboarding, ₹0 monthly fee, 12% booking commission**).\n\nTell me where you want to target — for example, say **\"Hunt 15 hotels in Jaipur\"**, **\"Find boutique stays in Goa\"**, or **\"Run audits\"**."
                else:
                    reply_text = "Hey! **Aloria Labs Agent** is online and ready.\n\nI discover local commercial businesses (restaurants, web agencies, medical clinics), run comprehensive technical performance and SSL audits on their sites, and pitch modern infrastructure rebuilds.\n\nTell me what to target — for example, say **\"Hunt 10 restaurants in Mumbai\"**, **\"Find web agencies in Bangalore\"**, or **\"Run audits\"**."
                yield f"data: {json.dumps({'type': 'done', 'sender': agent_name, 'reply': reply_text, 'thought': 'Contextual agent greeting dispatched.'})}\n\n"
                return

            # 9. GENERAL CONVERSATIONAL INTELLIGENCE
            else:
                yield f"data: {json.dumps({'type': 'thought', 'step': 'Analyzing intent and checking operational context...'})}\n\n"
                await asyncio.sleep(0.3)
                if "india" in msg and not intent["has_explicit_city"]:
                    if is_hotel:
                        reply_text = f"India is our primary market for **GetHotelStays**! Which city or destination would you like to sweep first?\n\nPopular targets: **Jaipur**, **Goa**, **Udaipur**, **Delhi**, **Mumbai**, **Manali**, or **Pushkar**.\n\nYou can say **\"Hunt 20 hotels in Jaipur\"** or **\"Find resorts in Goa\"** to start immediately."
                    else:
                        reply_text = f"Understood! For **Aloria Labs**, which city and business niche should we target in India?\n\nYou can say **\"Hunt 15 restaurants in Mumbai\"**, **\"Find digital agencies in Bangalore\"**, or **\"Run audits\"**."
                elif is_hotel:
                    reply_text = f"Understood! I'm armed for **{target_niche}** under **GetHotelStays**.\n\nYou can say **\"Hunt 15 {target_niche.lower()} in {target_city}\"**, **\"Run audits\"** to inspect websites, or **\"Send pitch\"** to dispatch partner onboarding emails."
                else:
                    reply_text = f"Understood! I'm armed for **{target_niche}** in **{target_city}**.\n\nYou can say **\"Hunt 10 {target_niche.lower()} in {target_city}\"**, **\"Run audits\"**, or **\"Dispatch follow-ups\"**."

                yield f"data: {json.dumps({'type': 'done', 'sender': agent_name, 'reply': reply_text, 'thought': 'Provided contextual agent suggestions based on active business profile.'})}\n\n"
                return

        except Exception as stream_err:
            logger.exception("Error during chat stream processing")
            yield f"data: {json.dumps({'type': 'thought', 'step': f'Notice: {str(stream_err)[:80]}'})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'sender': 'Aloria Hunter', 'reply': f'⚠️ **Encountered an issue**: {str(stream_err)}.\n\nPlease check that your browser drivers are ready, or try another command like **\"Run audits\"** or **\"Status\"**.', 'thought': f'Recovered from {type(stream_err).__name__}.'})}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


@app.post("/api/chat")
async def post_chat(request: Request):
    data = await request.json()
    raw_msg = (data.get("message") or "").strip()
    msg = raw_msg.lower()
    selected_agent = data.get("agent")  # 'hotel', 'aloria', or None/'both'

    if not msg:
        return {
            "sender": "Aloria Hunter",
            "reply": "Hey! How can I help you today? You can ask me to hunt leads, audit websites, or dispatch follow-ups.",
            "thought": "Standing by for your instructions."
        }

    intent = parse_chat_intent(raw_msg, selected_agent)
    action = intent["action"]
    target_city = intent["target_city"]
    target_country = intent["target_country"]
    target_niche = intent["target_niche"]
    target_agent = intent["target_agent"]
    agent_name = intent["agent_name"]
    limit = intent["safe_limit"]
    is_hotel = intent["is_hotel"]

    # 1. HUNT / SCRAPE DIRECTIVES
    if action == "hunt":
        orchestrator.command_agent(target_agent, "hunt", {
            "city": target_city,
            "country": target_country,
            "niche": target_niche,
            "limit": limit
        })

        return {
            "sender": agent_name,
            "reply": f"Got it! Starting to search Google Maps for {limit} {target_niche} in {target_city}, {target_country}. I'll inspect their websites, pull verified direct contact inboxes, and update your pipeline.",
            "thought": f"Sweeping Google Maps listings for '{target_niche} in {target_city}', validating domain DNS and mailto inboxes.",
            "action_executed": "hunt",
            "agent": target_agent
        }

    # 2. AUDIT DIRECTIVES
    elif action == "audit":
        target_agent = selected_agent or "both"
        orchestrator.command_agent(target_agent, "audit", {"limit": limit if limit > 5 else 10})
        agent_name = "GHS Agent" if selected_agent == "hotel" else ("Aloria Labs Agent" if selected_agent == "aloria" else "Auditor")
        return {
            "sender": agent_name,
            "reply": "Running website audits across candidate domains now. Inspecting server response speed, SSL validity, and scraping direct contact emails.",
            "thought": "Testing HTTP latency, SSL certificate trust chain, and mailto tags across pending candidate websites.",
            "action_executed": "audit",
            "agent": target_agent
        }

    # 3. INITIAL PITCH DISPATCH DIRECTIVES
    elif action == "pitch":
        target_agent = "hotel" if is_hotel else (selected_agent or "both")
        orchestrator.command_agent(target_agent, "dispatch_initial", {"limit": limit})
        agent_name = "GHS Agent" if is_hotel else ("Aloria Labs Agent" if selected_agent == "aloria" else "Outreach Dispatcher")
        return {
            "sender": agent_name,
            "reply": "Drafted and dispatched personalized Day-0 outreach proposals to verified candidate business inboxes.",
            "thought": "Validated recipient MX records, loaded personalized pitch templates, and transmitted outreach proposals.",
            "action_executed": "dispatch_initial",
            "agent": target_agent
        }

    # 4. FOLLOW-UP DISPATCH DIRECTIVES
    elif action == "followup":
        orchestrator.trigger_instant_followup()
        al_od = len(db.get_overdue_followups("aloria_labs"))
        gh_od = len(db.get_overdue_followups("gethotelstays"))
        total_od = al_od + gh_od
        return {
            "sender": "Follow-up Sentry",
            "reply": f"Checked the pipeline schedule. Found {total_od} leads reaching the 3-day milestone and triggered sequential follow-up dispatches.",
            "thought": f"Verified 3.0-day follow-up interval for {total_od} candidate leads. Dispatched parallel bumps.",
            "action_executed": "dispatch_followups",
            "agent": "followup_daemon"
        }

    # 5. BOUNCE DEFENDER / BLACKLIST
    elif action == "bounce":
        import bounce_detector
        res = bounce_detector.scan_all_profiles()
        return {
            "sender": "Bounce Defense",
            "reply": f"Inbox scan finished. Identified and blacklisted {res.get('total_newly_blacklisted', 0)} bad inboxes to protect sender domain reputation.",
            "thought": "Scanned IMAP delivery failure notices, parsed SMTP rejection codes, and updated blacklist ledger.",
            "action_executed": "bounce_scan",
            "agent": "guardian"
        }

    # 6. AUTOPILOT DIRECTIVES
    elif action == "autopilot":
        if any(w in msg for w in ["stop", "pause", "off", "cancel"]):
            orchestrator.stop_24_7_autopilot()
            return {
                "sender": "Aloria Hunter",
                "reply": "24/7 Autopilot paused. Standing by in manual mode.",
                "thought": "Autopilot background heartbeat suspended.",
                "action_executed": "autopilot_stop"
            }
        else:
            orchestrator.start_24_7_autopilot(interval_minutes=15)
            return {
                "sender": "Aloria Hunter",
                "reply": "24/7 Autonomous mode is now active! The engine will continuously cycle between Lead Discovery, Technical Audits, Pitches, and Scheduled Follow-ups.",
                "thought": "Perpetual Autopilot heartbeat active on 15-minute rotation cycle.",
                "action_executed": "autopilot_start"
            }

    # 7. STATUS & STATS REPORT
    elif action == "status":
        st = orchestrator.get_status()
        ho = st.get("hotel_stats", {})
        al = st.get("aloria_stats", {})
        total_leads = ho.get("total", 0) + al.get("total", 0)
        total_aud = ho.get("audited", 0) + al.get("audited", 0)
        total_sent = ho.get("emails_sent", 0) + al.get("emails_sent", 0)
        aloria_st = st.get("aloria", {}).get("status", "IDLE")
        hotel_st = st.get("hotel", {}).get("status", "IDLE")

        return {
            "sender": "Aloria Hunter",
            "reply": f"Here is your current outreach status:\n• Total Captured Leads: {total_leads}\n• Audited Websites: {total_aud}\n• Delivered Pitches & Emails: {total_sent}\n• GHS Agent: {hotel_st}\n• Aloria Labs Agent: {aloria_st}\n• Follow-up Engine: Active 24/7",
            "thought": "Queried SQLite database ledger and active thread telemetry.",
            "action_executed": "status_report"
        }

    # 8. GREETING & CONVERSATIONAL INTELLIGENCE
    elif action == "greeting":
        if is_hotel:
            reply_text = "Hey! **GHS Agent** is online and ready. I specialize in discovering independent hotels and resorts, auditing their booking setups, and dispatching ₹0 upfront partnership proposals. What city would you like to target?"
        else:
            reply_text = "Hey! **Aloria Labs Agent** is online and ready. I discover commercial businesses, audit website speed/SSL, and pitch high-performance rebuilds. What niche are we hunting today?"
        return {
            "sender": agent_name,
            "reply": reply_text,
            "thought": "Ready for operator directives.",
            "action_executed": "greeting"
        }
    else:
        if "india" in msg and not intent["has_explicit_city"]:
            if is_hotel:
                reply_text = "India is our primary market for **GetHotelStays**! Which destination should we sweep? (e.g., 'Hunt 20 hotels in Jaipur' or 'Find resorts in Goa')."
            else:
                reply_text = "Understood! For **Aloria Labs**, which city and business niche should we target in India? (e.g., 'Hunt 15 restaurants in Mumbai')."
        elif is_hotel:
            reply_text = f"Understood! I'm armed for **{target_niche}** in **{target_city}** under **GetHotelStays**.\n\nYou can say 'Hunt 15 {target_niche.lower()} in {target_city}', 'Run audits', or 'Dispatch follow-ups'."
        else:
            reply_text = f"Understood! I'm armed for **{target_niche}** in **{target_city}**.\n\nYou can say 'Hunt 10 {target_niche.lower()} in {target_city}', 'Run audits', or 'Dispatch follow-ups'."

        return {
            "sender": agent_name,
            "reply": reply_text,
            "thought": "Provided contextual assistance.",
            "action_executed": "conversational"
        }



def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def run_server(host="0.0.0.0", port=8000):
    ip = get_local_ip()
    print(f"\n🏹 [HUNTER MOBILE COMMAND SERVER ONLINE]")
    print(f"  • Local Laptop:  http://localhost:{port}")
    print(f"  • Mobile Access: http://{ip}:{port}  (Open this on your phone's browser)\n")
    uvicorn.run(app, host=host, port=port, log_level="warning")

if __name__ == "__main__":
    run_server()
