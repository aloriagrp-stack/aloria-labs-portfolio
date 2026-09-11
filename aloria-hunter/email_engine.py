import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import config
import db
import ui

import business_manager

def generate_pitch(lead, email_type="INITIAL"):
    name = lead["business_name"]
    city = lead["city"]
    niche = lead["niche"]
    has_website = lead["has_website"]
    audit = (lead["audit_summary"] or "").lower()
    website_url = lead["website_url"] or ""
    biz_id = lead.get("business_id") or "aloria_labs"

    # Check if business has custom templates in business_manager
    biz = business_manager.get_business(biz_id)
    sender_name = biz.get("sender_display_name", "Shriyansh Aloria — Aloria Labs") if biz else "Shriyansh Aloria — Aloria Labs"

    if biz and "pitches" in biz:
        pitch_key = None
        if email_type == "INITIAL":
            pitch_key = "case_a_no_website" if not has_website else "case_b_audit"
        elif email_type == "FOLLOW_UP_1":
            pitch_key = "follow_up_1"
        elif email_type == "FOLLOW_UP_2":
            pitch_key = "follow_up_2"

        if pitch_key and pitch_key in biz["pitches"]:
            tpl = biz["pitches"][pitch_key]
            rating_val = lead.get("rating") or "4.5"
            reviews_val = lead.get("reviews_count") or "20+"
            flaws_text = lead.get("audit_summary") or "• Sub-optimal mobile responsiveness\n• Slower load times impacting Google rankings"

            subj = tpl.get("subject", "").format(
                business_name=name, city=city, niche=niche,
                rating=rating_val, reviews_count=reviews_val,
                website_url=website_url, sender_name=sender_name
            )
            body = tpl.get("body", "").format(
                business_name=name, city=city, niche=niche,
                rating=rating_val, reviews_count=reviews_val,
                website_url=website_url, sender_name=sender_name,
                flaws_bullet_points=flaws_text
            )
            html_body = f"""<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #111; line-height: 1.6; max-width: 600px; white-space: pre-line;">{body}</div>"""
            return subj, body, html_body

    if email_type == "INITIAL":
        if not has_website:

            # PITCH CATEGORY A: ZERO DIGITAL FOOTPRINT / NO WEBSITE
            subject = f"Question regarding {name}'s online reservations in {city}"
            plain_text = f"""Hi {name} Team,

I came across {name} on Google Maps while researching top-rated {niche} in {city}.

I noticed you currently don't have an official website or digital booking system listed. In today's market, customers searching on their phones frequently default to competitors who offer instant online menus and reservations.

At Aloria Labs, we engineer custom, high-speed digital infrastructure and web systems for premier businesses. We can deploy a dedicated, modern online reservation system for {name} that captures customer bookings directly without high third-party aggregator commissions.

Would you be open to a quick 5-minute chat this week to see a prototype tailored for {name}?

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
  <p>I came across <strong>{name}</strong> on Google Maps while researching top-rated {niche} in {city}.</p>
  <p>I noticed you currently don't have an official website or digital booking system listed. In today's market, customers searching on their phones frequently default to competitors who offer instant online menus and reservations.</p>
  <p>At <strong>Aloria Labs</strong>, we engineer custom, high-speed digital infrastructure and web systems for premier businesses. We can deploy a dedicated, modern online reservation system for {name} that captures customer bookings directly without high third-party aggregator commissions.</p>
  <p>Would you be open to a quick 5-minute chat this week to see a prototype tailored for {name}?</p>
  <br>
  <p style="margin-bottom: 2px;"><strong>Shriyansh Aloria</strong><br>
  <span style="color: #666; font-size: 0.9em;">Founder & Chief Systems Architect | Aloria Labs</span><br>
  <a href="https://alorialabs.in" style="color: #111; text-decoration: underline;">alorialabs.in</a> | +91 93184 85680
  </p>
</div>
"""
        elif "error" in audit or "500" in audit or "timed out" in audit:
            # PITCH CATEGORY B: SERVER DOWN / HTTP ERRORS
            subject = f"Urgent technical alert regarding {name}'s web server"
            plain_text = f"""Hi {name} Team,

I was inspecting digital infrastructure for top {niche} in {city} and came across {name}'s website ({website_url}).

Our technical scanner flagged that your server returned critical connection or HTTP errors. When this happens, potential guests and clients trying to visit your site encounter broken pages or timeouts, resulting in lost revenue.

At Aloria Labs, we architect zero-downtime, high-performance web systems and automated server health monitoring.

Would you be open to a brief 5-minute call so we can show you how to stabilize your infrastructure?

Best regards,

Shriyansh Aloria
Founder & Chief Systems Architect
Aloria Labs
https://alorialabs.in
"""
            html_text = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #111; line-height: 1.6; max-width: 600px;">
  <p>Hi {name} Team,</p>
  <p>I was inspecting digital infrastructure for top {niche} in {city} and came across <strong>{name}</strong>'s website (<a href="{website_url}" style="color: #111;">{website_url}</a>).</p>
  <p style="color: #b91c1c; font-weight: 500;">Our technical scanner flagged that your server is returning connection or HTTP error statuses. When this happens, potential guests trying to visit your site encounter broken pages or timeouts, directly impacting customer revenue.</p>
  <p>At <strong>Aloria Labs</strong>, we architect zero-downtime, high-performance web systems and automated server health monitoring.</p>
  <p>Would you be open to a brief 5-minute call so we can show you how to stabilize your infrastructure?</p>
  <br>
  <p style="margin-bottom: 2px;"><strong>Shriyansh Aloria</strong><br>
  <span style="color: #666; font-size: 0.9em;">Founder & Chief Systems Architect | Aloria Labs</span><br>
  <a href="https://alorialabs.in" style="color: #111; text-decoration: underline;">alorialabs.in</a> | +91 93184 85680
  </p>
