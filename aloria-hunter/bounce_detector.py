import imaplib
import email
import re
from datetime import datetime, timedelta
from pathlib import Path
import config
import db
import ui

BOUNCE_SUBJECT_KEYWORDS = [
    "delivery status notification",
    "undelivered mail",
    "failure notice",
    "mail delivery subsystem",
    "returned mail",
    "delivery failed",
    "could not be delivered"
]

def clean_bounced_address(raw_addr):
    if not raw_addr:
        return None
    addr = raw_addr.strip().lower()
    # Strip angle brackets, quotes, trailing hyphens, dots, semicolons
    addr = re.sub(r'^[<"\'\s]+|[>"\'\s,;.-]+$', '', addr)
    if "@" not in addr or len(addr) < 5:
        return None
    # Reject sender / system domains
    if any(ignore in addr for ignore in ["googlemail.com", "google.com", "mailer-daemon", "postmaster"]):
        return None
    return addr

def extract_bounced_addresses_from_msg(msg):
    bounced = set()
    reason = "Address not found or mailbox unavailable"

    # 1. Check standard header X-Failed-Recipients
    x_failed = msg.get("X-Failed-Recipients")
    if x_failed:
        for part in re.split(r'[,;\s]+', x_failed):
            cleaned = clean_bounced_address(part)
            if cleaned:
                bounced.add(cleaned)

    # 2. Check RFC 3464 delivery status report parts or body text
    body_parts = []
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            try:
                payload = part.get_payload(decode=True)
                if payload:
                    body_parts.append(payload.decode("utf-8", errors="ignore"))
            except Exception:
                pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                body_parts.append(payload.decode("utf-8", errors="ignore"))
        except Exception:
            body_parts.append(str(msg))

    full_body = "\n".join(body_parts)

    # Check for Final-Recipient: rfc822; user@example.com
    for match in re.findall(r'Final-Recipient:\s*(?:rfc822;)?\s*([^\s\r\n;]+)', full_body, re.I):
        cleaned = clean_bounced_address(match)
        if cleaned:
            bounced.add(cleaned)

    # Check for Original-Recipient
    for match in re.findall(r'Original-Recipient:\s*(?:rfc822;)?\s*([^\s\r\n;]+)', full_body, re.I):
        cleaned = clean_bounced_address(match)
        if cleaned:
            bounced.add(cleaned)

    # Check for server error reason
    err_match = re.search(r'The response from the remote server was:\s*([^\r\n]+)', full_body, re.I)
    if err_match:
        reason = err_match.group(1).strip()[:100]
    else:
        status_match = re.search(r'Diagnostic-Code:\s*(?:smtp;)?\s*([^\r\n]+)', full_body, re.I)
        if status_match:
            reason = status_match.group(1).strip()[:100]

    # If still empty, regex search for failed email lines
    if not bounced:
        for line in full_body.splitlines():
            line_str = line.strip()
            if any(k in line_str.lower() for k in ["550", "554", "551", "552", "address not found", "does not exist", "mailbox unavailable"]):
                candidates = re.findall(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', line_str)
                for cand in candidates:
                    cleaned = clean_bounced_address(cand)
                    if cleaned:
                        bounced.add(cleaned)

    return list(bounced), reason

def scan_inbox_bounces(profile_name=None, silent=False):
    """
    Connects to Gmail via IMAP, discovers all delivery bounce notices,
    and automatically registers them into email_blacklist & marks leads as BOUNCED.
    """
    smtp_conf = config.get_smtp_config(profile_name)
    user_email = str(smtp_conf.get("email") or "")
    password = (smtp_conf.get("password") or "").replace(" ", "").strip()
    imap_server = "imap.gmail.com"
    imap_port = 993

    if not user_email or not password:
        if not silent:
            print(f"  {ui.C_RED}[!] Error: No email/password configured for {user_email or profile_name} IMAP access.{ui.RESET}")
        return {"success": False, "error": "No password", "newly_blacklisted": 0, "bounced_emails": []}

    if not silent:
        print(f"  {ui.C_MAGENTA}[🛡 BOUNCE DETECTOR]{ui.RESET} Connecting to IMAP inbox for {ui.C_CYAN}{user_email}{ui.RESET}...")

    try:
        imap = imaplib.IMAP4_SSL(imap_server, imap_port, timeout=20)
        imap.login(user_email, password)
        imap.select("INBOX", readonly=True)

        # Search for Mailer-Daemon or Postmaster
        all_ids = set()

        typ, data_md = imap.search(None, 'FROM', 'mailer-daemon')
        if data_md and data_md[0]:
            all_ids.update(data_md[0].split())

        typ, data_pm = imap.search(None, 'FROM', 'postmaster')
        if data_pm and data_pm[0]:
            all_ids.update(data_pm[0].split())

        msg_ids = sorted(list(all_ids), key=lambda x: int(x))

        if not silent:
            print(f"  {ui.C_CYAN}[🛡 BOUNCE DETECTOR]{ui.RESET} Found {ui.C_WHITE}{len(msg_ids)}{ui.RESET} delivery status / failure messages in inbox.")

        newly_blacklisted = 0
        all_detected_bounces = []

        for msg_id in msg_ids:
            try:
                typ, msg_data = imap.fetch(msg_id, '(RFC822)')
                if not msg_data or not msg_data[0] or not isinstance(msg_data[0], tuple):
                    continue

                msg = email.message_from_bytes(msg_data[0][1])
                subject = msg.get("Subject", "").lower()

                # Filter if it's delivery delay rather than permanent failure
                if "delay" in subject and "failure" not in subject:
                    continue

                bounced_addrs, reason = extract_bounced_addresses_from_msg(msg)
                for b_addr in bounced_addrs:
                    all_detected_bounces.append(b_addr)
                    # Check if already blacklisted
                    was_added = db.add_to_blacklist(
                        email=b_addr,
                        reason=reason,
                        source=f"IMAP_{user_email}"
                    )
                    if was_added:
                        newly_blacklisted += 1
                        if not silent:
                            print(f"  {ui.C_RED}[✗ BOUNCE BLACKLISTED]{ui.RESET} {ui.C_WHITE}{b_addr}{ui.RESET} ➔ {ui.C_DIM}{reason[:50]}{ui.RESET}")
            except Exception as ex:
                continue

        imap.logout()

        unique_bounces = list(set(all_detected_bounces))
        if not silent:
            print(f"  {ui.C_GREEN}[✓ BOUNCE AUDIT COMPLETE]{ui.RESET} Identified {len(unique_bounces)} invalid addresses. Added {ui.C_YELLOW}{newly_blacklisted}{ui.RESET} new entries to permanent blacklist.")

        return {
            "success": True,
            "total_bounces_found": len(unique_bounces),
            "newly_blacklisted": newly_blacklisted,
            "bounced_emails": unique_bounces
        }

    except Exception as e:
        if not silent:
            print(f"  {ui.C_RED}[!] IMAP connection error for {user_email}: {e}{ui.RESET}")
        return {"success": False, "error": str(e), "newly_blacklisted": 0, "bounced_emails": []}

def scan_all_profiles():
    profiles, _ = config.list_smtp_profiles()
    total_new = 0
    all_bounces = []
    for prof_key in profiles.keys():
        res = scan_inbox_bounces(profile_name=prof_key, silent=False)
        if res.get("success"):
            total_new += res.get("newly_blacklisted", 0)
            all_bounces.extend(res.get("bounced_emails", []))
    return {
        "total_newly_blacklisted": total_new,
        "all_bounces": list(set(all_bounces))
    }

if __name__ == "__main__":
    scan_all_profiles()
