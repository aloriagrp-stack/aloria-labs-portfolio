import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__)))
import db

conn = db.get_connection()
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM leads WHERE business_id='gethotelstays'")
print("Total GHS leads in DB:", c.fetchone()[0])

c.execute("SELECT COUNT(*) FROM leads WHERE business_id='gethotelstays' AND email IS NOT NULL AND email != ''")
print("GHS leads with email:", c.fetchone()[0])

c.execute("SELECT COUNT(*) FROM leads WHERE business_id='gethotelstays' AND initial_email_sent_at IS NOT NULL")
print("GHS leads already sent:", c.fetchone()[0])

c.execute("SELECT status, COUNT(*) FROM leads WHERE business_id='gethotelstays' GROUP BY status")
for r in c.fetchall():
    print("  Status:", r[0], "Count:", r[1])

ready = db.get_leads_ready_for_initial_email("gethotelstays", limit=50)
print("Ready for initial right now:", len(ready))
for r in ready[:5]:
    print("  Ready:", r['business_name'], r['email'])

pending_audits = db.get_pending_audits("gethotelstays", limit=50)
print("Pending audits for GHS right now:", len(pending_audits))
