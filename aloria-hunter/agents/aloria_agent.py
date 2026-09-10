import time
from agents.base_agent import BaseAgent
import maps_crawler
import website_auditor
import email_engine
import business_manager
import db

class AloriaAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="agent_aloria",
            name="Agent Aloria (Web & Tech)",
            business_id="aloria_labs"
        )
        self.cooldown_seconds = 180  # Cooldown between background waves

    def run(self):
        self.is_running = True
        self.log_event("Agent Aloria initialized and online.", "INFO")

        while self.is_running:
            # 1. Process immediate manual commands from queue (if any)
            while not self.command_queue.empty():
                cmd = self.command_queue.get()
                self._handle_command(cmd)

            if self.is_paused:
                time.sleep(2)
                continue

            # 2. Standby / wait for trigger or continuous cycle
            time.sleep(2)

    def _handle_command(self, cmd):
        action = cmd.get("action")
        params = cmd.get("params", {})

        if action == "hunt":
            self.execute_hunt_wave(
                city=params.get("city", "Algiers"),
                country=params.get("country", "Algeria"),
                niche=params.get("niche", "Restaurants"),
                limit=params.get("limit", 5),
                headless=params.get("headless", True)
            )
        elif action == "audit":
            self.execute_audit(limit=params.get("limit", 10))
        elif action == "dispatch_initial":
            self.execute_dispatch(limit=params.get("limit", 5))
        elif action == "dispatch_followups":
            self.execute_followups()
        elif action == "full_wave":
            self.execute_full_wave(
                city=params.get("city", "Algiers"),
                country=params.get("country", "Algeria"),
                niche=params.get("niche", "Restaurants"),
                limit=params.get("limit", 5)
            )
        elif action == "pause":
            self.pause()
        elif action == "resume":
            self.resume()

    def execute_hunt_wave(self, city="Algiers", country="Algeria", niche="Restaurants", limit=5, headless=True):
        self.status = "HUNTING"
        self.current_task = f"Scraping {niche} in {city}, {country}"
        self.log_event(f"Starting Maps lead discovery for {niche} in {city}...", "INFO")

        try:
            discovered = maps_crawler.crawl_google_maps(
                city=city,
                country=country,
                niche=niche,
                max_places=limit,
                headless=headless,
                business_id=self.business_id
            )
            self.log_event(f"Discovery wave finished: {len(discovered)} leads captured.", "SUCCESS")
        except Exception as e:
            self.log_event(f"Maps crawl error: {e}", "ERROR")

        self.status = "IDLE"
        self.current_task = "Standby"

    def execute_audit(self, limit=10):
        self.status = "AUDITING"
        self.current_task = f"Auditing pending candidate websites"
        self.log_event("Starting website audit & email extraction...", "INFO")

        try:
            audited = website_auditor.audit_pending_leads(limit=limit, business_id=self.business_id)
            self.log_event(f"Audit completed: {len(audited)} sites audited.", "SUCCESS")
        except Exception as e:
            self.log_event(f"Audit error: {e}", "ERROR")

        self.status = "IDLE"
        self.current_task = "Standby"

    def execute_dispatch(self, limit=5):
        self.status = "DISPATCHING"
        self.current_task = "Dispatching initial web modernization pitches"
        self.log_event("Dispatching tailored Day 0 cold pitches...", "INFO")

        try:
            sent = email_engine.dispatch_initial_emails(limit=limit, business_id=self.business_id)
            self.log_event(f"Dispatch complete: {sent} emails successfully sent.", "SUCCESS")
        except Exception as e:
            self.log_event(f"Dispatch error: {e}", "ERROR")

        self.status = "IDLE"
        self.current_task = "Standby"

    def execute_followups(self):
        self.status = "DISPATCHING"
        self.current_task = "Dispatching scheduled 2-Day / 4-Day follow-ups"
        self.log_event("Checking scheduled follow-up queue...", "INFO")

        try:
            sent = email_engine.dispatch_followups(business_id=self.business_id)
            self.log_event(f"Follow-ups dispatched: {sent} reminders sent.", "SUCCESS")
        except Exception as e:
            self.log_event(f"Follow-up error: {e}", "ERROR")

        self.status = "IDLE"
        self.current_task = "Standby"

    def execute_full_wave(self, city="Algiers", country="Algeria", niche="Restaurants", limit=5):
        self.cycle_count += 1
        self.log_event(f"Starting Full Autonomous Wave #{self.cycle_count} for Aloria Labs...", "INFO")
        self.execute_hunt_wave(city=city, country=country, niche=niche, limit=limit, headless=True)
        self.execute_audit(limit=limit)
        self.execute_dispatch(limit=limit)
        self.execute_followups()
        self.log_event(f"Wave #{self.cycle_count} fully completed.", "SUCCESS")
