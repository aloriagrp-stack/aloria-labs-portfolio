import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import config
import db

def generate_pitch(lead, email_type="INITIAL"):
    name = lead["business_name"]
    city = lead["city"]
    niche = lead["niche"]
    has_website = lead["has_website"]
    audit = lead["audit_summary"] or ""

    if email_type == "INITIAL":
        if not has_website:
            subject = f"Quick question regarding {name}'s online presence in {city}"
            plain_text = f"""Hi {name} Team,

I came across {name} on Google Maps while researching top {niche} in {city}.

I noticed you currently don't have an official website or digital ordering/booking system listed. In today's market, customers searching on their phones often default to competitors that offer instant online reservations and digital menus.

At Aloria Labs, we build autonomous AI systems, modern websites, and private digital infrastructure for businesses. We can deploy a dedicated, high-performance web platform for {name} that handles customer reservations automatically without recurring platform cuts.

Would you be open to a quick 5-minute chat this week to see a live demo?

Best regards,

Shriyansh Aloria
Founder & Chief Systems Architect
Aloria Labs
Web: https://alorialabs.in
Email: info@alorialabs.in
Direct: +91 93184 85680
"""
            html_text = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #111; line-height: 1.6; max-width: 600px;">
  <p>Hi {name} Team,</p>
  <p>I came across <strong>{name}</strong> on Google Maps while researching top {niche} in {city}.</p>
  <p>I noticed you currently don't have an official website or digital ordering/booking system listed. In today's market, customers searching on their phones often default to competitors that offer instant online reservations and digital menus.</p>
  <p>At <strong>Aloria Labs</strong>, we build autonomous AI systems, modern websites, and private digital infrastructure for businesses. We can deploy a dedicated, high-performance web platform for {name} that handles customer reservations automatically without recurring third-party platform cuts.</p>
  <p>Would you be open to a quick 5-minute chat this week to see a live demo?</p>
  <br>
  <p style="margin-bottom: 2px;"><strong>Shriyansh Aloria</strong><br>
  <span style="color: #666; font-size: 0.9em;">Founder & Chief Systems Architect | Aloria Labs</span><br>
  <a href="https://alorialabs.in" style="color: #111; text-decoration: underline;">alorialabs.in</a> | +91 93184 85680
  </p>
</div>
"""
        else:
            subject = f"Technical observation regarding {name}'s website"
            plain_text = f"""Hi {name} Team,

I came across {name} in {city} and was inspecting your digital infrastructure.

During a technical audit of your site ({lead['website_url']}), our systems flagged a couple of areas:
- {audit}

These issues directly impact mobile customer conversion and search rankings. At Aloria Labs, we engineer high-speed autonomous web systems and AI workflow integrations with guaranteed 100% client code ownership.

Would you be open to a brief 5-minute call to see how we could optimize this for you?

Best regards,

Shriyansh Aloria
Founder & Chief Systems Architect
Aloria Labs
https://alorialabs.in
"""
            html_text = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #111; line-height: 1.6; max-width: 600px;">
  <p>Hi {name} Team,</p>
  <p>I came across <strong>{name}</strong> in {city} and was inspecting your digital infrastructure.</p>
  <p>During a technical audit of your site (<a href="{lead['website_url']}" style="color: #111;">{lead['website_url']}</a>), our automated systems flagged:</p>
  <ul style="color: #444;">
    <li>{audit}</li>
  </ul>
  <p>These issues directly impact mobile customer conversion and search rankings. At <strong>Aloria Labs</strong>, we engineer high-speed autonomous web systems and AI workflow integrations with guaranteed 100% client code ownership.</p>
  <p>Would you be open to a brief 5-minute call to see how we could optimize this for you?</p>
  <br>
  <p style="margin-bottom: 2px;"><strong>Shriyansh Aloria</strong><br>
  <span style="color: #666; font-size: 0.9em;">Founder & Chief Systems Architect | Aloria Labs</span><br>
  <a href="https://alorialabs.in" style="color: #111; text-decoration: underline;">alorialabs.in</a> | +91 93184 85680
  </p>
</div>
"""
    elif email_type == "FOLLOW_UP_1":
        subject = f"Re: Quick question regarding {name}'s online presence in {city}"
        plain_text = f"""Hi {name} Team,

Following up on my note from a couple of days ago.

We recently helped an enterprise partner automate their entire customer booking flow, cutting manual phone triage down to zero.

I'd love to share a quick 2-minute walkthrough tailored to {name}. Let me know if tomorrow or Thursday works for a brief chat.

Best,
Shriyansh Aloria
Aloria Labs | https://alorialabs.in
"""
        html_text = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #111; line-height: 1.6;">
  <p>Hi {name} Team,</p>
  <p>Following up on my note from a couple of days ago.</p>
  <p>We recently helped an enterprise partner automate their entire customer booking flow, cutting manual phone triage down to zero.</p>
  <p>I'd love to share a quick 2-minute walkthrough tailored to {name}. Let me know if tomorrow or Thursday works for a brief chat.</p>
  <br>
  <p><strong>Shriyansh Aloria</strong><br>Aloria Labs | <a href="https://alorialabs.in">alorialabs.in</a></p>
