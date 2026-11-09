"""
Aloria Hunter - Autonomous AI Closer & Hotel Onboarding Engine
==============================================================
Trained directly on official GetHotelStays Reply Email Templates
(gethotelstays_reply_templates.txt):
1. HOTEL IS INTERESTED -> Get Started with GetHotelStays
2. HOTEL ASKS ABOUT CHANNEL MANAGER -> Managing Your Property on GetHotelStays
3. HOTEL DECLINES PARTNERSHIP -> Re: GetHotelStays Partnership (Re-engagement)
4. HOTEL ASKS ABOUT PRICING -> GetHotelStays — Pricing Information
5. HOTEL ASKS HOW THE PLATFORM WORKS -> How GetHotelStays Works
6. HOTEL RAISES AN OBJECTION / UNCLEAR -> Clarification & Free Registration
7. HOTEL ASKS FOR MORE INFORMATION -> Learn More About GetHotelStays (About + Onboarding)

Plus:
- Automated WhatsApp/Phone extraction & CRM contact synchronization (leads.phone)
- In-thread multi-turn SMTP reply with strict RFC headers (In-Reply-To, References)
- Non-lead filter (ignores cold spam, newsletters, non-pitched domains)
"""

import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime, timezone
import json
from pathlib import Path
from email.utils import parsedate_to_datetime
import sqlite3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random
import time

import config
import db
import ui

DB_PATH = Path(__file__).resolve().parent / "hunter.db"
PARENT_DIR = Path(__file__).resolve().parent.parent

# Official Links (from config or defaults)
GHS_ONBOARDING_LINK = getattr(config, "GHS_ONBOARDING_LINK", "https://gethotelstays.com/list-property/")
GHS_ABOUT_LINK = getattr(config, "GHS_ABOUT_LINK", "https://gethotelstays.com/about/")

# Pattern Matchers for 7 Core Intent Categories
CHANNEL_MANAGER_PATTERNS = [
    r"channel manager", r"channel-manager", r"channelmanager", r"cm integration",
    r"\bpms\b", r"staah", r"maximojo", r"ratetiger", r"rate tiger", r"synxis",
    r"d-edge", r"hotelogix", r"ezee", r"ezeetechnosys", r"connect via cm",
    r"api connect", r"integrated with"
]

HOW_IT_WORKS_PATTERNS = [
    r"how it works", r"how does it work", r"how do you operate", r"payout",
    r"payment cycle", r"commission per booking", r"payment terms", r"how do we get paid",
    r"working model", r"business model", r"explain the process", r"how do you work"
]

PRICING_PATTERNS = [
    r"pricing", r"how much", r"\bcost\b", r"\bfee\b", r"charges", r"listing charge",
    r"registration charge", r"membership fee", r"subscription", r"commercials",
    r"what are the charges", r"registration fee"
]

MORE_INFO_PATTERNS = [
    r"more info", r"more information", r"tell me more", r"details", r"brochure",
    r"presentation", r"share details", r"send details", r"deck", r"website link",
    r"profile link", r"share profile"
]

DECLINED_PATTERNS = [
    r"not interested", r"no thanks", r"decline", r"not looking", r"don't need",
    r"do not need", r"remove us", r"unsubscribe", r"stop emailing", r"not right now",
    r"not at the moment"
]

INTERESTED_PATTERNS = [
    r"interested", r"we would like to join", r"want to join", r"sign up",
    r"how to register", r"how to onboard", r"send link", r"send registration",
    r"onboard us", r"listing link", r"registration link", r"proceed",
    r"glad to partner", r"looking forward to", r"happy to collaborate"
]

PHONE_PATTERNS = [
    r'(?:\+?91[\-\s]?)?[6-9]\d{9}',                     # Indian 10-digit mobile
    r'(?:\+?971[\-\s]?)?(?:5[0-9]|4[0-9])[\-\s]?\d{7}', # UAE mobile & landline
    r'0\d{10}',                                         # Landline with std code
    r'\+?\d{1,4}[\s\-]?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}' # International
]

def extract_phone_numbers(text: str) -> list[str]:
    """Extracts valid phone/WhatsApp numbers from email text."""
    if not text:
        return []
    candidates = []
    for pattern in PHONE_PATTERNS:
        matches = re.findall(pattern, text)
        for m in matches:
            clean = re.sub(r'[\s\-\(\)]', '', m)
            if len(clean) >= 9 and clean not in candidates:
                candidates.append(clean)
    return candidates

