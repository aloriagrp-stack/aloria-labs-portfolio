import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__)))
import db

conn = db.get_connection()
c = conn.cursor()
c.execute("SELECT COUNT(*), COUNT(email), COUNT(website_url) FROM leads WHERE business_id='gethotelstays'")
print("Total GHS leads, with email, with web:", c.fetchone())

c.execute("SELECT status, COUNT(*) FROM leads WHERE business_id='gethotelstays' GROUP BY status")
print("Status breakdown:", c.fetchall())

c.execute("SELECT COUNT(*) FROM leads WHERE business_id='gethotelstays' AND website_audit_done = 0")
print("Pending website audits:", c.fetchone())

c.execute("SELECT COUNT(*) FROM leads WHERE business_id='gethotelstays' AND status = 'DISCOVERED' AND email IS NOT NULL AND email != ''")
print("Discovered leads ready for initial email:", c.fetchone())
