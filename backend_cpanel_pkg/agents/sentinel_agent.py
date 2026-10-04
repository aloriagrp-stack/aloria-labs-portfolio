"""
Aloria Hunter - Sentinel Agent (Inbox & Reply Watcher)
Runs continuously in the background (every 5 minutes or on-demand).
Monitors outreach inboxes via IMAP for:
1. Delivery Bounces: Automatically blacklists dead inboxes and marks leads as BOUNCED.
2. Inbound Replies: Matches replies against contacted leads, marks them as REPLIED to prevent duplicate follow-ups, and raises instant operator alerts.
"""

import time
import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime
from typing import Any, List, Dict

from agents.base_agent import BaseAgent
import config
import db
import ui
import bounce_detector

def _decode_header_str(val: str | None) -> str:
    if not val:
        return ""
    try:
        dh = decode_header(val)
        parts = []
        for s, enc in dh:
            if isinstance(s, bytes):
                parts.append(s.decode(enc or "utf-8", errors="ignore"))
            else:
                parts.append(str(s))
        return "".join(parts).strip()
    except Exception:
        return str(val)

def _extract_email_address(raw_str: str) -> str:
    if not raw_str:
        return ""
    match = re.search(r'<([^>]+)>', raw_str)
    if match:
        return match.group(1).strip().lower()
    match = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', raw_str)
    if match:
        return match.group(1).strip().lower()
    return raw_str.strip().lower()