def classify_inbound_intent(body: str) -> str:
    """
    Classifies inbound hotel reply into one of the 7 official GetHotelStays template categories:
    1. CHANNEL_MANAGER
    2. HOW_IT_WORKS
    3. PRICING
    4. MORE_INFO
    5. DECLINED
    6. INTERESTED
    7. UNCLEAR_OBJECTION
    """
    text = (body or "").lower()

    # 1. Channel Manager query has highest specificity
    if any(re.search(p, text) for p in CHANNEL_MANAGER_PATTERNS):
        return "CHANNEL_MANAGER"

    # 2. How platform works / commission / payout
    if any(re.search(p, text) for p in HOW_IT_WORKS_PATTERNS):
        return "HOW_IT_WORKS"

    # 3. Pricing / Charges query
    if any(re.search(p, text) for p in PRICING_PATTERNS):
        return "PRICING"

    # 4. More Information / About Page request
    if any(re.search(p, text) for p in MORE_INFO_PATTERNS):
        return "MORE_INFO"

    # 5. Explicit Decline / Unsubscribe
    if any(re.search(p, text) for p in DECLINED_PATTERNS):
        return "DECLINED"

    # 6. Explicit Interest / Registration request
    if any(re.search(p, text) for p in INTERESTED_PATTERNS):
        return "INTERESTED"

    # 7. WhatsApp or Phone shared -> Route to Interested / Onboarding
    phones = extract_phone_numbers(body)
    if phones and any(k in text for k in ["whatsapp", "contact", "number", "reach", "call", "mobile", "phone"]):
        return "WHATSAPP_SHARED"

    # 8. Unclear response / generic objection
    return "UNCLEAR_OBJECTION"

