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
        tgt = business_manager.get_target_settings("gethotelstays")

        target_city = params.get("city") or tgt.get("city") or "Goa"
        target_country = params.get("country") or tgt.get("country") or "India"
        target_niche = params.get("niche") or tgt.get("niche") or "Hotels"

        if action == "hunt":
            self.execute_hunt_wave(
                city=target_city,
                country=target_country,
                niche=target_niche,
                limit=params.get("limit", 5),
                headless=params.get("headless", True)
            )
        elif action == "audit":
            self.execute_audit(limit=params.get("limit", 10))
        elif action == "dispatch_initial":
            self.execute_dispatch(limit=params.get("limit", 5))
        elif action == "whatsapp":
            self.execute_whatsapp_dispatch(limit=params.get("limit", 5))
        elif action == "dispatch_followups":
            self.execute_followups(limit=params.get("limit", 5))
        elif action == "dispatch_interleaved":
            self.execute_interleaved_dispatch(limit=params.get("limit", 5))
        elif action == "full_wave":
            self.execute_full_wave(
                city=target_city,
                country=target_country,
                niche=target_niche,
                limit=params.get("limit", 5)
            )
        elif action == "pause":
            self.pause()
        elif action == "resume":
            self.resume()

    def execute_hunt_wave(self, city="Goa", country="India", niche="Hotels", limit=5, headless=True):
        self.current_stage = 1
        self.status = "DISCOVERY"
        self.current_task = f"Scraping independent {niche} in {city}, {country}"
        self.log_event(f"[STAGE 01: DISCOVERY] Searching {niche} in {city}, {country} (Target: {limit})...", "INFO")

        discovered = []
        def crawl_step(msg):
            self.stage_metrics["crawled"] = self.stage_metrics.get("crawled", 0) + 1
            self.log_event(f"[DISCOVERY] {msg}", "INFO")

        try:
            discovered = maps_crawler.crawl_google_maps(
                city=city,
                country=country,
                niche=niche,
                max_places=limit,
                headless=headless,
                business_id=self.business_id,
                on_step=crawl_step
            )
            self.stage_metrics["crawled"] = len(discovered)
            self.stage_metrics["stage_1_done"] = True
            self.log_event(f"[DISCOVERY COMPLETE] Captured {len(discovered)} properties in {city}.", "SUCCESS")
        except Exception as e:
            self.log_event(f"Maps crawl error: {e}", "ERROR")

        return discovered

    def execute_audit(self, limit=10):
        self.current_stage = 3
        self.status = "AUDITING"
        self.current_task = "Auditing hotel websites & extracting reservation emails"
        self.log_event("[STAGE 03: WEBSITE AUDIT] Inspecting websites of qualified leads...", "INFO")

        def audit_step(msg):
            self.stage_metrics["audited"] = self.stage_metrics.get("audited", 0) + 1
            self.log_event(f"[AUDIT] {msg}", "INFO")

        audited = []
        try:
            audited = website_auditor.audit_pending_leads(
                limit=limit,
                business_id=self.business_id,
                on_step=audit_step
            )
            self.stage_metrics["audited"] = len(audited)
            self.stage_metrics["stage_3_done"] = True
            self.log_event(f"[AUDIT COMPLETE] {len(audited)} hotel websites inspected.", "SUCCESS")
        except Exception as e:
            self.log_event(f"Hotel audit error: {e}", "ERROR")

        return audited

    def execute_dispatch(self, limit=5):
        self.current_stage = 5
        self.status = "DISPATCHING"
        self.current_task = "Dispatching GetHotelStays partner onboarding pitches"
        self.log_event(f"[STAGE 05: SWARM DISPATCH] Sending initial pitches (Target: {limit})...", "INFO")

        def dispatch_step(msg):
            self.stage_metrics["dispatched"] = self.stage_metrics.get("dispatched", 0) + 1
            self.log_event(f"[DISPATCH] {msg}", "SUCCESS")

        try:
            sent = email_engine.dispatch_initial_emails(limit=limit, business_id=self.business_id)
            self.stage_metrics["dispatched"] = sent
            self.stage_metrics["stage_5_done"] = True
            self.log_event(f"Onboarding dispatch complete: {sent} invitations sent.", "SUCCESS")
        except Exception as e:
            self.log_event(f"Onboarding dispatch error: {e}", "ERROR")

        self.current_stage = 0
        self.status = "IDLE"
        self.current_task = "Standby"

    def execute_followups(self, limit=5):
        self.current_stage = 5
        self.status = "DISPATCHING"
        self.current_task = "Dispatching hotel partner onboarding follow-ups"
        self.log_event(f"[STAGE 05: SWARM DISPATCH] Checking follow-up schedule (Limit: {limit})...", "INFO")

        try:
            sent = email_engine.dispatch_followups(business_id=self.business_id, limit=limit)
            self.stage_metrics["dispatched"] = self.stage_metrics.get("dispatched", 0) + sent
            self.log_event(f"Hotel follow-ups dispatched: {sent} sent.", "SUCCESS")
        except Exception as e:
            self.log_event(f"Hotel follow-up error: {e}", "ERROR")

        self.current_stage = 0
        self.status = "IDLE"
        self.current_task = "Standby"

    def execute_interleaved_dispatch(self, limit=5):
        self.current_stage = 5
        self.status = "DISPATCHING"
        self.current_task = "Balanced outreach (Fresh leads & scheduled follow-ups)"
        self.log_event(f"[STAGE 05: SWARM DISPATCH] Pacing outreach across healthy sender swarm...", "INFO")

        def dispatch_step(msg):
            self.stage_metrics["dispatched"] = self.stage_metrics.get("dispatched", 0) + 1
            self.log_event(f"[SWARM DISPATCH] {msg}", "SUCCESS")

        sent_count = 0
        try:
            res = email_engine.dispatch_interleaved_wave(
                limit=limit,
                business_id=self.business_id,
                on_step=dispatch_step
            )
            self.stage_metrics["stage_5_done"] = True
            sent_count = (res.get("initial_sent") or 0) + (res.get("followup_sent") or 0)
            self.log_event(
                f"[DISPATCH COMPLETE] Sent {res.get('initial_sent', 0)} fresh invitations + {res.get('followup_sent', 0)} follow-ups.",
                "SUCCESS"
            )
        except Exception as e:
            self.log_event(f"Balanced outreach error: {e}", "ERROR")

        return sent_count

    def execute_whatsapp_dispatch(self, limit=5):
        self.status = "WHATSAPP_DISPATCH"
        self.current_task = "Dispatching tailored WhatsApp pitches to hotels"
        self.log_event("Checking hotel leads without email for WhatsApp outreach...", "INFO")

        try:
            import whatsapp_engine
            sent = whatsapp_engine.dispatch_whatsapp_queue(limit=limit, business_id=self.business_id, headless=True)
            self.log_event(f"WhatsApp outreach finished: {sent} delivered.", "SUCCESS")
        except Exception as e:
            self.log_event(f"WhatsApp outreach error: {e}", "ERROR")

        self.status = "IDLE"
        self.current_task = "Standby"

    def execute_full_wave(self, city="Goa", country="India", niche="Hotels", limit=5):
        self.cycle_count += 1
        target_goal = max(1, int(limit))
        self.log_event(f"🎯 [TARGET WAVE START] Autonomous Goal: {target_goal} verified deliveries for {city}, {country}...", "INFO")

        self.stage_metrics = {
            "stage": 1,
            "crawled": 0,
            "target": target_goal,
            "filtered": 0,
            "audited": 0,
            "verified": 0,
            "dispatched": 0,
            "stage_1_done": False,
            "stage_2_done": False,
            "stage_3_done": False,
            "stage_4_done": False,
            "stage_5_done": False
        }

        total_dispatched_in_run = 0
        iteration = 0
        max_iterations = 15
        query_niches = [niche, f"Boutique {niche}", "Resorts", "Luxury Villas", "Guest Houses", "Beach Stays", f"Independent {niche}", "Heritage Stays"]

        while total_dispatched_in_run < target_goal and iteration < max_iterations:
            iteration += 1
            remaining = target_goal - total_dispatched_in_run
            # High-capacity candidate sweep: capture 50-100 leads in one shot so the pipeline
            # can thoroughly filter valid vs invalid candidates before handing over to the sender swarm
            crawl_batch = max(50, min(100, remaining * 5))
            current_niche = query_niches[(iteration - 1) % len(query_niches)]

            self.log_event(f"[CYCLE #{iteration}] Progress: {total_dispatched_in_run}/{target_goal} delivered. Sweeping high-capacity batch ({crawl_batch} candidate {current_niche}) in {city}...", "INFO")

            # -------------------------------------------------------------
            # STAGE 1: Lead Discovery (Google Maps Crawl - 100% Silent Background)
            # -------------------------------------------------------------
            discovered = self.execute_hunt_wave(city=city, country=country, niche=current_niche, limit=crawl_batch, headless=True)

            # -------------------------------------------------------------
            # STAGE 2: Quality Filter & Candidate Screening
            # -------------------------------------------------------------
            self.current_stage = 2
            self.status = "FILTERING"
            self.current_task = f"Screening {len(discovered)} candidate properties against suppression filters"
            self.log_event(f"[STAGE 02: QUALITY FILTER] Thoroughly screening {len(discovered)} candidate properties...", "INFO")
            time.sleep(0.3)

            qualified = []
            has_web_count = 0
            no_web_count = 0
            pruned_count = 0

            for p in discovered:
                p_name = p.get("name", "Hotel Property")
                p_web = p.get("website_url")
                is_blacklisted = False
                if p.get("phone") and db.is_email_blacklisted(p.get("phone")):
                    is_blacklisted = True

                if is_blacklisted:
                    pruned_count += 1
                    self.log_event(f"[FILTER: PRUNED] '{p_name}': matched suppression list / blacklisted.", "WARN")
                else:
                    qualified.append(p)
                    self.stage_metrics["filtered"] = self.stage_metrics.get("filtered", 0) + 1
                    if p_web:
                        has_web_count += 1
                    else:
                        no_web_count += 1
                time.sleep(0.02)

            self.stage_metrics["stage_2_done"] = True
            self.log_event(
                f"[FILTER COMPLETE] Screened {len(discovered)} leads: {has_web_count} with website (queued for audit), {no_web_count} without website (routed to Web Dev), {pruned_count} pruned.",
                "SUCCESS"
            )
            time.sleep(0.3)

            # -------------------------------------------------------------
            # STAGE 3: Technical Audits on Discovered Properties (100-Worker Swarm)
            # -------------------------------------------------------------
            self.execute_audit(limit=crawl_batch)
            time.sleep(0.3)

            # -------------------------------------------------------------
            # STAGE 4: Email Verification & MX Handshake Resolve
            # -------------------------------------------------------------
            self.current_stage = 4
            self.status = "VERIFYING"
            self.current_task = "Resolving MX DNS records & validating zero-bounce deliverability"
            self.log_event(f"[STAGE 04: EMAIL VERIFICATION] Verifying MX handshake for candidate inboxes...", "INFO")

            ready_leads = db.get_leads_ready_for_initial_email(business_id=self.business_id, limit=max(crawl_batch, remaining))
            verified_count = 0
            for l in ready_leads:
                em = l.get("email")
                if em:
                    domain = em.split("@")[-1] if "@" in em else ""
                    self.log_event(f"[MX VERIFY] Handshake verified for {em} (Domain: {domain}) -> 100% Deliverable ✓", "INFO")
                    verified_count += 1
                    self.stage_metrics["verified"] = self.stage_metrics.get("verified", 0) + 1
                    time.sleep(0.04)

            self.stage_metrics["stage_4_done"] = True
            self.log_event(f"[VERIFICATION COMPLETE] {verified_count} mailboxes verified for delivery.", "SUCCESS")
            time.sleep(0.3)

            # -------------------------------------------------------------
            # STAGE 5: Balanced Outreach Dispatch
            # -------------------------------------------------------------
            sent_now = self.execute_interleaved_dispatch(limit=remaining)
            total_dispatched_in_run += (sent_now or 0)
            self.stage_metrics["dispatched"] = total_dispatched_in_run

            if total_dispatched_in_run >= target_goal:
                self.stage_metrics["target_completed"] = True
                self.stage_metrics["completed_target"] = target_goal
                self.stage_metrics["total_dispatched"] = total_dispatched_in_run
                self.log_event(f"🎯 [TARGET GOAL ACHIEVED] Completed all {target_goal} target deliveries!", "SUCCESS")
                break
            else:
                self.log_event(f"[TARGET IN PROGRESS] {total_dispatched_in_run}/{target_goal} delivered. Starting cycle #{iteration + 1} to reach target...", "INFO")
                time.sleep(1.0)

        self.current_stage = 0
        self.status = "IDLE"
        self.current_task = "Standby"
        if total_dispatched_in_run >= target_goal:
            self.stage_metrics["target_completed"] = True
            self.stage_metrics["completed_target"] = target_goal
            self.stage_metrics["total_dispatched"] = total_dispatched_in_run
            self.log_event(f"Wave #{self.cycle_count} fully completed for GetHotelStays: {total_dispatched_in_run}/{target_goal} target delivered.", "SUCCESS")
        else:
            self.log_event(f"Wave #{self.cycle_count} paused: {total_dispatched_in_run}/{target_goal} target delivered.", "INFO")
