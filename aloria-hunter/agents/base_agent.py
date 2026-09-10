import threading
import time
from datetime import datetime
from queue import Queue

class BaseAgent(threading.Thread):
    def __init__(self, agent_id, name, business_id):
        super().__init__(daemon=True)
        self.agent_id = agent_id
        self.name = name
        self.business_id = business_id
        self.status = "IDLE"  # IDLE, HUNTING, AUDITING, DISPATCHING, SLEEPING, PAUSED
        self.is_running = False
        self.is_paused = False
        self.command_queue = Queue()
        self.recent_events = []
        self.current_task = "Standby"
        self.cycle_count = 0

    def log_event(self, message, level="INFO"):
        now_str = datetime.now().strftime("%H:%M:%S")
        event = {
            "time": now_str,
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "level": level,
            "message": message
        }
        self.recent_events.append(event)
        if len(self.recent_events) > 50:
            self.recent_events.pop(0)
        return event

    def send_command(self, cmd_dict):
        self.command_queue.put(cmd_dict)

    def pause(self):
        self.is_paused = True
        self.status = "PAUSED"
        self.log_event(f"{self.name} paused by operator.", "WARN")

    def resume(self):
        self.is_paused = False
        self.status = "IDLE"
        self.log_event(f"{self.name} resumed operations.", "INFO")

    def stop(self):
        self.is_running = False
        self.status = "STOPPED"
        self.log_event(f"{self.name} stopped.", "WARN")

    def get_state(self):
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "business_id": self.business_id,
            "status": self.status,
            "current_task": self.current_task,
            "cycle_count": self.cycle_count,
            "is_paused": self.is_paused,
            "recent_events": self.recent_events[-10:]
        }