</div>
"""
        elif "missing ssl" in audit or "non-secure" in audit:
            # PITCH CATEGORY C: SECURITY / MISSING SSL
            subject = f"Security notice regarding {name}'s website security certificate"
            plain_text = f"""Hi {name} Team,

While researching premier {niche} in {city}, I noticed {name}'s website ({website_url}) is missing an active SSL certificate (HTTP instead of HTTPS).

Modern browsers (Google Chrome, Safari) now show a prominent "Not Secure" warning to visitors on non-SSL sites, which deters guests from booking or trusting the site.

At Aloria Labs, we secure, modernize, and engineer high-performance web systems for growing businesses.

Would you be open to a quick 5-minute chat to discuss securing and modernizing your domain?

Best regards,

Shriyansh Aloria
Founder & Chief Systems Architect
Aloria Labs
https://alorialabs.in
"""
            html_text = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #111; line-height: 1.6; max-width: 600px;">
  <p>Hi {name} Team,</p>
  <p>While researching premier {niche} in {city}, I noticed <strong>{name}</strong>'s website (<a href="{website_url}" style="color: #111;">{website_url}</a>) is missing an active SSL certificate.</p>
  <p>Modern browsers like Chrome and Safari now display a prominent <strong>"Not Secure"</strong> warning to visitors on unencrypted domains, which immediately impacts customer trust and search engine rankings.</p>
  <p>At <strong>Aloria Labs</strong>, we secure, modernize, and engineer high-performance web systems for premier businesses.</p>
  <p>Would you be open to a quick 5-minute chat to discuss securing and modernizing your web presence?</p>
  <br>
  <p style="margin-bottom: 2px;"><strong>Shriyansh Aloria</strong><br>
  <span style="color: #666; font-size: 0.9em;">Founder & Chief Systems Architect | Aloria Labs</span><br>
  <a href="https://alorialabs.in" style="color: #111; text-decoration: underline;">alorialabs.in</a> | +91 93184 85680
  </p>
</div>
"""
        elif "mobile viewport" in audit:
            # PITCH CATEGORY D: MOBILE OPTIMIZATION
            subject = f"Mobile guest experience on {name}'s website"
            plain_text = f"""Hi {name} Team,

I came across {name} while looking at leading {niche} in {city}.

During a quick check of your website ({website_url}), our audit noted that the site isn't fully optimized for mobile viewports. Over 75% of guests search and book from their smartphones, and when a site doesn't fit mobile screens seamlessly, bounce rates skyrocket.

At Aloria Labs, we engineer responsive, lightning-fast mobile web applications and autonomous reservation systems.

Would you be open to a brief 5-minute call to see how a modern mobile experience could boost your conversions?

Best regards,

Shriyansh Aloria
Founder & Chief Systems Architect
Aloria Labs
https://alorialabs.in
"""
            html_text = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #111; line-height: 1.6; max-width: 600px;">
  <p>Hi {name} Team,</p>
  <p>I came across <strong>{name}</strong> while looking at leading {niche} in {city}.</p>
  <p>During a technical check of your website (<a href="{website_url}" style="color: #111;">{website_url}</a>), our audit noted that the layout lacks mobile viewport optimization. Over 75% of diners and guests now search from their mobile devices, and an unoptimized mobile view directly causes customers to leave.</p>
  <p>At <strong>Aloria Labs</strong>, we engineer responsive, ultra-fast mobile web applications and autonomous reservation systems.</p>
  <p>Would you be open to a brief 5-minute call to see how a modern mobile experience could increase your direct bookings?</p>
  <br>
  <p style="margin-bottom: 2px;"><strong>Shriyansh Aloria</strong><br>
  <span style="color: #666; font-size: 0.9em;">Founder & Chief Systems Architect | Aloria Labs</span><br>
  <a href="https://alorialabs.in" style="color: #111; text-decoration: underline;">alorialabs.in</a> | +91 93184 85680
  </p>
