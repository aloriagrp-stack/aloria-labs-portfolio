import threading
import time
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

    def start(self):
        if not self.is_running:
            self.aloria_agent.start()
            self.hotel_agent.start()
            self.is_running = True

    def get_status(self):
        return {
            "aloria": self.aloria_agent.get_state(),
            "hotel": self.hotel_agent.get_state(),
            "autopilot_active": self.autopilot_active
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