def generate_official_template_reply(hotel_name: str, intent: str, orig_subject: str = "") -> tuple[str, str, str]:
    """
    Generates exact GetHotelStays official reply template matching gethotelstays_reply_templates.txt.
    Returns: (subject, plain_text, html_text)
    """
    h_display = hotel_name or "Property Team"

    # 1. HOTEL IS INTERESTED (or shared WhatsApp)
    if intent in ["INTERESTED", "WHATSAPP_SHARED"]:
        subj = "Get Started with GetHotelStays"
        plain = f"""Hi {h_display},

We’re glad you’re interested in joining GetHotelStays!

You can register your property through the link below. The registration process is simple and free.

{GHS_ONBOARDING_LINK}

Once you’ve registered, please let us know so we can review and approve your property.

Best regards,
GetHotelStays Team"""

    # 2. HOTEL ASKS WHETHER WE USE A CHANNEL MANAGER
    elif intent == "CHANNEL_MANAGER":
        subj = "Managing Your Property on GetHotelStays"
        plain = f"""Hi {h_display},

GetHotelStays operates independently of traditional channel managers, allowing your property to manage its rates and bookings directly through our platform.

You only need to enter your room rates, including seasonal pricing, once. Our specialized AI agents will then help set up and manage your property’s profile, handle guest communication, and help you attract more bookings.

This means you can get started without the additional cost or complexity of a channel manager.

You can register your property here:

{GHS_ONBOARDING_LINK}

Best regards,
GetHotelStays Team"""

    # 3. HOTEL DECLINES THE PARTNERSHIP OR SAYS THEY ARE NOT INTERESTED
    elif intent == "DECLINED":
        subj = "Re: GetHotelStays Partnership"
        plain = f"""Hi {h_display},

Thank you for your response.

May we ask what is preventing you from moving forward with the partnership?

We offer hotels the opportunity to increase their bookings without any upfront registration fees. We’d appreciate the opportunity to understand your concerns and see if we can address them.

Best regards,
GetHotelStays Team"""

    # 4. HOTEL ASKS ABOUT PRICING
    elif intent == "PRICING":
        subj = "GetHotelStays — Pricing Information"
        plain = f"""Hi {h_display},

There is no charge to register your property on GetHotelStays.

We offer hotels the opportunity to increase their bookings and improve their operations through our platform.

You can register your property free of cost using the link below:

{GHS_ONBOARDING_LINK}

Best regards,
GetHotelStays Team"""

    # 5. HOTEL ASKS HOW THE PLATFORM WORKS
    elif intent == "HOW_IT_WORKS":
        subj = "How GetHotelStays Works"
        plain = f"""Hi {h_display},

GetHotelStays uses specialized AI agents to manage each property’s profile and help generate bookings.

Our platform operates on a 12% commission per booking received through GetHotelStays, with no registration fee.

Once a booking is completed, you can request a payout whenever you need it. Payments are processed in less than one week.

You can register your property here:

{GHS_ONBOARDING_LINK}

Best regards,
GetHotelStays Team"""

    # 7. HOTEL ASKS FOR MORE INFORMATION
    elif intent == "MORE_INFO":
        subj = "Learn More About GetHotelStays"
        plain = f"""Hi {h_display},

Thank you for your interest in GetHotelStays.

You can learn more about our platform and how we help properties increase their bookings through our About page:

{GHS_ABOUT_LINK}

If you’d like to register your property, you can do so free of cost here:

{GHS_ONBOARDING_LINK}

We look forward to welcoming your property to GetHotelStays.

Best regards,
GetHotelStays Team"""

    # 6. HOTEL RAISES AN OBJECTION OR GIVES AN UNCLEAR RESPONSE (Default)
    else:
        subj = "Re: GetHotelStays Partnership"
        plain = f"""Hi {h_display},

Thank you for your response.

We understand your concern and welcome any questions you may have.

Could you please clarify whether you are interested in joining GetHotelStays, or if there is a specific concern preventing you from moving forward?

If you’re interested, you can register your property free of cost here:

{GHS_ONBOARDING_LINK}

Best regards,
GetHotelStays Team"""

    # Format HTML version with clean typography and clickable links
    html_lines = []
    for line in plain.split("\n"):
        clean_l = line.strip()
        if not clean_l:
            html_lines.append("<br/>")
        elif clean_l == GHS_ONBOARDING_LINK:
            html_lines.append(f"<p style='margin:10px 0;'><a href='{GHS_ONBOARDING_LINK}' style='color:#0d6efd; font-weight:bold; text-decoration:underline;'>{GHS_ONBOARDING_LINK}</a></p>")
        elif clean_l == GHS_ABOUT_LINK:
            html_lines.append(f"<p style='margin:10px 0;'><a href='{GHS_ABOUT_LINK}' style='color:#0d6efd; font-weight:bold; text-decoration:underline;'>{GHS_ABOUT_LINK}</a></p>")
        else:
            html_lines.append(f"<p style='margin:0 0 8px 0; line-height: 1.5;'>{clean_l}</p>")

    html = f"""<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 14px; color: #222222;">
    {''.join(html_lines)}
    </div>"""

    return subj, plain, html

def _clean_email_str(raw: str) -> str:
    if not raw:
        return ""
    m = re.search(r'<([^>]+)>', raw)
    if m:
        return m.group(1).strip().lower()
    m = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', raw)
    if m:
        return m.group(1).strip().lower()
    return raw.strip().lower()

def _decode_hdr(val: str | None) -> str:
    if not val:
        return ""
    try:
        dh = decode_header(val)
        return "".join(s.decode(enc or "utf-8", errors="ignore") if isinstance(s, bytes) else str(s) for s, enc in dh).strip()
    except Exception:
        return str(val)

def _get_body_from_email_msg(msg) -> str:
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdisp = str(part.get('Content-Disposition'))
            if ctype == 'text/plain' and 'attachment' not in cdisp:
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode('utf-8', errors='ignore')
                    break
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body = payload.decode('utf-8', errors='ignore')

    clean_lines = []
    for line in body.splitlines():
        if line.strip().startswith('>') or ('On ' in line and 'wrote:' in line):
            break
        clean_lines.append(line)
    return '\n'.join(clean_lines).strip()

