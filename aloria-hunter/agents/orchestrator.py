import threading
import time
from datetime import datetime
from agents.aloria_agent import AloriaAgent
from agents.hotel_agent import HotelStaysAgent


class AgentOrchestrator:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = AgentOrchestrator()
        return cls._instance

    def __init__(self):
        self.aloria_agent = AloriaAgent()
        self.hotel_agent = HotelStaysAgent()
        self.agents = {
            "aloria": self.aloria_agent,
            "hotel": self.hotel_agent
        }
        self.is_running = False
        self.autopilot_thread = None
        self.autopilot_active = False
        self.followup_thread = None
        self.followup_running = False
        self.last_followup_check = None
        self.last_followup_sent = 0
        self.followup_events = []
        self.log_followup_event("Parallel Follow-up Daemon initialized and armed.", "SUCCESS")

    def log_followup_event(self, message, level="INFO"):
        now_str = datetime.now().strftime("%H:%M:%S")
        event = {
            "time": now_str,
            "agent_id": "followup_daemon",
            "agent_name": "Parallel Follow-up Engine",
            "level": level,
            "message": message
        }
        self.followup_events.append(event)
        if len(self.followup_events) > 50:
            self.followup_events.pop(0)
        return event

    def start(self):
        if not self.is_running:
            self.aloria_agent.start()
            self.hotel_agent.start()
            self.start_parallel_followup_worker(interval_seconds=60)
            self.is_running = True

    def start_parallel_followup_worker(self, interval_seconds=60):
        if self.followup_running:
            return
        self.followup_running = True

        def _worker_loop():
            import email_engine
            import db
            import config
            while self.followup_running:
                try:
                    self.last_followup_check = time.time()
                    # Check for ready followups
                    overdue = db.get_leads_ready_for_followup(interval_days=getattr(config, "FOLLOW_UP_INTERVAL_DAYS", 3)) if hasattr(db, "get_leads_ready_for_followup") else []
                    if overdue:
                        self.log_followup_event(f"Detected {len(overdue)} overdue leads. Dispatching parallel outreach wave...", "INFO")
                        sent_al = email_engine.dispatch_followups(business_id="aloria_labs")
                        sent_gh = email_engine.dispatch_followups(business_id="gethotelstays")
                        total_sent = sent_al + sent_gh
                        self.last_followup_sent = total_sent
                        self.log_followup_event(f"Parallel wave complete: Delivered {total_sent} follow-up emails.", "SUCCESS")
                    else:
                        self.log_followup_event("Routine scan: 0 leads overdue at this checkpoint.", "INFO")
                except Exception as e:
                    self.log_followup_event(f"Parallel engine error: {e}", "ERROR")

                for _ in range(interval_seconds):
                    if not self.followup_running:
                        break
                    time.sleep(1)

        self.followup_thread = threading.Thread(target=_worker_loop, daemon=True, name="ParallelFollowupWorker")
        self.followup_thread.start()

    def trigger_instant_followup(self):
        def _instant_worker():
            import email_engine
            try:
                self.log_followup_event("Manual instant follow-up wave triggered by operator.", "INFO")
                sent_al = email_engine.dispatch_followups(business_id="aloria_labs")
                sent_gh = email_engine.dispatch_followups(business_id="gethotelstays")
                self.last_followup_sent = sent_al + sent_gh
                self.log_followup_event(f"Instant wave complete: {sent_al + sent_gh} emails sent.", "SUCCESS")
            except Exception as e:
                self.log_followup_event(f"Instant follow-up error: {e}", "ERROR")

        t = threading.Thread(target=_instant_worker, daemon=True)
        t.start()
        return {"status": "dispatched_parallel"}

    def get_status(self):
        return {
            "aloria": self.aloria_agent.get_state(),
            "hotel": self.hotel_agent.get_state(),
            "autopilot_active": self.autopilot_active,
            "parallel_followup_running": self.followup_running,
            "last_followup_check": self.last_followup_check,
            "last_followup_sent": self.last_followup_sent,
            "followup_events": self.followup_events[-20:]
        }


    def command_agent(self, agent_target, action, params=None):
        params = params or {}
        cmd = {"action": action, "params": params}

        if agent_target in ["aloria", "agent_aloria"]:
            self.aloria_agent.send_command(cmd)
            return {"target": "aloria", "action": action, "status": "queued"}
        elif agent_target in ["hotel", "agent_hotelstays", "hotelstays"]:
            self.hotel_agent.send_command(cmd)
            return {"target": "hotel", "action": action, "status": "queued"}
        elif agent_target in ["both", "all"]:
            self.aloria_agent.send_command(cmd)
            self.hotel_agent.send_command(cmd)
            return {"target": "both", "action": action, "status": "queued"}
        else:
            return {"error": f"Unknown agent target: {agent_target}"}

    def start_24_7_autopilot(self, interval_minutes=15):
        if self.autopilot_active:
            return {"status": "already_active"}

        self.autopilot_active = True

        def _loop():
            while self.autopilot_active:
                # Wave 1: Aloria Agent
                self.aloria_agent.send_command({"action": "full_wave", "params": {"limit": 5}})
                # Cooldown 5 mins to protect IP/rate limits
                time.sleep(300)

                # Wave 2: HotelStays Agent
                self.hotel_agent.send_command({"action": "full_wave", "params": {"limit": 5}})
                # Sleep interval
                time.sleep(interval_minutes * 60)

        self.autopilot_thread = threading.Thread(target=_loop, daemon=True)
        self.autopilot_thread.start()
        return {"status": "autopilot_started", "interval_minutes": interval_minutes}

    def stop_24_7_autopilot(self):
        self.autopilot_active = False
        return {"status": "autopilot_stopped"}

orchestrator = AgentOrchestrator.get_instance()

