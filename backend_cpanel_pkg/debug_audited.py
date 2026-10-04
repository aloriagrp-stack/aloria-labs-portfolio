import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__)))
import db

conn = db.get_connection()
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM leads WHERE business_id='gethotelstays' AND status='AUDITED' AND email IS NOT NULL AND email != ''")
print("AUDITED leads with email:", c.fetchone()[0])

c.execute("SELECT COUNT(*) FROM leads WHERE business_id='gethotelstays' AND status='AUDITED' AND (email IS NULL OR email = '')")
print("AUDITED leads WITHOUT email:", c.fetchone()[0])