</div>
"""
        elif "booking" in audit or "order" in audit:
            # PITCH CATEGORY E: LACK OF AUTOMATED BOOKING
            subject = f"Direct online reservation system for {name}"
            plain_text = f"""Hi {name} Team,

I came across {name} in {city} and was admiring your reputation in the local {niche} space.

I noticed your website ({website_url}) doesn't feature a direct, automated online booking or reservation system. Today's customers expect instant booking confirmation, and businesses without direct systems often lose reservations to third-party apps that charge hefty commissions.

At Aloria Labs, we deploy custom, commission-free booking engines and private web portals tailored directly to your workflow.

Would you be open to a 5-minute demo to see how this could automate reservations for {name}?

Best regards,

Shriyansh Aloria
Founder & Chief Systems Architect
Aloria Labs
https://alorialabs.in
"""
            html_text = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #111; line-height: 1.6; max-width: 600px;">
  <p>Hi {name} Team,</p>
  <p>I came across <strong>{name}</strong> in {city} and was admiring your reputation in the local {niche} space.</p>
  <p>I noticed your website (<a href="{website_url}" style="color: #111;">{website_url}</a>) doesn't feature a direct, automated online reservation or booking system. Today's customers expect instant confirmation, and businesses without direct digital systems often lose revenue or pay high third-party aggregator commissions.</p>
  <p>At <strong>Aloria Labs</strong>, we deploy custom, commission-free booking engines and private web portals tailored directly to your brand.</p>
  <p>Would you be open to a 5-minute demo to see how this could automate direct bookings for {name}?</p>
  <br>
  <p style="margin-bottom: 2px;"><strong>Shriyansh Aloria</strong><br>
  <span style="color: #666; font-size: 0.9em;">Founder & Chief Systems Architect | Aloria Labs</span><br>
  <a href="https://alorialabs.in" style="color: #111; text-decoration: underline;">alorialabs.in</a> | +91 93184 85680
  </p>
</div>
"""
        else:
            # PITCH CATEGORY F: HEALTHY / FAST SITE -> AI & AUTOMATION PARTNERSHIP
            subject = f"AI workflows & automated systems for {name}"
            plain_text = f"""Hi {name} Team,

I came across {name} in {city} and inspected your digital presence ({website_url}). Your web infrastructure is fast and well-maintained.

At Aloria Labs, we help premier hospitality and service businesses integrate custom AI agents, automated guest triage, and intelligent workflow systems that operate 24/7 with zero manual overhead.

Would you be open to a brief 5-minute conversation to explore how AI automation could streamline operations for {name}?

Best regards,

Shriyansh Aloria
Founder & Chief Systems Architect
Aloria Labs
https://alorialabs.in
"""
            html_text = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #111; line-height: 1.6; max-width: 600px;">
  <p>Hi {name} Team,</p>
  <p>I came across <strong>{name}</strong> in {city} and inspected your digital presence (<a href="{website_url}" style="color: #111;">{website_url}</a>). Your web infrastructure is fast and well-maintained.</p>
  <p>At <strong>Aloria Labs</strong>, we help premier hospitality and service brands integrate custom AI agents, automated guest communication, and private workflow systems that operate 24/7 with zero manual overhead.</p>
  <p>Would you be open to a brief 5-minute conversation to explore how AI automation could streamline operations for {name}?</p>
  <br>
  <p style="margin-bottom: 2px;"><strong>Shriyansh Aloria</strong><br>
  <span style="color: #666; font-size: 0.9em;">Founder & Chief Systems Architect | Aloria Labs</span><br>
  <a href="https://alorialabs.in" style="color: #111; text-decoration: underline;">alorialabs.in</a> | +91 93184 85680
  </p>
