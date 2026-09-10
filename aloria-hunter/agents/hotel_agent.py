import time
from agents.base_agent import BaseAgent
import maps_crawler
import website_auditor
import email_engine
import business_manager
import db

class HotelStaysAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="agent_hotelstays",
            name="Agent HotelStays (Hospitality)",
            business_id="gethotelstays"
        )
        self.cooldown_seconds = 180

    def run(self):
        self.is_running = True
        self.log_event("Agent HotelStays initialized and online.", "INFO")

        while self.is_running:
            # 1. Process immediate manual commands from queue
            while not self.command_queue.empty():
                cmd = self.command_queue.get()
                self._handle_command(cmd)

            if self.is_paused:
                time.sleep(2)
                continue

            time.sleep(2)

    def _handle_command(self, cmd):
        action = cmd.get("action")
        params = cmd.get("params", {})

        if action == "hunt":
            self.execute_hunt_wave(
                city=params.get("city", "Algiers"),
                country=params.get("country", "Algeria"),
                niche=params.get("niche", "Hotels"),
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
                niche=params.get("niche", "Hotels"),
                limit=params.get("limit", 5)
            )
        elif action == "pause":
            self.pause()
        elif action == "resume":
            self.resume()

    def execute_hunt_wave(self, city="Algiers", country="Algeria", niche="Hotels", limit=5, headless=True):
        self.status = "HUNTING"
        self.current_task = f"Scraping independent {niche} in {city}, {country}"
        self.log_event(f"Searching independent hotels & boutique stays in {city}...", "INFO")

        try:
            discovered = maps_crawler.crawl_google_maps(
                city=city,
                country=country,
                niche=niche,
                max_places=limit,
                headless=headless,
                business_id=self.business_id
            )
            self.log_event(f"Hotel discovery wave finished: {len(discovered)} properties found.", "SUCCESS")
        except Exception as e:
            self.log_event(f"Maps crawl error: {e}", "ERROR")

        self.status = "IDLE"
        self.current_task = "Standby"

    def execute_audit(self, limit=10):
        self.status = "AUDITING"
        self.current_task = "Auditing hotel websites & extracting reservation emails"
        self.log_event("Auditing hotel booking portals & contact points...", "INFO")

        try:
            audited = website_auditor.audit_pending_leads(limit=limit, business_id=self.business_id)
            self.log_event(f"Hotel audits completed: {len(audited)} inspected.", "SUCCESS")
        except Exception as e:
            self.log_event(f"Hotel audit error: {e}", "ERROR")

        self.status = "IDLE"
        self.current_task = "Standby"

    def execute_dispatch(self, limit=5):
        self.status = "DISPATCHING"
        self.current_task = "Dispatching GetHotelStays partner onboarding pitches"
        self.log_event("Dispatching partner onboarding invitations to hotel management...", "INFO")

        try:
            sent = email_engine.dispatch_initial_emails(limit=limit, business_id=self.business_id)
            self.log_event(f"Onboarding dispatch complete: {sent} invitations sent.", "SUCCESS")
        except Exception as e:
            self.log_event(f"Onboarding dispatch error: {e}", "ERROR")

        self.status = "IDLE"
        self.current_task = "Standby"

    def execute_followups(self):
        self.status = "DISPATCHING"
        self.current_task = "Dispatching hotel partner onboarding follow-ups"
        self.log_event("Checking hotel partner follow-up schedule...", "INFO")

        try:
            sent = email_engine.dispatch_followups(business_id=self.business_id)
            self.log_event(f"Hotel follow-ups dispatched: {sent} sent.", "SUCCESS")
        except Exception as e:
            self.log_event(f"Hotel follow-up error: {e}", "ERROR")

        self.status = "IDLE"
        self.current_task = "Standby"

    def execute_full_wave(self, city="Algiers", country="Algeria", niche="Hotels", limit=5):
        self.cycle_count += 1
        self.log_event(f"Starting Full Autonomous Wave #{self.cycle_count} for GetHotelStays...", "INFO")
        self.execute_hunt_wave(city=city, country=country, niche=niche, limit=limit, headless=True)
        self.execute_audit(limit=limit)
        self.execute_dispatch(limit=limit)
        self.execute_followups()
        self.log_event(f"Wave #{self.cycle_count} fully completed for GetHotelStays.", "SUCCESS")
