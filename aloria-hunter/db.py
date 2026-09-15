import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "hunter.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_name TEXT NOT NULL,
        country TEXT NOT NULL,
        city TEXT NOT NULL,
        niche TEXT NOT NULL,
        address TEXT,
        phone TEXT,
        rating TEXT,
        reviews_count TEXT,
        has_website INTEGER DEFAULT 0,
        website_url TEXT,
        email TEXT,
        audit_summary TEXT,
        status TEXT DEFAULT 'DISCOVERED',
        initial_email_sent_at TEXT,
        last_follow_up_at TEXT,
        follow_up_count INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        business_id TEXT DEFAULT 'aloria_labs',
        UNIQUE(business_name, city, country)
    );

    CREATE TABLE IF NOT EXISTS outreach_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER,
        business_name TEXT,
        recipient_email TEXT,
        sender_email TEXT,
        pitch_type TEXT,
        subject TEXT,
        status TEXT DEFAULT 'SENT',
        sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
        business_id TEXT DEFAULT 'aloria_labs'
    );

    CREATE TABLE IF NOT EXISTS email_blacklist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        reason TEXT DEFAULT 'BOUNCED',
        source TEXT DEFAULT 'IMAP_BOUNCE',
        blacklisted_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_blacklist_email ON email_blacklist(email);
    """)
    conn.commit()

    # Migration safety check for existing databases without business_id
    cursor.execute("PRAGMA table_info(leads)")
    lead_cols = [r["name"] for r in cursor.fetchall()]
    if "business_id" not in lead_cols:
        cursor.execute("ALTER TABLE leads ADD COLUMN business_id TEXT DEFAULT 'aloria_labs'")
        conn.commit()

    if "whatsapp_status" not in lead_cols:
        cursor.execute("ALTER TABLE leads ADD COLUMN whatsapp_status TEXT DEFAULT NULL")
    if "whatsapp_sent_at" not in lead_cols:
        cursor.execute("ALTER TABLE leads ADD COLUMN whatsapp_sent_at TEXT DEFAULT NULL")

    cursor.execute("PRAGMA table_info(outreach_logs)")
    log_cols = [r["name"] for r in cursor.fetchall()]
    if "business_id" not in log_cols:
        cursor.execute("ALTER TABLE outreach_logs ADD COLUMN business_id TEXT DEFAULT 'aloria_labs'")
        conn.commit()

    conn.close()

def insert_lead(business_name, country, city, niche, address=None, phone=None, rating=None, reviews_count=None, website_url=None, business_id="aloria_labs"):
    conn = get_connection()
    cursor = conn.cursor()
    has_website = 1 if (website_url and website_url.strip() and website_url.startswith("http")) else 0
    try:
        cursor.execute("""
        INSERT INTO leads (business_name, country, city, niche, address, phone, rating, reviews_count, has_website, website_url, status, business_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'DISCOVERED', ?)
        """, (business_name, country, city, niche, address, phone, rating, reviews_count, has_website, website_url, business_id))
        conn.commit()
        lead_id = cursor.lastrowid
        conn.close()
        return lead_id
    except sqlite3.IntegrityError:
        conn.close()
        return None  # Duplicate already in database

def get_pending_audits(business_id=None, limit=20):
    conn = get_connection()
    cursor = conn.cursor()
    if business_id:
        cursor.execute("""
        SELECT * FROM leads WHERE status = 'DISCOVERED' AND has_website = 1 AND business_id = ? LIMIT ?
        """, (business_id, limit))
    else:
        cursor.execute("""
        SELECT * FROM leads WHERE status = 'DISCOVERED' AND has_website = 1 LIMIT ?
        """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_no_website_leads(business_id=None, limit=20):
    conn = get_connection()
    cursor = conn.cursor()
    if business_id:
        cursor.execute("""
        SELECT * FROM leads WHERE status = 'DISCOVERED' AND has_website = 0 AND business_id = ? LIMIT ?
        """, (business_id, limit))
    else:
        cursor.execute("""
        SELECT * FROM leads WHERE status = 'DISCOVERED' AND has_website = 0 LIMIT ?
        """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def update_audit(lead_id, email, audit_summary):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE leads
    SET email = ?, audit_summary = ?, status = 'AUDITED'
    WHERE id = ?
    """, (email, audit_summary, lead_id))
    conn.commit()
    conn.close()