class HotelSentinelAgent(BaseAgent):
    def __init__(self, check_interval_seconds=300):
        super().__init__(
            agent_id="agent_sentinel",
            name="GetHotelStays Sentinel (Inbox & Deliverability Watcher)",
            business_id="gethotelstays"
        )
        self.check_interval = check_interval_seconds  # Continuous 5-minute (300s) cycle
        self.last_check_time = None
        self.total_bounces_found = 0
        self.total_replies_found = 0
        self.recent_replies: List[Dict[str, Any]] = []
        self.recent_bounces: List[Dict[str, Any]] = []
        self.log_event("GetHotelStays Sentinel Agent armed (5-min continuous all-inbox cycle).", "SUCCESS")

    def run(self):
        self.is_running = True
        self.log_event("Starting continuous inbox sentinel monitoring loop...", "INFO")

        # Initial immediate scan on startup
        time.sleep(2)
        try:
            self.execute_inbox_scan()
        except Exception as e:
            self.log_event(f"Initial inbox scan error: {e}", "ERROR")

        elapsed_since_last_check = 0
        while self.is_running:
            # 1. Process queue commands
            while not self.command_queue.empty():
                cmd = self.command_queue.get()
                self._handle_command(cmd)

            if self.is_paused:
                time.sleep(2)
                continue

            # 2. Check timer
            if elapsed_since_last_check >= self.check_interval:
                self.execute_inbox_scan()
                elapsed_since_last_check = 0

            time.sleep(1)
            elapsed_since_last_check += 1

    def _handle_command(self, cmd):
        action = cmd.get("action")
        params = cmd.get("params", {})

        if action in ["scan", "check", "check_now", "check_inbox"]:
            self.execute_inbox_scan()
        elif action == "set_interval":
            new_int = params.get("interval", 60)
            self.check_interval = max(15, int(new_int))
            self.log_event(f"Inbox scan interval updated to {self.check_interval}s.", "INFO")
        elif action == "pause":
            self.pause()
        elif action == "resume":
            self.resume()

    def execute_inbox_scan(self):
        self.status = "SCANNING_INBOX"
        self.current_task = "Connecting to IMAP and checking for bounces & replies..."
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.last_check_time = now_str
        self.cycle_count += 1

        self.log_event(f"Cycle #{self.cycle_count}: Checking inboxes for replies and bounces across all accounts...", "INFO")

        try:
            # Gather ALL profiles that have email & password configured (all 11 accounts)
            profiles_dict, _ = config.list_smtp_profiles()
            target_profiles = []
            for p_key, p_val in profiles_dict.items():
                if p_val and p_val.get("email") and p_val.get("password"):
                    target_profiles.append(p_key)

            if not target_profiles:
                target_profiles = ["gethotelstays"]

            new_replies_this_cycle = 0
            new_bounces_this_cycle = 0

            for p_key in target_profiles:
                b_count, r_count = self._scan_single_inbox(p_key)
                new_bounces_this_cycle += b_count
                new_replies_this_cycle += r_count

            summary_msg = f"Inbox audit complete across {len(target_profiles)} inboxes: {new_replies_this_cycle} new replies detected, {new_bounces_this_cycle} bounces blacklisted."
            if new_replies_this_cycle > 0:
                self.log_event(f"⭐ {summary_msg}", "SUCCESS")
            else:
                self.log_event(summary_msg, "INFO")

        except Exception as e:
            self.log_event(f"Inbox sentinel error: {e}", "ERROR")

        self.status = "MONITORING"
        self.current_task = f"Monitoring inboxes (Next scan in {self.check_interval}s)"

    def _scan_single_inbox(self, profile_name: str) -> tuple[int, int]:
        smtp_conf = config.get_smtp_config(profile_name)
        user_email = str(smtp_conf.get("email") or "")
        password = (smtp_conf.get("password") or "").replace(" ", "").strip()
        imap_server = "imap.gmail.com"
        imap_port = 993

        if not user_email or not password:
            return 0, 0

        bounces_count = 0
        replies_count = 0

        try:
            imap = imaplib.IMAP4_SSL(imap_server, imap_port, timeout=15)
            imap.login(user_email, password)
            imap.select("INBOX", readonly=True)

            # Fetch recent message IDs (last 30 messages in inbox)
            typ, data = imap.search(None, "ALL")
            if not data or not data[0]:
                imap.logout()
                return 0, 0

            all_ids = data[0].split()
            recent_ids = all_ids[-30:]

            for mid in recent_ids:
                try:
                    typ, mdata = imap.fetch(mid, '(BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE MESSAGE-ID IN-REPLY-TO)])')
                    if not mdata or not mdata[0] or not isinstance(mdata[0], tuple):
                        continue

                    header_raw = mdata[0][1].decode("utf-8", errors="ignore")
                    msg = email.message_from_string(header_raw)

                    from_raw = _decode_header_str(msg.get("From"))
                    from_email = _extract_email_address(from_raw)
                    subject = _decode_header_str(msg.get("Subject"))
                    date_str = msg.get("Date", "")

                    if not from_email:
                        continue

                    # 1. BOUNCE CHECK
                    if any(daemon in from_email for daemon in ["mailer-daemon", "postmaster"]):
                        # Full fetch to extract failed recipient
                        typ, full_mdata = imap.fetch(mid, '(RFC822)')
                        if full_mdata and full_mdata[0] and isinstance(full_mdata[0], tuple):
                            full_msg = email.message_from_bytes(full_mdata[0][1])
                            bounced_addrs, reason = bounce_detector.extract_bounced_addresses_from_msg(full_msg)
                            for b_addr in bounced_addrs:
                                was_added = db.add_to_blacklist(
                                    email=b_addr,
                                    reason=f"Sentinel Auto-Detect: {reason}",
                                    source=f"SENTINEL_{user_email}"
                                )
                                if was_added:
                                    bounces_count += 1
                                    self.total_bounces_found += 1
                                    self.recent_bounces.append({
                                        "email": b_addr,
                                        "reason": reason,
                                        "time": datetime.now().strftime("%H:%M:%S")
                                    })
                                    self.log_event(f"🛡️ BOUNCE CAUGHT: {b_addr} automatically blacklisted ({reason[:40]}).", "WARN")
                        continue

                    # Filter out system and marketing senders
                    ignored_senders = [
                        "google.com", "googlemail.com", "linkedin.com", "pinterest.com",
                        "quora.com", "medium.com", "youtube.com", "noreply", "no-reply"
                    ]
                    if any(ig in from_email for ig in ignored_senders):
                        continue

                    # 2. INCOMING LEAD REPLY CHECK
                    matched_lead = db.find_lead_by_email_or_domain(from_email, subject=subject)
                    if matched_lead:
                        lead_id = matched_lead["id"]
                        biz_name = matched_lead.get("business_name") or "Hotel Partner"
                        lead_email = matched_lead.get("email") or ""
                        curr_status = matched_lead.get("status")

                        if curr_status != "REPLIED":
                            import super_intelligence
                            intent_data = super_intelligence.classify_incoming_reply(subject, "", from_email)
                            intent = intent_data.get("intent", "GENERAL_INQUIRY")
                            extracted_phone = intent_data.get("extracted_phone")

                            # Newly identified reply! Mark lead and lock email & domain in replied_contacts
                            db.mark_lead_replied(lead_id=lead_id, email=lead_email, business_name=biz_name, source=f"SENTINEL_{user_email}")
                            
                            # If recipient replied from an alias or personal corporate email differing from lead_email, register that too
                            if from_email and from_email.lower() != lead_email.lower():
                                db.add_to_replied_contacts(email=from_email, business_name=biz_name, source=f"SENTINEL_ALIAS_{user_email}")

                            # Cognitive Intent Actions
                            if intent == super_intelligence.REPLY_INTENT_OPT_OUT:
                                db.add_to_blacklist(from_email, reason="Recipient requested opt-out", source=f"OPT_OUT_{user_email}")
                                self.log_event(f"🛑 RECIPIENT OPTED OUT: {from_email} permanently suppressed across all accounts.", "WARN")
                            elif extracted_phone:
                                conn = db.get_connection()
                                c = conn.cursor()
                                c.execute("UPDATE leads SET phone = ? WHERE id = ? AND (phone IS NULL OR phone = '')", (extracted_phone, lead_id))
                                conn.commit()
                                conn.close()
                                self.log_event(f"🔥 HOT LEAD PHONE CAPTURED: {extracted_phone} for {biz_name}!", "SUCCESS")

                            db.log_outreach_event(
                                lead_id=lead_id,
                                business_name=biz_name,
                                recipient_email=user_email,
                                sender_email=from_email,
                                pitch_type="INCOMING_REPLY",
                                subject=subject,
                                status="REPLIED",
                                business_id=matched_lead.get("business_id", "gethotelstays")
                            )
                            replies_count += 1
                            self.total_replies_found += 1
                            rep_info = {
                                "lead_id": lead_id,
                                "business_name": biz_name,
                                "from_email": from_email,
                                "subject": subject,
                                "intent": intent,
                                "extracted_phone": extracted_phone,
                                "date": date_str,
                                "time": datetime.now().strftime("%H:%M:%S")
                            }
                            self.recent_replies.append(rep_info)
                            if len(self.recent_replies) > 20:
                                self.recent_replies.pop(0)

                            # High-visibility operator alert
                            intent_badge = "🔥 [HOT INTEREST / PHONE PROVIDED]" if intent == "HOT_LEAD" else "[INCOMING REPLY]"
                            self.log_event(
                                f"{intent_badge} from {biz_name} ({from_email})! Subject: '{subject[:60]}' ➔ Marked REPLIED, all follow-ups locked out.",
                                "SUCCESS"
                            )
                            print(f"\n  {ui.C_GREEN}╔═══════════════════════════════════════════════════════════════════════════════════════╗{ui.RESET}")
                            print(f"  {ui.C_WHITE}║  ⭐ {ui.C_YELLOW}NEW HOTEL REPLY RECEIVED! {intent_badge}{ui.RESET}")
                            print(f"  {ui.C_CYAN}║  From:    {biz_name} <{from_email}>")
                            print(f"  {ui.C_WHITE}║  Subject: {subject[:70]}")
                            if extracted_phone:
                                print(f"  {ui.C_GREEN}║  Phone:   {extracted_phone} (Auto-saved to Lead CRM)")
                            print(f"  {ui.C_GREEN}║  Status:  Lead #{lead_id} updated to REPLIED. Follow-ups automatically halted!       ║{ui.RESET}")
                            print(f"  {ui.C_GREEN}╚═══════════════════════════════════════════════════════════════════════════════════════╝{ui.RESET}\n")
                    else:
                        # Unmatched lead, but check if subject indicates an inbound response to our cold pitches
                        sub_clean = (subject or "").strip().lower()
                        if sub_clean.startswith("re:") or any(kw in sub_clean for kw in ["gethotelstays", "aloria", "ota commission", "hotel stays", "hotelstays"]):
                            # Block this sender email and domain from ALL future pitches or follow-ups
                            db.add_to_replied_contacts(email=from_email, business_name=from_raw or "Inbound Lead", source=f"SENTINEL_UNMATCHED_{user_email}")
                            db.log_outreach_event(
                                lead_id=0,
                                business_name=from_raw or "Inbound Lead",
                                recipient_email=user_email,
                                sender_email=from_email,
                                pitch_type="INCOMING_REPLY",
                                subject=subject,
                                status="REPLIED",
                                business_id="gethotelstays"
                            )
                            replies_count += 1
                            self.total_replies_found += 1
                            self.log_event(f"🛡️ INCOMING REPLY BLOCKED: {from_email} (Subject: '{subject[:45]}') registered to replied suppression registry.", "SUCCESS")
                except Exception:
                    continue

            imap.logout()

        except Exception as ex:
            self.log_event(f"IMAP connection failed for {user_email}: {ex}", "WARN")

        return bounces_count, replies_count

    def get_state(self) -> dict[str, Any]:
        base = super().get_state()
        base.update({
            "check_interval_seconds": self.check_interval,
            "last_check_time": self.last_check_time,
            "total_bounces_found": self.total_bounces_found,
            "total_replies_found": self.total_replies_found,
            "recent_replies": self.recent_replies[-10:],
            "recent_bounces": self.recent_bounces[-10:],
        })
        return base
