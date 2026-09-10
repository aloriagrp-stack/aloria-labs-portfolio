import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "hunter.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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
    """)
    conn.commit()

    # Migration safety check for existing databases without business_id
    cursor.execute("PRAGMA table_info(leads)")
    lead_cols = [r["name"] for r in cursor.fetchall()]
    if "business_id" not in lead_cols:
        cursor.execute("ALTER TABLE leads ADD COLUMN business_id TEXT DEFAULT 'aloria_labs'")
        conn.commit()

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

def get_leads_ready_for_initial_email(business_id=None, limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    if business_id:
        cursor.execute("""
        SELECT * FROM leads
        WHERE (status = 'AUDITED' OR (status = 'DISCOVERED' AND has_website = 0))
          AND email IS NOT NULL AND email != ''
          AND initial_email_sent_at IS NULL
          AND business_id = ?
        LIMIT ?
        """, (business_id, limit))
    else:
        cursor.execute("""
        SELECT * FROM leads
        WHERE (status = 'AUDITED' OR (status = 'DISCOVERED' AND has_website = 0))
          AND email IS NOT NULL AND email != ''
          AND initial_email_sent_at IS NULL
        LIMIT ?
        """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_leads_ready_for_followup(business_id=None, interval_days=2, max_followups=2):
    conn = get_connection()
    cursor = conn.cursor()
    cutoff_time = (datetime.utcnow() - timedelta(days=interval_days)).isoformat()
    if business_id:
        cursor.execute("""
        SELECT * FROM leads
        WHERE status IN ('SENT_INITIAL', 'FOLLOW_UP_1')
          AND follow_up_count < ?
          AND business_id = ?
          AND (
              (status = 'SENT_INITIAL' AND initial_email_sent_at <= ?)
              OR
              (status = 'FOLLOW_UP_1' AND last_follow_up_at <= ?)
          )
        """, (max_followups, business_id, cutoff_time, cutoff_time))
    else:
        cursor.execute("""
        SELECT * FROM leads
        WHERE status IN ('SENT_INITIAL', 'FOLLOW_UP_1')
          AND follow_up_count < ?
          AND (
              (status = 'SENT_INITIAL' AND initial_email_sent_at <= ?)
              OR
              (status = 'FOLLOW_UP_1' AND last_follow_up_at <= ?)
          )
        """, (max_followups, cutoff_time, cutoff_time))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def mark_initial_email_sent(lead_id):
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.utcnow().isoformat()
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
    row = dict(cursor.fetchone() or {"total": 0, "with_website": 0, "without_website": 0})
    if row.get("with_website") is None:
        row["with_website"] = 0
    if row.get("without_website") is None:
        row["without_website"] = 0

    cursor.execute(f"SELECT status, count(*) as count FROM leads {base_cond} GROUP BY status", params)
    statuses = {r['status']: r['count'] for r in cursor.fetchall()}

    log_cond = "WHERE business_id = ? AND status='SENT'" if business_id else "WHERE status='SENT'"
    cursor.execute(f"SELECT count(*) as count FROM outreach_logs {log_cond}", params)
    row['total_emails_sent'] = cursor.fetchone()['count']
    conn.close()
    row['statuses'] = statuses
    return row

def get_funnel_stats(business_id=None):
    stats = get_stats(business_id)
    statuses = stats.get("statuses", {})
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
    return rows

init_db()
