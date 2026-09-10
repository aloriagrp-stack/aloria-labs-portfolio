import os
import sys
import json
import socket
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

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
def get_mobile_ui():
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

@app.get("/api/status")
def get_status():
    status = orchestrator.get_status()
    status["aloria_stats"] = db.get_funnel_stats("aloria_labs")
    status["hotel_stats"] = db.get_funnel_stats("gethotelstays")
    return status

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
    return db.get_lead_ledger(business_id=business_id, limit=30)

@app.post("/api/chat")
async def post_chat(request: Request):
    data = await request.json()
    msg = (data.get("message") or "").strip().lower()

    if not msg:
        return {"sender": "SYSTEM", "reply": "Empty command received."}

    if "hotel" in msg or "stays" in msg:
        if "hunt" in msg or "scrape" in msg or "find" in msg:
            orchestrator.command_agent("hotel", "hunt", {"niche": "Hotels", "city": "Algiers", "limit": 5})
            return {"sender": "Agent HotelStays", "reply": "Understood! Hunting independent hotels in Algiers right now."}
        elif "send" in msg or "dispatch" in msg or "email" in msg:
            orchestrator.command_agent("hotel", "dispatch_initial", {"limit": 5})
            return {"sender": "Agent HotelStays", "reply": "Dispatching GetHotelStays onboarding pitches to hotel managers."}
        else:
            state = orchestrator.hotel_agent.get_state()
            return {"sender": "Agent HotelStays", "reply": f"I am currently {state['status']}. Task: {state['current_task']}."}

    elif "aloria" in msg or "web" in msg or "restaurant" in msg:
        if "hunt" in msg or "scrape" in msg or "find" in msg:
            orchestrator.command_agent("aloria", "hunt", {"niche": "Restaurants", "city": "Algiers", "limit": 5})
            return {"sender": "Agent Aloria", "reply": "Understood! Hunting restaurants & cafes in Algiers for web audits."}
        elif "send" in msg or "dispatch" in msg or "email" in msg:
            orchestrator.command_agent("aloria", "dispatch_initial", {"limit": 5})
            return {"sender": "Agent Aloria", "reply": "Dispatching web modernization pitches to business owners."}
        else:
            state = orchestrator.aloria_agent.get_state()
            return {"sender": "Agent Aloria", "reply": f"I am currently {state['status']}. Task: {state['current_task']}."}

    elif "follow" in msg:
        orchestrator.command_agent("both", "dispatch_followups", {})
        return {"sender": "COORDINATOR", "reply": "Checking and dispatching scheduled Day 2/Day 4 follow-ups for both businesses."}

    elif "audit" in msg:
        orchestrator.command_agent("both", "audit", {})
        return {"sender": "COORDINATOR", "reply": "Triggered website speed and SSL audits on all pending candidate leads."}

    elif "pause" in msg or "stop" in msg:
        orchestrator.command_agent("both", "pause", {})
        orchestrator.stop_24_7_autopilot()
        return {"sender": "COORDINATOR", "reply": "Both agents and 24/7 autopilot have been PAUSED."}

    elif "resume" in msg or "start" in msg:
        orchestrator.command_agent("both", "resume", {})
        return {"sender": "COORDINATOR", "reply": "Both agents are RESUMED and standing by for orders."}

    elif "autopilot" in msg or "24/7" in msg:
        res = orchestrator.start_24_7_autopilot(interval_minutes=15)
        return {"sender": "COORDINATOR", "reply": "24/7 Continuous Dual Autopilot is now ACTIVE! Rotating between Aloria Labs and GetHotelStays."}

    elif "status" in msg or "report" in msg:
        s = orchestrator.get_status()
        al_stat = s['aloria']['status']
        ho_stat = s['hotel']['status']
        return {
            "sender": "COORDINATOR",
            "reply": f"Status Report: Agent Aloria is [{al_stat}]. Agent HotelStays is [{ho_stat}]. Autopilot is [{'ON' if s['autopilot_active'] else 'STANDBY'}]."
        }

    else:
        return {
            "sender": "COORDINATOR",
            "reply": "Command recognized. You can type: 'Hunt hotels', 'Hunt web leads', 'Run audits', 'Send emails', 'Dispatch follow-ups', or 'Status'."
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
