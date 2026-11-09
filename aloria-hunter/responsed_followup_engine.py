"""
GetHotelStays - Responsed Follow-up Engine
===========================================
Specialized engine for mid-funnel leads based on Shriyansh's exact 4-Step & 2-Day Rules:
1. High-speed thread discovery:
   - Scans INBOX of GetHotelStays accounts for real inbound human replies.
   - Extracts Gmail thread IDs (X-GM-THRID).
   - Reconstructs complete multi-turn conversations from [Gmail]/All Mail.
2. Classification Rules:
   - DEEP_CONVERSATION_EXEMPT: Thread length > 4 steps (5, 6, 7+) -> 100% PROTECTED, NEVER MESSAGE (Onboarded/Deep negotiation).
   - WAITING_FOR_OPERATOR_REPLY: Last message sent by Hotel -> Operator (Shriyansh) must reply manually.
   - WAITING_48H_WINDOW: Shriyansh sent last message, but < 48 hours elapsed -> Wait for grace period.
   - RESPONSED_FOLLOWUP_READY: 2, 3, or 4 messages in thread, last message sent by Shriyansh, >= 48 hours elapsed with 0 hotel response -> ELIGIBLE FOR NUDGE.
"""

import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
from email.utils import parsedate_to_datetime
import sqlite3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config
import db
import ui

DB_PATH = Path(__file__).resolve().parent / "hunter.db"
ROOT_DIR = Path(__file__).resolve().parent.parent

IGNORED_SENDERS = [
    "mailer-daemon", "postmaster", "google.com", "googlemail.com", "linkedin.com",
    "instagram.com", "semrush.com", "tripadvisor", "facebookmail", "noreply",
    "no-reply", "security@account", "accounts.snapchat", "udchalo.com"
]

