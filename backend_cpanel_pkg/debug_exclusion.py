import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__)))
import db

conn = db.get_connection()
c = conn.cursor()

c.execute("""
SELECT id, business_name, email, initial_email_sent_at, status 
FROM leads 
WHERE business_id='gethotelstays' AND status='AUDITED' AND email IS NOT NULL AND email != ''
LIMIT 10
""")
for r in c.fetchall():
    print(dict(r))

c.execute("""
SELECT COUNT(*)
FROM leads 
WHERE business_id='gethotelstays' AND status='AUDITED' AND email IS NOT NULL AND email != ''
  AND initial_email_sent_at IS NULL
""")
print("Audited with email and initial_email_sent_at IS NULL:", c.fetchone()[0])

c.execute("""
SELECT COUNT(*)
FROM leads 
WHERE business_id='gethotelstays' AND status='AUDITED' AND email IS NOT NULL AND email != ''
  AND initial_email_sent_at IS NULL
  AND LOWER(TRIM(email)) IN (SELECT LOWER(TRIM(recipient_email)) FROM outreach_logs WHERE status='SENT')
""")
print("Already in outreach_logs SENT:", c.fetchone()[0])