def add_to_blacklist(email, reason="BOUNCED", source="IMAP_BOUNCE"):
    if not email or not isinstance(email, str):
        return False
    clean = email.strip().lower()
    if not clean or "@" not in clean:
        return False
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT OR IGNORE INTO email_blacklist (email, reason, source)
        VALUES (?, ?, ?)
        """, (clean, reason, source))
        conn.commit()
        # Also mark existing leads with this email as BOUNCED
        cursor.execute("""
        UPDATE leads
        SET status = 'BOUNCED', audit_summary = coalesce(audit_summary, '') || ' [BOUNCED: ' || ? || ']'
        WHERE LOWER(TRIM(email)) = ? AND status != 'BOUNCED'
        """, (reason, clean))
        # Update outreach_logs status
        cursor.execute("""
        UPDATE outreach_logs
        SET status = 'BOUNCED'
        WHERE LOWER(TRIM(recipient_email)) = ?
        """, (clean,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        conn.close()
        return False

def is_email_blacklisted(email):
    if not email:
        return False
    clean = email.strip().lower()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM email_blacklist WHERE LOWER(TRIM(email)) = ? LIMIT 1", (clean,))
    res = cursor.fetchone() is not None
    conn.close()
    return res

def get_blacklisted_emails(limit=200):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, reason, source, blacklisted_at FROM email_blacklist ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def is_email_already_contacted(email, business_id=None):
    if not email:
        return False
    clean = email.strip().lower()
    conn = get_connection()
    cursor = conn.cursor()
    # Check outreach_logs: ANY initial outreach sent to this email
    cursor.execute("""
    SELECT 1 FROM outreach_logs 
    WHERE LOWER(TRIM(recipient_email)) = ? AND status = 'SENT'
    LIMIT 1
    """, (clean,))
    if cursor.fetchone():
        conn.close()
        return True

    # Check leads table for sent initial
    cursor.execute("""
    SELECT 1 FROM leads 
    WHERE LOWER(TRIM(email)) = ? AND initial_email_sent_at IS NOT NULL
    LIMIT 1
    """, (clean,))
    res = cursor.fetchone() is not None
    conn.close()
    return res

def mark_lead_bounced(email, reason="Address not found / Mailbox unavailable"):
    return add_to_blacklist(email, reason=reason, source="IMAP_BOUNCE")

def get_leads_ready_for_initial_email(business_id=None, limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    # Strict deduplication & protection query:
    # 1. Email must be present and not empty
    # 2. Status must not be BOUNCED or BLACKLISTED
    # 3. Email must not be in email_blacklist
    # 4. Email must not have already received a cold email in outreach_logs
    # 5. Email must not have already been sent in another lead record
    # 6. GROUP BY email ensures zero duplicate emails in the same batch
    sql = """
    SELECT * FROM leads
    WHERE (status = 'AUDITED' OR (status = 'DISCOVERED' AND has_website = 0))
      AND email IS NOT NULL AND TRIM(email) != ''
      AND initial_email_sent_at IS NULL
      AND status NOT IN ('BOUNCED', 'BLACKLISTED')
      AND LOWER(TRIM(email)) NOT IN (SELECT LOWER(TRIM(email)) FROM email_blacklist)
      AND LOWER(TRIM(email)) NOT IN (
          SELECT LOWER(TRIM(recipient_email)) FROM outreach_logs WHERE status = 'SENT'
      )
      AND LOWER(TRIM(email)) NOT IN (
          SELECT LOWER(TRIM(l2.email)) FROM leads l2 
          WHERE l2.initial_email_sent_at IS NOT NULL AND l2.id != leads.id AND l2.email IS NOT NULL
      )
    """
    params = []
    if business_id:
        sql += " AND business_id = ?"
        params.append(business_id)

    sql += " GROUP BY LOWER(TRIM(email)) ORDER BY id ASC LIMIT ?"
    params.append(limit)

    cursor.execute(sql, tuple(params))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_leads_ready_for_followup(business_id=None, interval_days=3, max_followups=2):
    conn = get_connection()
    cursor = conn.cursor()
    cutoff_time = (datetime.utcnow() - timedelta(days=interval_days)).isoformat()
    
    # Exclude bounced, blacklisted, and leads whose email is in email_blacklist
    sql = """
    SELECT * FROM leads
    WHERE status IN ('SENT_INITIAL', 'FOLLOW_UP_1')
      AND follow_up_count < ?
      AND status NOT IN ('BOUNCED', 'BLACKLISTED', 'REPLIED', 'OPT_OUT')
      AND (
          (status = 'SENT_INITIAL' AND initial_email_sent_at <= ?)
          OR
          (status = 'FOLLOW_UP_1' AND last_follow_up_at <= ?)
      )
      AND LOWER(TRIM(email)) NOT IN (SELECT LOWER(TRIM(email)) FROM email_blacklist)
    """
    params = [max_followups, cutoff_time, cutoff_time]
    if business_id:
        sql += " AND business_id = ?"
        params.append(business_id)

    sql += " ORDER BY COALESCE(last_follow_up_at, initial_email_sent_at) ASC"

    cursor.execute(sql, tuple(params))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_overdue_followups(business_id=None, interval_days=3, max_followups=2):
    """
    Offline/Downtime Aware Calculator:
    Inspects all leads that have been sent an outreach email, calculates exact elapsed time,
    and returns leads that are overdue for follow-up (e.g. because the laptop was shut down).
    """
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow()

    sql = """
    SELECT id, business_name, email, city, country, niche, status,
           initial_email_sent_at, last_follow_up_at, follow_up_count, business_id
    FROM leads
    WHERE status IN ('SENT_INITIAL', 'FOLLOW_UP_1')
      AND follow_up_count < ?
      AND email IS NOT NULL AND TRIM(email) != ''
      AND status NOT IN ('BOUNCED', 'BLACKLISTED', 'REPLIED', 'OPT_OUT')
      AND LOWER(TRIM(email)) NOT IN (SELECT LOWER(TRIM(email)) FROM email_blacklist)
    """
    params = [max_followups]
    if business_id:
        sql += " AND business_id = ?"
        params.append(business_id)

    cursor.execute(sql, tuple(params))
    candidates = [dict(r) for r in cursor.fetchall()]
    conn.close()

    overdue_leads = []
    for lead in candidates:
        status = lead["status"]
        ref_time_str = lead["last_follow_up_at"] if status == "FOLLOW_UP_1" else lead["initial_email_sent_at"]
        if not ref_time_str:
            continue

        try:
            # Handle ISO string or space-separated timestamp
            clean_ts = ref_time_str.replace("Z", "").split("+")[0]
            if "T" in clean_ts:
                sent_dt = datetime.fromisoformat(clean_ts)
            else:
                sent_dt = datetime.strptime(clean_ts, "%Y-%m-%d %H:%M:%S")

            elapsed_seconds = (now - sent_dt).total_seconds()
            days_elapsed = elapsed_seconds / 86400.0

            if days_elapsed >= interval_days:
                lead["days_elapsed"] = round(days_elapsed, 1)
                lead["days_overdue"] = round(days_elapsed - interval_days, 1)
                lead["target_follow_up"] = (lead["follow_up_count"] or 0) + 1
                lead["reference_sent_at"] = ref_time_str
                overdue_leads.append(lead)
        except Exception:
            continue

    # Sort descending by days overdue (most urgent first)
    overdue_leads.sort(key=lambda x: x["days_elapsed"], reverse=True)
    return overdue_leads

def mark_initial_email_sent(lead_id, email=None):
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.utcnow().isoformat()
    if email:
        clean = email.strip().lower()
        # Mark all duplicate leads sharing this exact email address so none can receive a duplicate
        cursor.execute("""
        UPDATE leads
        SET status = 'SENT_INITIAL', initial_email_sent_at = ?, last_follow_up_at = ?
        WHERE LOWER(TRIM(email)) = ? OR id = ?
        """, (now_str, now_str, clean, lead_id))
    else:
        cursor.execute("""
        UPDATE leads
        SET status = 'SENT_INITIAL', initial_email_sent_at = ?, last_follow_up_at = ?
        WHERE id = ?
        """, (now_str, now_str, lead_id))
    conn.commit()
    conn.close()

def mark_followup_sent(lead_id, new_count):
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.utcnow().isoformat()
    status = f"FOLLOW_UP_{new_count}"
    cursor.execute("""
    UPDATE leads
    SET status = ?, follow_up_count = ?, last_follow_up_at = ?
    WHERE id = ?
    """, (status, new_count, now_str, lead_id))
    conn.commit()
    conn.close()

def log_outreach_event(lead_id, business_name, recipient_email, sender_email, pitch_type, subject, status="SENT", business_id="aloria_labs"):
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO outreach_logs (lead_id, business_name, recipient_email, sender_email, pitch_type, subject, status, sent_at, business_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (lead_id, business_name, recipient_email, sender_email, pitch_type, subject, status, now_str, business_id))
    conn.commit()
    conn.close()

def get_outreach_history(business_id=None, limit=50):
    conn = get_connection()
    cursor = conn.cursor()
    if business_id:
        cursor.execute("""
        SELECT * FROM outreach_logs WHERE business_id = ? ORDER BY id DESC LIMIT ?
        """, (business_id, limit))
    else:
        cursor.execute("""
        SELECT * FROM outreach_logs ORDER BY id DESC LIMIT ?
        """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_stats(business_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    base_cond = "WHERE business_id = ?" if business_id else ""
    params = (business_id,) if business_id else ()

    cursor.execute(f"SELECT count(*) as total, sum(has_website) as with_website, count(CASE WHEN has_website = 0 THEN 1 END) as without_website FROM leads {base_cond}", params)
    raw_row = cursor.fetchone()
    res: dict = dict(raw_row) if raw_row else {"total": 0, "with_website": 0, "without_website": 0}
    if res.get("with_website") is None:
        res["with_website"] = 0
    if res.get("without_website") is None:
        res["without_website"] = 0

    cursor.execute(f"SELECT status, count(*) as count FROM leads {base_cond} GROUP BY status", params)
    statuses: dict = {str(r['status']): int(r['count']) for r in cursor.fetchall()}

    log_cond = "WHERE business_id = ? AND status='SENT'" if business_id else "WHERE status='SENT'"
    cursor.execute(f"SELECT count(*) as count FROM outreach_logs {log_cond}", params)
    log_row = cursor.fetchone()
    res['total_emails_sent'] = int(log_row['count']) if log_row else 0
    conn.close()
    res['statuses'] = statuses
    return res

def get_funnel_stats(business_id=None):
    stats = get_stats(business_id)
    raw_statuses = stats.get("statuses")
    statuses: dict = raw_statuses if isinstance(raw_statuses, dict) else {}
    total = stats.get("total", 0)
    discovered = statuses.get("DISCOVERED", 0)
    audited = statuses.get("AUDITED", 0)
    pitch_sent = statuses.get("SENT_INITIAL", 0)
    follow_up_1 = statuses.get("FOLLOW_UP_1", 0)
    follow_up_2 = statuses.get("FOLLOW_UP_2", 0)
    replied = statuses.get("REPLIED", 0)
    golden_leads = stats.get("without_website", 0)
    emails_sent = stats.get("total_emails_sent", 0)

    return {
        "total": total,
        "discovered": discovered,
        "audited": audited,
        "pitch_sent": pitch_sent,
        "follow_up_1": follow_up_1,
        "follow_up_2": follow_up_2,
        "replied": replied,
        "golden_leads": golden_leads,
        "emails_sent": emails_sent
    }

def get_lead_ledger(business_id=None, limit=25):
    conn = get_connection()
    cursor = conn.cursor()
    if business_id:
        cursor.execute("""
        SELECT id, business_name, city, niche, has_website, email, status, follow_up_count,
               initial_email_sent_at, last_follow_up_at, created_at, business_id
        FROM leads
        WHERE business_id = ?
        ORDER BY id DESC
        LIMIT ?
        """, (business_id, limit))
    else:
        cursor.execute("""
        SELECT id, business_name, city, niche, has_website, email, status, follow_up_count,
               initial_email_sent_at, last_follow_up_at, created_at, business_id
        FROM leads
        ORDER BY id DESC
        LIMIT ?
        """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_recent_logs(business_id=None, limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    if business_id:
        cursor.execute("""
        SELECT id, lead_id, business_name, recipient_email, pitch_type, subject, status, sent_at
        FROM outreach_logs
        WHERE business_id = ?
        ORDER BY id DESC
        LIMIT ?
        """, (business_id, limit))
    else:
        cursor.execute("""
        SELECT id, lead_id, business_name, recipient_email, pitch_type, subject, status, sent_at
        FROM outreach_logs
        ORDER BY id DESC
        LIMIT ?
        """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
def get_leads_ready_for_whatsapp(business_id=None, limit=5):
    conn = get_connection()
    cursor = conn.cursor()
    if business_id:
        cursor.execute("""
        SELECT * FROM leads
        WHERE business_id = ?
          AND phone IS NOT NULL AND TRIM(phone) != ''
          AND (email IS NULL OR TRIM(email) = '' OR status = 'NO_EMAIL' OR status = 'AUDITED')
          AND (whatsapp_status IS NULL OR whatsapp_status = 'PENDING')
        ORDER BY id ASC
        LIMIT ?
        """, (business_id, limit))
    else:
        cursor.execute("""
        SELECT * FROM leads
        WHERE phone IS NOT NULL AND TRIM(phone) != ''
          AND (email IS NULL OR TRIM(email) = '' OR status = 'NO_EMAIL' OR status = 'AUDITED')
          AND (whatsapp_status IS NULL OR whatsapp_status = 'PENDING')
        ORDER BY id ASC
        LIMIT ?
        """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def mark_whatsapp_sent(lead_id, status="SENT"):
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    UPDATE leads
    SET whatsapp_status = ?, whatsapp_sent_at = ?
    WHERE id = ?
    """, (status, now_str, lead_id))
    conn.commit()
    conn.close()

