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
        sent_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()

def insert_lead(business_name, country, city, niche, address=None, phone=None, rating=None, reviews_count=None, website_url=None):
    conn = get_connection()
    cursor = conn.cursor()
    has_website = 1 if (website_url and website_url.strip() and website_url.startswith("http")) else 0
    try:
        cursor.execute("""
        INSERT INTO leads (business_name, country, city, niche, address, phone, rating, reviews_count, has_website, website_url, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'DISCOVERED')
        """, (business_name, country, city, niche, address, phone, rating, reviews_count, has_website, website_url))
        conn.commit()
        lead_id = cursor.lastrowid
        conn.close()
        return lead_id
    except sqlite3.IntegrityError:
        conn.close()
        return None  # Duplicate already in database

def get_pending_audits(limit=20):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM leads WHERE status = 'DISCOVERED' AND has_website = 1 LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_no_website_leads(limit=20):
    conn = get_connection()
    cursor = conn.cursor()
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

def get_leads_ready_for_initial_email(limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    # Can send to either audited sites with an email, or businesses with no website if an email was discovered
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

def get_leads_ready_for_followup(interval_days=2, max_followups=2):
    conn = get_connection()
    cursor = conn.cursor()
    cutoff_time = (datetime.utcnow() - timedelta(days=interval_days)).isoformat()
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

def log_outreach_event(lead_id, business_name, recipient_email, sender_email, pitch_type, subject, status="SENT"):
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO outreach_logs (lead_id, business_name, recipient_email, sender_email, pitch_type, subject, status, sent_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (lead_id, business_name, recipient_email, sender_email, pitch_type, subject, status, now_str))
    conn.commit()
    conn.close()

def get_outreach_history(limit=50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM outreach_logs ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) as total, sum(has_website) as with_website, count(CASE WHEN has_website = 0 THEN 1 END) as without_website FROM leads")
    row = dict(cursor.fetchone())
    cursor.execute("SELECT status, count(*) as count FROM leads GROUP BY status")
    statuses = {r['status']: r['count'] for r in cursor.fetchall()}
    cursor.execute("SELECT count(*) as count FROM outreach_logs WHERE status='SENT'")
    row['total_emails_sent'] = cursor.fetchone()['count']
    conn.close()
    row['statuses'] = statuses
    return row

init_db()
