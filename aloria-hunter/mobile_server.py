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

# Allow CORS
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

@app.get("/api/status")
def get_status():
    status = orchestrator.get_status()
    # Add stats
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

    # Intent routing
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