def process_and_close_inbound_threads(dry_run: bool = False, limit: int = 15) -> int:
    """
    Scans threads categorized as WAITING_FOR_OPERATOR_REPLY, extracts last inbound message,
    classifies intent according to official GetHotelStays playbook, updates DB,
    and dispatches the exact corresponding template response!
    """
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT id, thread_id, sender_profile, sender_email, lead_email, hotel_name, subject, step_count
    FROM responsed_followups
    WHERE classification = 'WAITING_FOR_OPERATOR_REPLY' AND status = 'PENDING'
    ORDER BY id DESC
    LIMIT ?
    """, (limit,))
    waiting_threads = [dict(r) for r in c.fetchall()]
    conn.close()

    if not waiting_threads:
        print(f"  {ui.C_GREEN}[AI CLOSER]{ui.RESET} 0 pending inbound replies waiting. All threads up to date.")
        return 0

    print(f"\n{ui.C_CYAN}╔═══════════════════════════════════════════════════════════════════════════════════════════════╗{ui.RESET}")
    print(f"  {ui.C_CYAN}║     🧠 AI AUTONOMOUS CLOSER: MATCHING {len(waiting_threads)} INBOUND REPLIES WITH GETHOTELSTAYS TEMPLATES     ║{ui.RESET}")
    print(f"  {ui.C_CYAN}╚═══════════════════════════════════════════════════════════════════════════════════════════════╝{ui.RESET}\n")

    closed_count = 0
    smtp_data = config.get_raw_smtp_data().get("profiles", {})

    for item in waiting_threads:
        prof_key = item['sender_profile']
        thrid = item['thread_id']
        lead_email = item['lead_email']
        hotel_name = item['hotel_name'] or "Hotel Partner"
        orig_subject = item['subject'] or "GetHotelStays Partnership"

        # Strict Hotel Outreach Verification Gate:
        # Must be an actual hotel lead that was officially pitched in outreach_logs or leads table!
        conn_v = db.get_connection()
        cv = conn_v.cursor()
        cv.execute("SELECT 1 FROM outreach_logs WHERE LOWER(TRIM(recipient_email)) = ? LIMIT 1", (lead_email,))
        pitched_in_logs = cv.fetchone() is not None
        cv.execute("SELECT 1 FROM leads WHERE LOWER(TRIM(email)) = ? LIMIT 1", (lead_email,))
        pitched_in_leads = cv.fetchone() is not None
        conn_v.close()

        if not pitched_in_logs and not pitched_in_leads:
            print(f"  {ui.C_DIM}[🛡 SKIPPED NON-LEAD]{ui.RESET} {lead_email} was never pitched by GetHotelStays. Skipping inbox noise.")
            conn_u = db.get_connection()
            cu = conn_u.cursor()
            cu.execute("UPDATE responsed_followups SET status = 'EXEMPT_SPAM' WHERE id = ?", (item['id'],))
            conn_u.commit()
            conn_u.close()
            continue

        prof_conf = smtp_data.get(prof_key, {})
        user_email = str(prof_conf.get("email") or "").lower()
        pwd = (prof_conf.get("password") or "").replace(" ", "").strip()

        if not user_email or not pwd:
            print(f"  {ui.C_YELLOW}[!] Missing SMTP config for profile {prof_key}. Skipping.{ui.RESET}")
            continue

        try:
            # 1. Connect IMAP to read the full thread and extract the last inbound message
            imap = imaplib.IMAP4_SSL("imap.gmail.com", 993, timeout=12)
            imap.login(user_email, pwd)
            imap.select('"[Gmail]/All Mail"', readonly=True)

            typ, tdata = imap.search(None, f'X-GM-THRID {thrid}')
            if not tdata or not tdata[0]:
                imap.logout()
                continue

            msg_ids = tdata[0].split()
            last_msg_id_num = msg_ids[-1]

            typ, mdata = imap.fetch(last_msg_id_num, '(RFC822)')
            if not mdata or not isinstance(mdata[0], tuple):
                imap.logout()
                continue

            last_msg_raw = mdata[0][1]
            last_email_obj = email.message_from_bytes(last_msg_raw)
            last_from = _clean_email_str(_decode_hdr(last_email_obj.get("From")))
            last_msg_id_header = last_email_obj.get("Message-ID", "").strip()
            last_subject = _decode_hdr(last_email_obj.get("Subject"))
            inbound_body = _get_body_from_email_msg(last_email_obj)
            imap.logout()

            # Verify last message is indeed from the hotel (not our account)
            if last_from == user_email:
                conn_u = db.get_connection()
                cu = conn_u.cursor()
                cu.execute("UPDATE responsed_followups SET classification = 'WAITING_48H_WINDOW' WHERE id = ?", (item['id'],))
                conn_u.commit()
                conn_u.close()
                continue

            # 2. Classify Hotel Intent based on official templates
            intent = classify_inbound_intent(inbound_body)
            extracted_phones = extract_phone_numbers(inbound_body)

            print(f"  {ui.C_MAGENTA}► [HOTEL INBOUND DETECTED]{ui.RESET} {ui.C_WHITE}{hotel_name}{ui.RESET} ({lead_email})")
            print(f"    Intent Matched: {ui.C_YELLOW}{intent}{ui.RESET} │ Profile: {user_email}")
            if extracted_phones:
                print(f"    {ui.C_GREEN}📞 WhatsApp / Mobile Captured:{ui.RESET} {', '.join(extracted_phones)}")

            # Update DB with extracted phone & onboarding status
            conn = db.get_connection()
            c = conn.cursor()
            if extracted_phones:
                phone_val = extracted_phones[0]
                c.execute("""
                UPDATE leads 
                SET phone = ?, status = 'ONBOARDING_IN_PROGRESS' 
                WHERE LOWER(TRIM(email)) = ?
                """, (phone_val, lead_email))

            if intent == "DECLINED":
                c.execute("UPDATE leads SET status = 'OPT_OUT' WHERE LOWER(TRIM(email)) = ?", (lead_email,))
                db.add_to_blacklist(lead_email, reason="Hotel requested opt-out", source="AI_CLOSER")

            conn.commit()
            conn.close()

            # 3. Generate Official GetHotelStays Template Reply
            template_subj, plain_reply, html_reply = generate_official_template_reply(hotel_name, intent, orig_subject)

            # In-thread subject preservation:
            clean_sub = last_subject or orig_subject
            if not clean_sub.lower().startswith("re:"):
                dispatch_subject = f"Re: {clean_sub}"
            else:
                dispatch_subject = clean_sub

            if dry_run:
                print(f"    {ui.C_CYAN}[DRY-RUN TEMPLATE MATCHED: {template_subj}]:{ui.RESET}\n{plain_reply}\n")
                closed_count += 1
                continue

            # 4. Dispatch In-Thread Reply via SMTP
            msg = MIMEMultipart("alternative")
            msg["Subject"] = dispatch_subject
            msg["From"] = f"GetHotelStays Team <{user_email}>"
            msg["To"] = lead_email
            if last_msg_id_header:
                msg["In-Reply-To"] = last_msg_id_header
                msg["References"] = last_msg_id_header

            msg.attach(MIMEText(plain_reply, "plain", "utf-8"))
            msg.attach(MIMEText(html_reply, "html", "utf-8"))

            server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15)
            server.login(user_email, pwd)
            server.sendmail(user_email, [lead_email], msg.as_string())
            server.quit()

            # 5. Update responsed_followups record
            conn = db.get_connection()
            c = conn.cursor()
            now_iso = datetime.now(timezone.utc).isoformat()
            c.execute("""
            UPDATE responsed_followups
            SET classification = 'AI_AUTO_REPLIED',
                status = 'RESOLVED',
                last_sender = ?,
                last_message_at = ?,
                dispatched_at = ?
            WHERE id = ?
            """, (user_email, now_iso, now_iso, item['id']))
            conn.commit()
            conn.close()

            db.log_outreach_event(
                lead_id=item['id'],
                business_name=hotel_name,
                recipient_email=lead_email,
                sender_email=user_email,
                pitch_type=f"GHS_TEMPLATE_{intent}",
                subject=dispatch_subject,
                status="SENT",
                business_id="gethotelstays"
            )

            print(f"    {ui.C_GREEN}✓ Dispatched official template [{template_subj}] in thread.{ui.RESET}")
            closed_count += 1
            time.sleep(random.uniform(3.0, 6.0))

        except Exception as e:
            print(f"    {ui.C_RED}[!] Error closing thread for {hotel_name}: {e}{ui.RESET}")

    print(f"\n{ui.C_GREEN}✓ Successfully matched & dispatched official templates to {closed_count} hotels!{ui.RESET}\n")
    return closed_count

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AI Autonomous Closer Engine - Official GHS Templates")
    parser.add_argument("--dry-run", action="store_true", help="Preview template replies without sending")
    parser.add_argument("--limit", type=int, default=15, help="Max threads to close")
    args = parser.parse_args()
    process_and_close_inbound_threads(dry_run=args.dry_run, limit=args.limit)
