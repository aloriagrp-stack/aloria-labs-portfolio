import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__)))
import db

conn = db.get_connection()
c = conn.cursor()

c.execute("SELECT has_website, COUNT(*) FROM leads WHERE business_id='gethotelstays' AND status='DISCOVERED' GROUP BY has_website")
for r in c.fetchall():
    print("  has_website:", r[0], "Count:", r[1])

c.execute("SELECT status, has_website, COUNT(*) FROM leads WHERE business_id='gethotelstays' GROUP BY status, has_website")
for r in c.fetchall():
    print("  status:", r[0], "has_website:", r[1], "Count:", r[2])