def _init_responsed_followup_table():
    conn = db.get_connection()
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS responsed_followups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        thread_id TEXT UNIQUE NOT NULL,
        sender_profile TEXT NOT NULL,
        sender_email TEXT NOT NULL,
        lead_email TEXT NOT NULL,
        hotel_name TEXT,
        subject TEXT,
        step_count INTEGER DEFAULT 0,
        last_sender TEXT,
        last_message_at TEXT,
        hours_elapsed REAL DEFAULT 0,
        classification TEXT,
        status TEXT DEFAULT 'PENDING',
        dispatched_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_rf_thread_id ON responsed_followups(thread_id);
    CREATE INDEX IF NOT EXISTS idx_rf_classification ON responsed_followups(classification);
    CREATE INDEX IF NOT EXISTS idx_rf_lead_email ON responsed_followups(lead_email);
    """)
    conn.commit()
    conn.close()

def _decode_header_str(val):
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

def _clean_email(raw_str):
    if not raw_str:
        return ""
    match = re.search(r'<([^>]+)>', raw_str)
    if match:
        return match.group(1).strip().lower()
    match = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', raw_str)
    if match:
        return match.group(1).strip().lower()
    return raw_str.strip().lower()

def _clean_hotel_name(name):
    if not name:
        return ""
    name = re.sub(r'[\ue000-\uf8ff]', '', name)
    if 'Sponsored' in name:
        lines = [line.strip() for line in name.split('\n') if line.strip()]
        filtered = [l for l in lines if not l.lower().startswith('sponsored') and not l.lower().startswith('by ')]
        if filtered:
            name = filtered[0]
    name = name.replace('\n', ' ').replace('\r', ' ')
    return re.sub(r'\s+', ' ', name).strip()

def scan_inbox_threads(profile_key, verbose=False):
    """
    High-speed two-phase scanner:
    1. Reads INBOX for inbound non-spam messages to extract thread IDs.
    2. Reconstructs each thread from [Gmail]/All Mail using X-GM-THRID.
    """
    _init_responsed_followup_table()
    smtp_conf = config.get_smtp_config(profile_key)
    user_email = str(smtp_conf.get("email") or "").lower()
    password = (smtp_conf.get("password") or "").replace(" ", "").strip()

    if not user_email or not password:
        return []

    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com", 993, timeout=15)
        imap.login(user_email, password)

        # Phase 1: Search INBOX for incoming messages
        imap.select("INBOX", readonly=True)
        typ, data = imap.search(None, "ALL")
        if not data or not data[0]:
            imap.logout()
            return []

        inbox_ids = data[0].split()
        # Scan recent inbox messages (last 60)
        recent_ids = inbox_ids[-60:]
        id_str = b",".join(recent_ids)
        
        typ, mdata = imap.fetch(id_str, '(X-GM-THRID BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])')
        if not mdata:
            imap.logout()
            return []

        active_thrids = set()
        for item in mdata:
            if isinstance(item, tuple):
                header_str = item[0].decode('utf-8', errors='ignore')
                thrid_m = re.search(r'X-GM-THRID\s+(\d+)', header_str)
                from_str = item[1].decode('utf-8', errors='ignore').lower() if len(item) > 1 else ""
                
                # Filter spam/daemons
                if any(ig in from_str for ig in IGNORED_SENDERS):
                    continue
                if thrid_m:
                    active_thrids.add(thrid_m.group(1))

        if not active_thrids:
            imap.logout()
            return []

        # Phase 2: Select All Mail to fetch the full conversation thread
        imap.select('"[Gmail]/All Mail"', readonly=True)
        now = datetime.now(timezone.utc)
        results = []

        conn = db.get_connection()
        c = conn.cursor()

        for thrid in active_thrids:
            try:
                typ, tdata = imap.search(None, f'X-GM-THRID {thrid}')
                if not tdata or not tdata[0]:
                    continue
                t_msg_ids = tdata[0].split()
                if len(t_msg_ids) <= 1:
                    # Single message thread (no reply occurred)
                    continue

                t_id_str = b",".join(t_msg_ids)
                typ, thread_msgs_data = imap.fetch(t_id_str, '(BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE MESSAGE-ID)])')
                
                msgs = []
                for m_part in thread_msgs_data:
                    if isinstance(m_part, tuple):
                        header_raw = m_part[1].decode('utf-8', errors='ignore')
                        msg = email.message_from_string(header_raw)
                        from_addr = _clean_email(_decode_header_str(msg.get("From")))
                        to_addr = _clean_email(_decode_header_str(msg.get("To")))
                        subject = _decode_header_str(msg.get("Subject"))
                        msg_id = msg.get("Message-ID", "").strip()
                        date_str = msg.get("Date")
                        try:
                            dt = parsedate_to_datetime(date_str)
                        except Exception:
                            dt = now

                        msgs.append({
                            'from': from_addr,
                            'to': to_addr,
                            'subject': subject,
                            'msg_id': msg_id,
                            'date': dt,
                            'is_shriyansh': (from_addr == user_email)
                        })

                if not msgs:
                    continue

                msgs.sort(key=lambda x: x['date'])
                step_count = len(msgs)

                # Identify lead email (external party)
                external_emails = set()
                for m in msgs:
                    if not m['is_shriyansh'] and m['from'] and '@' in m['from']:
                        external_emails.add(m['from'])
                    if m['is_shriyansh'] and m['to'] and '@' in m['to']:
                        for part in m['to'].split(','):
                            clean_p = _clean_email(part)
                            if clean_p and clean_p != user_email:
                                external_emails.add(clean_p)

                if not external_emails:
                    continue

                lead_email = sorted(list(external_emails))[0]
                if any(ig in lead_email for ig in IGNORED_SENDERS):
                    continue

                last_msg = msgs[-1]
                last_sender_is_shriyansh = last_msg['is_shriyansh']
                last_dt = last_msg['date']
                hours_elapsed = (now - last_dt).total_seconds() / 3600.0

                # Match Hotel Name
                hotel_name = ""
                c.execute("SELECT business_name FROM leads WHERE LOWER(TRIM(email)) = ? LIMIT 1", (lead_email,))
                lr = c.fetchone()
                if lr and lr['business_name']:
                    hotel_name = _clean_hotel_name(lr['business_name'])
                else:
                    c.execute("SELECT business_name FROM outreach_logs WHERE LOWER(TRIM(recipient_email)) = ? AND business_name IS NOT NULL LIMIT 1", (lead_email,))
                    ol = c.fetchone()
                    if ol and ol['business_name']:
                        hotel_name = _clean_hotel_name(ol['business_name'])
                    else:
                        domain = lead_email.split('@')[1].split('.')[0]
                        hotel_name = domain.capitalize() + " Hotel"

                # Classification by Shriyansh's exact 4-step & 2-day rules
                classification = ""
                if step_count > 4:
                    # Rule B: > 4 steps (5, 6, 7+) -> Deep conversation / Onboarded client (EXCLUDE)
                    classification = "DEEP_CONVERSATION_EXEMPT"
                elif not last_sender_is_shriyansh:
                    # Hotel sent last message -> Waiting for Shriyansh manual reply
                    classification = "WAITING_FOR_OPERATOR_REPLY"
                elif hours_elapsed < 48.0:
                    # Within 2-day grace period
                    classification = "WAITING_48H_WINDOW"
                else:
                    # Rule A: 2, 3, or 4 steps, last was Shriyansh, >= 48 hours ghosted -> RESPONSED FOLLOW-UP!
                    classification = "RESPONSED_FOLLOWUP_READY"

                res_obj = {
                    'thread_id': str(thrid),
                    'sender_profile': profile_key,
                    'sender_email': user_email,
                    'lead_email': lead_email,
                    'hotel_name': hotel_name,
                    'subject': msgs[0]['subject'],
                    'last_msg_id': last_msg['msg_id'],
                    'step_count': step_count,
                    'last_sender': 'Shriyansh' if last_sender_is_shriyansh else lead_email,
                    'last_message_at': last_dt.isoformat(),
                    'hours_elapsed': round(hours_elapsed, 1),
                    'classification': classification
                }

                c.execute("""
                INSERT INTO responsed_followups (
                    thread_id, sender_profile, sender_email, lead_email,
                    hotel_name, subject, step_count, last_sender,
                    last_message_at, hours_elapsed, classification
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(thread_id) DO UPDATE SET
                    step_count = excluded.step_count,
                    last_sender = excluded.last_sender,
                    last_message_at = excluded.last_message_at,
                    hours_elapsed = excluded.hours_elapsed,
                    classification = excluded.classification
                """, (
                    res_obj['thread_id'], res_obj['sender_profile'], res_obj['sender_email'],
                    res_obj['lead_email'], res_obj['hotel_name'], res_obj['subject'],
                    res_obj['step_count'], res_obj['last_sender'], res_obj['last_message_at'],
                    res_obj['hours_elapsed'], res_obj['classification']
                ))

                results.append(res_obj)

            except Exception:
                continue

        conn.commit()
        conn.close()
        imap.logout()
        return results

    except Exception as e:
        if verbose:
            print(f"Error scanning {user_email}: {e}")
        return []

def scan_all_gethotelstays_accounts():
    """
    Scans all 12 GetHotelStays sender accounts.
    """
    _init_responsed_followup_table()
    profiles, _ = config.list_smtp_profiles()
    all_results = []

    print(f"\n  {ui.C_MAGENTA}[🔍 RESPONSED FOLLOW-UP SCANNER]{ui.RESET} Scanning GetHotelStays inboxes for conversation threads...")

    ghs_keys = [k for k in profiles.keys() if 'gethotelstays' in k or 'shriyanshaloria' in k]
    for key in ghs_keys:
        res = scan_inbox_threads(key)
        if res:
            all_results.extend(res)
            print(f"    * {key}: Scanned {len(res)} multi-message threads.")

    ready = [r for r in all_results if r['classification'] == "RESPONSED_FOLLOWUP_READY"]
    waiting = [r for r in all_results if r['classification'] == "WAITING_48H_WINDOW"]
    exempt = [r for r in all_results if r['classification'] == "DEEP_CONVERSATION_EXEMPT"]
    op_waiting = [r for r in all_results if r['classification'] == "WAITING_FOR_OPERATOR_REPLY"]

    print(f"\n  {ui.C_GREEN}[✓ SCAN COMPLETE]{ui.RESET}")
    print(f"    🎯 Responsed Follow-ups Ready (>48h ghosted): {ui.C_YELLOW}{len(ready)}{ui.RESET}")
    print(f"    ⏳ Waiting within 2-day window:                {ui.C_CYAN}{len(waiting)}{ui.RESET}")
    print(f"    🛑 Deep Conversations / Onboarded (>4 steps):  {ui.C_WHITE}{len(exempt)} (100% Protected){ui.RESET}")
    print(f"    💬 Waiting for your manual reply:             {ui.C_MAGENTA}{len(op_waiting)}{ui.RESET}")

    return {
        'ready': ready,
        'waiting': waiting,
        'exempt': exempt,
        'op_waiting': op_waiting,
        'all': all_results
    }

def get_ready_responsed_followups():
    """Returns all leads ready for responsed follow-up from the database."""
    _init_responsed_followup_table()
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM responsed_followups
        WHERE classification = 'RESPONSED_FOLLOWUP_READY'
          AND status = 'PENDING'
        ORDER BY hours_elapsed DESC
    """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def generate_responsed_followup_message(hotel_name, original_subject):
    """
    Generates a natural, professional nudge in the same thread.
    """
    clean_h = hotel_name or "there"
    subject = original_subject if original_subject.lower().startswith("re:") else f"Re: {original_subject}"

    plain_text = f"""Hi {clean_h} team,

Just bumping this to the top of your inbox in case you missed my last note.

Let me know if you had any questions on the details, or if you'd like us to take this forward!

Best regards,
Shriyansh Aloria
GetHotelStays — Official Partner
"""
    html_text = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #222;">
        <p>Hi <b>{clean_h}</b> team,</p>
        <p>Just bumping this to the top of your inbox in case you missed my last note with the details.</p>
        <p>Let me know if you had any questions on the details, or if you'd like us to take this forward!</p>
        <br>
        <p style="color: #555; margin-bottom: 2px;">Best regards,</p>
        <p style="margin: 0;"><b>Shriyansh Aloria</b><br><span style="color: #6366f1; font-weight: 600;">GetHotelStays</span> — Hotel Distribution Partner</p>
    </div>
    """
    return subject, plain_text, html_text

def dispatch_single_responsed_followup(item, dry_run=False):
    """
    Dispatches a single responsed follow-up in the exact same thread via SMTP.
    """
    prof_key = item['sender_profile']
    smtp_conf = config.get_smtp_config(prof_key)
    sender_email = smtp_conf.get("email")
    password = (smtp_conf.get("password") or "").replace(" ", "").strip()
    to_email = item['lead_email']
    hotel_name = item['hotel_name']
    orig_subject = item['subject'] or f"GetHotelStays — {hotel_name}"

    subject, plain, html = generate_responsed_followup_message(hotel_name, orig_subject)

    if dry_run:
        print(f"  [DRY-RUN] Would send Responsed Follow-up to '{hotel_name}' ({to_email}) via {sender_email}")
        return True, "DRY_RUN"

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{smtp_conf.get('sender_name', 'Shriyansh Aloria — GetHotelStays')} <{sender_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["Reply-To"] = smtp_conf.get("reply_to", sender_email)

        last_msg_id = item.get("last_msg_id")
        if last_msg_id:
            msg["In-Reply-To"] = last_msg_id
            msg["References"] = last_msg_id

        msg.attach(MIMEText(plain, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))

        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=20)
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()

        # Update database
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("""
            UPDATE responsed_followups
            SET status = 'SENT', dispatched_at = CURRENT_TIMESTAMP
            WHERE thread_id = ?
        """, (item['thread_id'],))
        conn.commit()
        conn.close()

        print(f"  {ui.C_GREEN}[✓ RESPONSED FOLLOW-UP DISPATCHED]{ui.RESET} '{hotel_name}' ({to_email}) via {sender_email}")
        return True, "SENT"

    except Exception as e:
        print(f"  {ui.C_RED}[!] Error dispatching to {to_email}: {e}{ui.RESET}")
        return False, str(e)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="GetHotelStays Responsed Follow-up Engine")
    parser.add_argument("--scan", action="store_true", help="Scan all inboxes and categorize threads")
    parser.add_argument("--dispatch", action="store_true", help="Dispatch pending responsed follow-ups")
    parser.add_argument("--limit", type=int, default=None, help="Max follow-ups to dispatch")
    parser.add_argument("--dry-run", action="store_true", help="Preview without actually sending")
    args = parser.parse_args()

    if args.scan or (not args.dispatch and not args.dry_run):
        scan_all_gethotelstays_accounts()
    elif args.dispatch or args.dry_run:
        items = get_ready_responsed_followups()
        if not items:
            print(f"  {ui.C_YELLOW}No pending responsed follow-ups in queue. Run with --scan first!{ui.RESET}")
        else:
            limit = args.limit or len(items)
            print(f"  Found {len(items)} ready. Dispatching up to {limit}...")
            count = 0
            for item in items[:limit]:
                ok, _ = dispatch_single_responsed_followup(item, dry_run=args.dry_run)
                if ok:
                    count += 1
            print(f"  Completed {count} follow-up dispatches.")