</div>
"""
    elif email_type == "FOLLOW_UP_1":
        subject = f"Re: Digital infrastructure for {name}"
        plain_text = f"""Hi {name} Team,

Following up on my note from a couple of days ago regarding {name}'s digital infrastructure.

We recently helped an enterprise partner automate their entire customer booking flow, cutting manual phone triage down to zero and boosting direct revenue by 35%.

I'd love to share a quick 2-minute walkthrough tailored to {name}. Let me know if tomorrow or Thursday works for a brief chat.

Best regards,

Shriyansh Aloria
Founder & Chief Systems Architect | Aloria Labs
https://alorialabs.in
"""
        html_text = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #111; line-height: 1.6; max-width: 600px;">
  <p>Hi {name} Team,</p>
  <p>Following up on my note from a couple of days ago regarding <strong>{name}</strong>'s digital infrastructure.</p>
  <p>We recently helped an enterprise partner automate their entire customer booking flow, cutting manual phone triage down to zero and boosting direct reservations by 35%.</p>
  <p>I'd love to share a quick 2-minute walkthrough tailored to {name}. Let me know if tomorrow or Thursday works for a brief chat.</p>
  <br>
  <p style="margin-bottom: 2px;"><strong>Shriyansh Aloria</strong><br>
  <span style="color: #666; font-size: 0.9em;">Founder & Chief Systems Architect | Aloria Labs</span><br>
  <a href="https://alorialabs.in" style="color: #111; text-decoration: underline;">alorialabs.in</a>
  </p>
</div>
"""
    else:  # FOLLOW_UP_2
        subject = f"Last note: Automated systems for {name}"
        plain_text = f"""Hi {name} Team,

Final note from my side regarding {name}'s web systems.

I understand you're busy delivering great experiences to your guests. If modernizing your web platform or automating customer bookings isn't a priority right now, no worries at all.

If you ever want to streamline operations or deploy dedicated AI infrastructure in the future, feel free to reach out anytime.

Best of luck with {name}!

Shriyansh Aloria
Founder | Aloria Labs
https://alorialabs.in
"""
        html_text = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #111; line-height: 1.6; max-width: 600px;">
  <p>Hi {name} Team,</p>
  <p>Final note from my side regarding <strong>{name}</strong>'s web systems.</p>
  <p>I understand you're busy delivering great experiences to your guests. If modernizing your web platform or automating customer bookings isn't a priority right now, no worries at all.</p>
  <p>If you ever want to streamline operations or deploy dedicated AI infrastructure in the future, feel free to reach out anytime.</p>
  <p>Best of luck with {name}!</p>
  <br>
  <p><strong>Shriyansh Aloria</strong><br>Founder | Aloria Labs<br><a href="https://alorialabs.in">alorialabs.in</a></p>