</div>
"""
    else:  # FOLLOW_UP_2 / Break-up
        subject = f"Re: Quick question regarding {name}'s online presence in {city}"
        plain_text = f"""Hi {name} Team,

I assume modernizing your digital presence isn't an active priority right now, which is completely understandable.

I won't follow up further. If you ever want to upgrade your website or deploy autonomous booking systems in the future, our door is always open: https://alorialabs.in

Wishing {name} continued success.

Best,
Shriyansh Aloria
Founder | Aloria Labs
"""
        html_text = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #111; line-height: 1.6;">
  <p>Hi {name} Team,</p>
  <p>I assume modernizing your digital presence isn't an active priority right now, which is completely understandable.</p>
  <p>I won't follow up further. If you ever want to upgrade your website or deploy autonomous booking systems in the future, our door is always open at <a href="https://alorialabs.in">alorialabs.in</a>.</p>
  <p>Wishing {name} continued success.</p>
  <br>
  <p><strong>Shriyansh Aloria</strong><br>Founder | Aloria Labs</p>
</div>
"""

    return subject, plain_text, html_text

def send_email_via_smtp(to_email, subject, plain_text, html_text):
    smtp_conf = config.get_smtp_config()
    sender_email = smtp_conf.get("email")
    password = smtp_conf.get("password")
    smtp_server = smtp_conf.get("smtp_server", "smtp.gmail.com")
    smtp_port = smtp_conf.get("smtp_port", 587)

    if not password:
        print("[!] Error: No SMTP password configured in smtp_config.json")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = f"Shriyansh Aloria — Aloria Labs <{sender_email}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Reply-To"] = "info@alorialabs.in"

    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_text, "html", "utf-8"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, password)
            server.sendmail(sender_email, [to_email], msg.as_string())
        return True
    except Exception as e:
        print(f"[!] SMTP sending failed for {to_email}: {e}")
        return False

def dispatch_initial_emails(limit=5):
    ready_leads = db.get_leads_ready_for_initial_email(limit=limit)
    print(f"\n[EMAIL ENGINE] Found {len(ready_leads)} leads ready for initial outreach...")

    sent_count = 0
    for lead in ready_leads:
        to_email = lead["email"]
        if not to_email:
            continue

        subject, plain, html = generate_pitch(lead, email_type="INITIAL")
        print(f"[DISPATCHING INITIAL] To: {to_email} | Subject: {subject}")

        success = send_email_via_smtp(to_email, subject, plain, html)
        if success:
            db.mark_initial_email_sent(lead["id"])
            print(f"  [+] Sent successfully to {lead['business_name']} ({to_email})")
            sent_count += 1
            # Rate limit delay between emails
            time.sleep(30)  # 30s delay in testing; can be set higher in config
        else:
            print(f"  [-] Failed to send to {to_email}")

    return sent_count

def dispatch_followups():
    ready_followups = db.get_leads_ready_for_followup(
        interval_days=config.FOLLOW_UP_INTERVAL_DAYS,
        max_followups=config.MAX_FOLLOW_UPS
    )
    print(f"\n[FOLLOW-UP ENGINE] Found {len(ready_followups)} leads ready for scheduled 2-day follow-up...")

    sent_count = 0
    for lead in ready_followups:
        to_email = lead["email"]
        curr_count = lead["follow_up_count"] or 0
        new_count = curr_count + 1
        email_type = f"FOLLOW_UP_{new_count}"

        subject, plain, html = generate_pitch(lead, email_type=email_type)
        print(f"[DISPATCHING {email_type}] To: {to_email} | Business: {lead['business_name']}")

        success = send_email_via_smtp(to_email, subject, plain, html)
        if success:
            db.mark_followup_sent(lead["id"], new_count)
            print(f"  [+] Follow-up {new_count} sent successfully to {to_email}")
            sent_count += 1
            time.sleep(30)

    return sent_count