def get_delivered_count(business_id="gethotelstays", channel="BOTH"):
    conn = get_connection()
    cursor = conn.cursor()
    if channel.upper() == "EMAIL":
        cursor.execute("SELECT COUNT(*) FROM leads WHERE business_id = ? AND initial_email_sent_at IS NOT NULL", (business_id,))
    elif channel.upper() == "WHATSAPP":
        cursor.execute("SELECT COUNT(*) FROM leads WHERE business_id = ? AND whatsapp_status = 'SENT'", (business_id,))
    else:
        cursor.execute("SELECT COUNT(*) FROM leads WHERE business_id = ? AND (initial_email_sent_at IS NOT NULL OR whatsapp_status = 'SENT')", (business_id,))
    res = cursor.fetchone()[0]
    conn.close()
    return res

def get_delivered_breakdown(business_id="gethotelstays"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM leads WHERE business_id = ? AND initial_email_sent_at IS NOT NULL", (business_id,))
    emails = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM leads WHERE business_id = ? AND whatsapp_status = 'SENT'", (business_id,))
    wa = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM leads WHERE business_id = ? AND (initial_email_sent_at IS NOT NULL OR whatsapp_status = 'SENT')", (business_id,))
    total_unique = cursor.fetchone()[0]
    conn.close()
    return {
        "emails_delivered": emails,
        "whatsapp_delivered": wa,
        "total_delivered": total_unique
    }

init_db()