</div>
"""

    return subject, plain_text, html_text

def send_email_via_smtp(to_email, subject, plain_text, html_text, profile_name=None):
    smtp_conf = config.get_smtp_config(profile_name)
    sender_email = smtp_conf.get("email")
    password = smtp_conf.get("password")
    smtp_server = smtp_conf.get("smtp_server", "smtp.gmail.com")
    smtp_port = smtp_conf.get("smtp_port", 587)
    sender_name = smtp_conf.get("sender_name", "Shriyansh Aloria — Aloria Labs")
    reply_to = smtp_conf.get("reply_to", "info@alorialabs.in")

    if not password:
        print(f"  {ui.C_RED}[!] Error: No password configured for sender profile ({sender_email}){ui.RESET}")
        return False, sender_email

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Reply-To"] = reply_to

    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_text, "html", "utf-8"))

    try:
        if int(smtp_port) == 465:
            import ssl
            ssl_ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_server, 465, context=ssl_ctx, timeout=20) as server:
                server.login(sender_email, password)
                server.sendmail(sender_email, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(smtp_server, int(smtp_port), timeout=20) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(sender_email, password)
                server.sendmail(sender_email, [to_email], msg.as_string())
        return True, sender_email
    except Exception as e:
        print(f"  {ui.C_RED}[!] SMTP error for {to_email}: {e}{ui.RESET}")
        return False, sender_email

def dispatch_initial_emails(limit=5, profile_name=None, business_id=None):
    ready_leads = db.get_leads_ready_for_initial_email(business_id=business_id, limit=limit)
    print(f"  {ui.C_MAGENTA}[⚡ EMAIL ENGINE]{ui.RESET} Found {ui.C_WHITE}{len(ready_leads)}{ui.RESET} verified leads ready for initial pitch...")

    sent_count = 0
    for lead in ready_leads:
        to_email = lead["email"]
        if not to_email:
            continue

        lead_biz = lead.get("business_id") or business_id or "aloria_labs"
        active_prof = profile_name
        if not active_prof:
            biz_data = business_manager.get_business(lead_biz)
            active_prof = biz_data.get("sender_profile") if biz_data else ("gethotelstays" if lead_biz == "gethotelstays" else "gmail")

        subject, plain, html = generate_pitch(lead, email_type="INITIAL")
        success, sender = send_email_via_smtp(to_email, subject, plain, html, active_prof)
        if success:
            db.mark_initial_email_sent(lead["id"])
            db.log_outreach_event(lead["id"], lead["business_name"], to_email, sender, "INITIAL", subject, "SENT", business_id=lead_biz)
            ui.log_email_dispatch(lead["business_name"], to_email, subject, True)
            sent_count += 1
            time.sleep(30)
        else:
            db.log_outreach_event(lead["id"], lead["business_name"], to_email, sender, "INITIAL", subject, "FAILED", business_id=lead_biz)
            ui.log_email_dispatch(lead["business_name"], to_email, subject, False, "SMTP Handshake Error")

    return sent_count

def dispatch_followups(profile_name=None, business_id=None):
    ready_followups = db.get_leads_ready_for_followup(
        business_id=business_id,
        interval_days=config.FOLLOW_UP_INTERVAL_DAYS,
        max_followups=config.MAX_FOLLOW_UPS
    )
    print(f"  {ui.C_MAGENTA}[⚡ FOLLOW-UP ENGINE]{ui.RESET} Found {ui.C_WHITE}{len(ready_followups)}{ui.RESET} leads ready for 2-day scheduled follow-up...")

    sent_count = 0
    for lead in ready_followups:
        to_email = lead["email"]
        curr_count = lead["follow_up_count"] or 0
        new_count = curr_count + 1
        email_type = f"FOLLOW_UP_{new_count}"
        lead_biz = lead.get("business_id") or business_id or "aloria_labs"
        active_prof = profile_name
        if not active_prof:
            biz_data = business_manager.get_business(lead_biz)
            active_prof = biz_data.get("sender_profile") if biz_data else ("gethotelstays" if lead_biz == "gethotelstays" else "gmail")

        subject, plain, html = generate_pitch(lead, email_type=email_type)
        success, sender = send_email_via_smtp(to_email, subject, plain, html, active_prof)
        if success:
            db.mark_followup_sent(lead["id"], new_count)
            db.log_outreach_event(lead["id"], lead["business_name"], to_email, sender, email_type, subject, "SENT", business_id=lead_biz)
            ui.log_email_dispatch(lead["business_name"], to_email, f"[Follow-up {new_count}] {subject}", True)
            sent_count += 1
            time.sleep(30)
        else:
            db.log_outreach_event(lead["id"], lead["business_name"], to_email, sender, email_type, subject, "FAILED", business_id=lead_biz)
            ui.log_email_dispatch(lead["business_name"], to_email, subject, False, "SMTP Error")

    return sent_count
