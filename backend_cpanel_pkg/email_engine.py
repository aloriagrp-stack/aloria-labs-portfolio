import smtplib
import time
import random
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from datetime import datetime
import config
import db
import ui
import email_verifier
import business_manager

_GHS_ROTATION_INDEX = 0
_ALORIA_ROTATION_INDEX = 0
_FAILED_AUTH_PROFILES = set()

def get_next_sender_profile(business_id="gethotelstays", requested_profile=None):
    """
    Multi-Sender Swarm Pool with Strict Delivered Quota:
    Automatically round-robins across ALL authenticated GetHotelStays sender accounts.
    Enforces that EACH sender account delivers exactly up to 50 emails per day.
    Only successfully DELIVERED emails are counted; accounts that reach 50 delivered
    are automatically paused/rested, allowing remaining accounts to finish their quota.
    """
    global _GHS_ROTATION_INDEX, _ALORIA_ROTATION_INDEX
    profiles, _ = config.list_smtp_profiles()
    max_quota = config.get_max_delivered_quota(business_id)

    # If a specific profile is requested (and not a generic pool flag)
    if requested_profile and requested_profile not in ["gethotelstays_pool", "aloria_pool", "pool", "auto"]:
        if requested_profile in profiles and profiles[requested_profile].get("password"):
            if requested_profile not in _FAILED_AUTH_PROFILES:
                s_email = profiles[requested_profile].get("email", "")
                delivered_today = db.get_sender_delivered_today(s_email, business_id=business_id)
                if delivered_today < max_quota:
                    return requested_profile
                else:
                    return None  # Requested account reached its daily delivered limit
        return requested_profile

    if business_id == "gethotelstays":
        # Find all valid GetHotelStays sender accounts that have passwords configured
        ghs_keys = [k for k in profiles.keys() if "gethotelstays" in k.lower() and profiles[k].get("password")]

        # Filter to only accounts that have delivered fewer than max_quota (50) emails today
        eligible_keys = []
        for k in ghs_keys:
            if k in _FAILED_AUTH_PROFILES:
                continue
            s_email = profiles[k].get("email", "")
            delivered_today = db.get_sender_delivered_today(s_email, business_id="gethotelstays")
            if delivered_today < max_quota:
                eligible_keys.append((k, delivered_today))

        if eligible_keys:
            chosen_key, _ = eligible_keys[_GHS_ROTATION_INDEX % len(eligible_keys)]
            _GHS_ROTATION_INDEX += 1
            return chosen_key
        else:
            # All configured GHS accounts reached 50 delivered emails daily quota
            return None
    else:
        # Aloria Labs accounts (strictly 100 delivered emails per account/day)
        aloria_keys = [k for k in profiles.keys() if "gethotelstays" not in k.lower() and profiles[k].get("password")]
        eligible_keys = []
        for k in aloria_keys:
            if k in _FAILED_AUTH_PROFILES:
                continue
            s_email = profiles[k].get("email", "")
            delivered_today = db.get_sender_delivered_today(s_email, business_id=business_id)
            if delivered_today < max_quota:
                eligible_keys.append((k, delivered_today))

        if eligible_keys:
            if "_ALORIA_ROTATION_INDEX" not in globals():
                _ALORIA_ROTATION_INDEX = 0
            chosen_key, _ = eligible_keys[_ALORIA_ROTATION_INDEX % len(eligible_keys)]
            _ALORIA_ROTATION_INDEX += 1
            return chosen_key
        else:
            # All configured Aloria Labs accounts reached 100 delivered emails daily quota
            return None

def get_adaptive_dispatch_delay():
    """Humanized random jitter pacing for high-speed inbox delivery without bot clustering."""
    mode = getattr(config, "PACING_MODE", "TURBO").upper()
    if mode == "TURBO":
        base = 8.0
        jitter = random.uniform(-2.0, 2.5)
    elif mode == "SAFE":
        base = 25.0
        jitter = random.uniform(-3.0, 3.0)
    else:  # BALANCED
        base = 14.0
        jitter = random.uniform(-3.0, 3.0)
    return max(4.0, base + jitter)

def generate_pitch(lead, email_type="INITIAL", sender_profile=None):
    name = lead["business_name"]
    city = lead["city"]
    niche = lead["niche"]
    has_website = lead["has_website"]
    audit = (lead["audit_summary"] or "").lower()
    website_url = lead["website_url"] or ""
    biz_id = lead.get("business_id") or "aloria_labs"
    is_hotel = any(h in (niche or "").lower() for h in ["hotel", "resort", "stay", "guest", "villa", "inn", "homestay", "hostel", "lodging"]) or "hotel" in (name or "").lower()
    is_golden_hotel = (not has_website) and is_hotel

    # For Golden Hotel Leads (Hotels with NO website): Always route to Aloria Labs Hotel Web Dev Pitch!
    if is_golden_hotel:
        biz_id = "aloria_labs"

    # For Aloria Labs (non-hotel golden leads): Use 500-problem intelligence library from Aloria Brain
    if biz_id == "aloria_labs" and not is_golden_hotel:
        try:
            import aloria_brain
            subj, body, html_body, meta = aloria_brain.generate_dynamic_email(lead, email_type)
            if subj and body:
                return subj, body, html_body
        except Exception as e:
            print(f"  [!] Aloria Brain error: {e}, falling back to default.")

    # Check if business has custom templates in business_manager (e.g. GetHotelStays or Aloria Labs)
    biz = business_manager.get_business(biz_id)
    sender_name = biz.get("sender_display_name", "Shriyansh Aloria — Aloria Labs") if biz else "Shriyansh Aloria — Aloria Labs"
    sender_prof = sender_profile or (biz.get("sender_profile") if biz else "gmail")
    smtp_cfg = config.get_smtp_config(sender_prof)
    sender_email = smtp_cfg.get("email", "info@alorialabs.in")

    if biz and "pitches" in biz:
        tpl = None
        if is_golden_hotel and "hotel_no_website" in biz["pitches"]:
            h_tpl = biz["pitches"]["hotel_no_website"]
            if email_type == "INITIAL":
                tpl = h_tpl
            elif email_type == "FOLLOW_UP_1":
                tpl = h_tpl.get("follow_up_1")
            elif email_type == "FOLLOW_UP_2":
                tpl = h_tpl.get("follow_up_2")
        else:
            pitch_key = None
            if email_type == "INITIAL":
                pitch_key = "case_a_no_website" if not has_website else "case_b_audit"
            elif email_type == "FOLLOW_UP_1":
                pitch_key = "follow_up_1"
            elif email_type == "FOLLOW_UP_2":
                pitch_key = "follow_up_2"

            if pitch_key and pitch_key in biz["pitches"]:
                tpl = biz["pitches"][pitch_key]

        if tpl:
            rating_val = lead.get("rating") or "4.5"
            reviews_val = lead.get("reviews_count") or "20+"
            flaws_text = lead.get("audit_summary") or "• Sub-optimal mobile responsiveness\n• Slower load times impacting Google rankings"

            fmt_kwargs = {
                "business_name": name or "",
                "city": city or "",
                "niche": niche or "",
                "rating": rating_val,
                "reviews_count": reviews_val,
                "website_url": website_url or "",
                "sender_name": sender_name or "",
                "sender_email": sender_email or "",
                "flaws_bullet_points": flaws_text or ""
            }
            raw_subj = tpl.get("subject", "")
            raw_body = tpl.get("body", "")
            try:
                subj = raw_subj.format(**fmt_kwargs)
            except Exception:
                subj = raw_subj
            try:
                body = raw_body.format(**fmt_kwargs)
            except Exception:
                body = raw_body

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

def send_email_via_smtp(to_email, subject, plain_text, html_text, profile_name=None, in_reply_to=None, references=None, out_msg_id_holder=None):
    smtp_conf = config.get_smtp_config(profile_name)
    sender_email = str(smtp_conf.get("email") or "alorialabs@gmail.com")
    password = (smtp_conf.get("password") or "").replace(" ", "").strip()
    smtp_server = str(smtp_conf.get("smtp_server") or "smtp.gmail.com")
    smtp_port = int(smtp_conf.get("smtp_port") or 587)
    sender_name = str(smtp_conf.get("sender_name") or "Shriyansh Aloria — Aloria Labs")
    reply_to = str(smtp_conf.get("reply_to") or "info@alorialabs.in")

    if not password:
        print(f"  {ui.C_RED}[!] Error: No password configured for sender profile ({sender_email}){ui.RESET}")
        return False, sender_email

    msg = MIMEMultipart("alternative")
    sender_domain = sender_email.split("@")[-1] if "@" in sender_email else "alorialabs.in"
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Reply-To"] = reply_to
    msg["Date"] = formatdate(localtime=True)
    msg_id = make_msgid(domain=sender_domain)
    msg["Message-ID"] = msg_id
    if out_msg_id_holder is not None and isinstance(out_msg_id_holder, list):
        out_msg_id_holder.append(msg_id)

    # Thread continuity headers for follow-ups
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    if references:
        msg["References"] = references

    msg["X-Mailer"] = "Aloria-Autonomous-Outreach/3.0"

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
    except smtplib.SMTPAuthenticationError:
        if profile_name:
            _FAILED_AUTH_PROFILES.add(profile_name)
        print(f"  {ui.C_YELLOW}[ℹ️ ACCOUNT PAUSED]{ui.RESET} {sender_email} credentials need update. Account paused for today.")
        return False, sender_email
    except smtplib.SMTPRecipientsRefused as e:
        err_msg = str(e)[:120]
        print(f"  {ui.C_RED}[🛡 RECIPIENT REJECTED - AUTO-BLACKLISTED]{ui.RESET} {to_email}: {err_msg}")
        db.add_to_blacklist(to_email, reason=f"SMTP Recipient Refused: {err_msg}", source="SMTP_DISPATCH")
        return False, sender_email
    except Exception as e:
        err_str = str(e)
        if "535" in err_str or "BadCredentials" in err_str or "Username and Password not accepted" in err_str:
            if profile_name:
                _FAILED_AUTH_PROFILES.add(profile_name)
            print(f"  {ui.C_YELLOW}[ℹ️ ACCOUNT PAUSED]{ui.RESET} {sender_email} credentials need update. Account paused for today.")
        elif any(code in err_str for code in ["550", "551", "552", "553", "554", "Recipient address rejected", "User unknown", "Mailbox unavailable", "does not exist"]):
            print(f"  {ui.C_RED}[🛡 RECIPIENT REJECTED - AUTO-BLACKLISTED]{ui.RESET} {to_email}: {err_str[:80]}")
            db.add_to_blacklist(to_email, reason=f"SMTP Error: {err_str[:80]}", source="SMTP_DISPATCH")
        else:
            print(f"  {ui.C_YELLOW}[!] Dispatch skipped for {to_email}: {err_str[:80]}{ui.RESET}")
        return False, sender_email

def send_single_initial_email(lead, profile_name=None, business_id=None, seen_in_batch=None):
    """
    Sends an initial Day 0 cold pitch to a single lead with strict safety gates.
    Returns (success_bool, status_str).
    """
    to_email = (lead.get("email") or "").strip().lower()
    if not to_email:
        return False, "EMPTY_EMAIL"

    if seen_in_batch is not None:
        if to_email in seen_in_batch:
            print(f"  {ui.C_YELLOW}[🛡 SKIPPED DEDUPLICATION]{ui.RESET} {to_email} already processed in current batch. Skipping.")
            return False, "DEDUPLICATED"
        seen_in_batch.add(to_email)

    lead_biz = lead.get("business_id") or business_id or "aloria_labs"
    is_lead_hotel = any(h in (lead.get("niche") or "").lower() for h in ["hotel", "resort", "stay", "guest", "villa", "inn", "homestay", "hostel", "lodging"]) or "hotel" in (lead.get("business_name") or "").lower()
    if not lead.get("has_website") and is_lead_hotel:
        lead_biz = "aloria_labs"

    import super_intelligence
    # SUPER INTELLIGENCE GATE: Reject junk aggregator ads, spam traps, or system pages
    biz_name = lead.get("business_name") or ""
    name_ok, clean_biz_name, name_rej = super_intelligence.sanitize_and_validate_business_name(biz_name)
    if not name_ok:
        print(f"  {ui.C_RED}[🛡 SUPER INTELLIGENCE BLOCKED JUNK LEAD]{ui.RESET} '{biz_name}' rejected: {name_rej}")
        db.mark_lead_invalid(lead["id"], reason=f"Super Intelligence: {name_rej}")
        return False, "JUNK_ENTITY"
    lead["business_name"] = clean_biz_name

    em_ok, clean_to_email, em_rej = super_intelligence.validate_email_super_intelligence(to_email, check_mx=False)
    if not em_ok:
        print(f"  {ui.C_RED}[🛡 SUPER INTELLIGENCE BLOCKED SPAM TRAP]{ui.RESET} '{to_email}' rejected: {em_rej}")
        db.add_to_blacklist(to_email, reason=f"Super Intelligence: {em_rej}", source="SUPER_INTEL_GATE")
        db.mark_lead_invalid(lead["id"], reason=f"Super Intelligence: {em_rej}")
        return False, "SPAM_TRAP"
    to_email = clean_to_email

    # STRICT PROTECTION CHECK 1: Never email a blacklisted, replied, or already contacted address
    if db.is_email_blacklisted(to_email):
        print(f"  {ui.C_RED}[🛡 SKIPPED BLACKLIST]{ui.RESET} {to_email} is on permanent blacklist. Skipping.")
        return False, "BLACKLISTED"

    if db.is_email_or_domain_replied(to_email):
        print(f"  {ui.C_YELLOW}[🛡 SKIPPED: PREVIOUS REPLIED ENTITY]{ui.RESET} {to_email} or its domain has already replied. Pitch cancelled.")
        return False, "ALREADY_REPLIED"

    if db.is_email_already_contacted(to_email, lead_biz):
        print(f"  {ui.C_YELLOW}[🛡 SKIPPED DEDUPLICATION]{ui.RESET} {to_email} already received outreach. Skipping.")
        return False, "ALREADY_CONTACTED"

    # ZERO-BOUNCE PRE-SEND VERIFICATION GATE:
    is_deliverable, valid_em, fail_reason = email_verifier.verify_email_deliverability(to_email, check_mx=True)
    if not is_deliverable:
        print(f"  {ui.C_RED}[🛡 BOUNCE HAZARD BLOCKED]{ui.RESET} {to_email} rejected: {fail_reason}. Auto-blacklisted.")
        db.add_to_blacklist(to_email, reason=f"Pre-send filter: {fail_reason}", source="PRE_SEND_GATE")
        db.mark_lead_invalid(lead["id"], reason=f"Pre-send filter: {fail_reason}")
        return False, "BOUNCE_HAZARD"

    active_prof = get_next_sender_profile(lead_biz, requested_profile=profile_name)
    max_q = config.get_max_delivered_quota(lead_biz)
    if active_prof is None:
        print(f"\n{ui.C_CYAN}  ╔═══════════════════════════════════════════════════════════════════════════════════════╗{ui.RESET}")
        print(f"  {ui.C_GREEN}║             ⭐ AAJ KA DAILY EMAIL OUTREACH QUOTA COMPLETE HO GAYA!                     ║{ui.RESET}")
        print(f"  {ui.C_CYAN}╠═══════════════════════════════════════════════════════════════════════════════════════╣{ui.RESET}")
        print(f"  {ui.C_WHITE}║  Sabhi active accounts ne apna {max_q}-email daily delivered quota poora kar liya hai.     ║{ui.RESET}")
        print(f"  {ui.C_YELLOW}║  Ab agle din raat 12:00 baje ke baad (new calendar day) fresh hunt try karein.        ║{ui.RESET}")
        print(f"  {ui.C_CYAN}╚═══════════════════════════════════════════════════════════════════════════════════════╝{ui.RESET}\n")
        return False, "QUOTA_EXHAUSTED"

    subject, plain, html = generate_pitch(lead, email_type="INITIAL", sender_profile=active_prof)
    msg_id_holder = []
    success, sender = send_email_via_smtp(valid_em or to_email, subject, plain, html, active_prof, out_msg_id_holder=msg_id_holder)
    if success:
        sent_msg_id = msg_id_holder[0] if msg_id_holder else None
        db.mark_initial_email_sent(
            lead["id"],
            email=to_email,
            sender_email=sender,
            sender_profile=active_prof,
            subject=subject,
            msg_id=sent_msg_id
        )
        db.log_outreach_event(lead["id"], lead["business_name"], to_email, sender, "INITIAL", subject, "SENT", business_id=lead_biz)
        del_today = db.get_sender_delivered_today(sender, business_id=lead_biz)
        ui.log_email_dispatch(lead["business_name"], to_email, subject, True, sender=f"{sender} [{del_today}/{max_q} Delivered Today]")
        delay = get_adaptive_dispatch_delay()
        time.sleep(delay)
        return True, "SENT"
    else:
        db.log_outreach_event(lead["id"], lead["business_name"], to_email, sender, "INITIAL", subject, "FAILED", business_id=lead_biz)
        ui.log_email_dispatch(lead["business_name"], to_email, subject, False, "SMTP Handshake Error", sender=sender)
        return False, "SMTP_ERROR"

def send_single_followup_email(lead, profile_name=None, business_id=None):
    """
    Sends a scheduled follow-up email to a single lead with strict safety gates:
    1. REPLY GUARD: If lead or corporate domain has EVER replied, permanently halts follow-up.
    2. SENDER CONTINUITY LOCK: Follow-up is strictly locked to the EXACT SAME sender account that sent the initial pitch.
    3. IN-THREAD DELIVERY: Preserves 'Re: {Subject}', 'In-Reply-To', and 'References' headers so follow-ups look 100% natural.
    """
    to_email = (lead.get("email") or "").strip().lower()
    if not to_email:
        return False, "EMPTY_EMAIL"

    import super_intelligence
    biz_name = lead.get("business_name") or ""
    name_ok, clean_biz_name, name_rej = super_intelligence.sanitize_and_validate_business_name(biz_name)
    if not name_ok:
        print(f"  {ui.C_RED}[🛡 SUPER INTELLIGENCE BLOCKED JUNK LEAD]{ui.RESET} '{biz_name}' follow-up rejected: {name_rej}")
        db.mark_lead_invalid(lead["id"], reason=f"Super Intelligence: {name_rej}")
        return False, "JUNK_ENTITY"
    lead["business_name"] = clean_biz_name

    em_ok, clean_to_email, em_rej = super_intelligence.validate_email_super_intelligence(to_email, check_mx=False)
    if not em_ok:
        print(f"  {ui.C_RED}[🛡 SUPER INTELLIGENCE BLOCKED SPAM TRAP]{ui.RESET} '{to_email}' follow-up rejected: {em_rej}")
        db.add_to_blacklist(to_email, reason=f"Super Intelligence: {em_rej}", source="SUPER_INTEL_GATE")
        db.mark_lead_invalid(lead["id"], reason=f"Super Intelligence: {em_rej}")
        return False, "SPAM_TRAP"
    to_email = clean_to_email

    # SECURITY GATE 1: REPLY SHIELD (Never follow up if lead has replied or opted out)
    if lead.get("status") in ["REPLIED", "OPT_OUT", "BLACKLISTED"]:
        print(f"  {ui.C_YELLOW}[🛡 FOLLOW-UP HALTED: REPLIED LEAD]{ui.RESET} '{lead.get('business_name')}' ({to_email}) already replied (status={lead.get('status')}). Follow-up cancelled.")
        return False, "ALREADY_REPLIED"

    if db.is_email_or_domain_replied(to_email):
        print(f"  {ui.C_YELLOW}[🛡 FOLLOW-UP HALTED: REPLIED INBOX]{ui.RESET} {to_email} or its domain has already replied. Marking REPLIED and halting.")
        db.mark_lead_replied(lead_id=lead["id"], email=to_email)
        return False, "ALREADY_REPLIED"

    # Blacklist check: never follow up on bounced/blacklisted inboxes
    if db.is_email_blacklisted(to_email) or lead.get("status") == "BOUNCED":
        print(f"  {ui.C_RED}[🛡 SKIPPED BOUNCED]{ui.RESET} {to_email} was flagged as bounced. Follow-up cancelled.")
        return False, "BOUNCED"

    # ZERO-BOUNCE PRE-SEND VERIFICATION GATE:
    is_deliverable, valid_em, fail_reason = email_verifier.verify_email_deliverability(to_email, check_mx=True)
    if not is_deliverable:
        print(f"  {ui.C_RED}[🛡 BOUNCE HAZARD BLOCKED]{ui.RESET} {to_email} rejected: {fail_reason}. Auto-blacklisted.")
        db.add_to_blacklist(to_email, reason=f"Pre-send filter: {fail_reason}", source="PRE_SEND_GATE")
        db.mark_lead_invalid(lead["id"], reason=f"Pre-send filter: {fail_reason}")
        return False, "BOUNCE_HAZARD"

    curr_count = lead.get("follow_up_count") or 0
    new_count = curr_count + 1
    email_type = f"FOLLOW_UP_{new_count}"
    lead_biz = lead.get("business_id") or business_id or "aloria_labs"
    is_lead_hotel = any(h in (lead.get("niche") or "").lower() for h in ["hotel", "resort", "stay", "guest", "villa", "inn", "homestay", "hostel", "lodging"]) or "hotel" in (lead.get("business_name") or "").lower()
    if not lead.get("has_website") and is_lead_hotel:
        lead_biz = "aloria_labs"

    max_q = config.get_max_delivered_quota(lead_biz)

    # SECURITY GATE 2: SENDER ACCOUNT CONTINUITY LOCK
    # Retrieves the EXACT sender account that sent the initial pitch to this lead
    assigned_data = db.get_lead_assigned_sender(lead["id"]) or {}
    orig_sender_email = assigned_data.get("assigned_sender_email")
    orig_profile_key = assigned_data.get("assigned_sender_profile")
    orig_subject = assigned_data.get("initial_subject")
    orig_msg_id = assigned_data.get("initial_msg_id")

    if not orig_profile_key and orig_sender_email:
        orig_profile_key = config.find_profile_key_by_email(orig_sender_email)

    if orig_profile_key:
        active_prof = orig_profile_key
    else:
        # Fallback to requested profile or default business profile
        active_prof = profile_name or ("gethotelstays" if lead_biz == "gethotelstays" else "gmail")

    prof_conf = config.get_smtp_config(active_prof)
    sender_account_email = str(prof_conf.get("email") or orig_sender_email or "")

    # Daily Quota Guard for the assigned account
    del_today = db.get_sender_delivered_today(sender_account_email, business_id=lead_biz)
    if del_today >= max_q:
        print(f"  {ui.C_YELLOW}[🔒 SENDER CONSISTENCY GUARD]{ui.RESET} Follow-up for '{lead.get('business_name')}' is locked to '{sender_account_email}', but this account has completed its daily quota ({del_today}/{max_q}). Postponing follow-up until next cycle to preserve sender authenticity!")
        return False, "SENDER_QUOTA_EXHAUSTED"

    # Time calculation logging (offline downtime awareness)
    interval_days = getattr(config, "FOLLOW_UP_INTERVAL_DAYS", 3)
    ref_ts = lead.get("last_follow_up_at") or lead.get("initial_email_sent_at")
    elapsed_str = ""
    if ref_ts:
        try:
            now = datetime.utcnow()
            clean_ts = ref_ts.replace("Z", "").split("+")[0]
            sent_dt = datetime.fromisoformat(clean_ts) if "T" in clean_ts else datetime.strptime(clean_ts, "%Y-%m-%d %H:%M:%S")
            days_elapsed = (now - sent_dt).total_seconds() / 86400.0
            days_overdue = max(0.0, days_elapsed - interval_days)
            if days_overdue > 0.3:
                elapsed_str = f" [Sent {days_elapsed:.1f}d ago | {days_overdue:.1f}d overdue (Laptop was offline)]"
            else:
                elapsed_str = f" [Sent {days_elapsed:.1f}d ago | Exactly on schedule]"
        except Exception:
            pass

    subject, plain, html = generate_pitch(lead, email_type=email_type, sender_profile=active_prof)

    # Thread continuity: Format subject as 'Re: {original_subject}'
    if orig_subject and not orig_subject.lower().startswith("re:"):
        thread_subject = f"Re: {orig_subject}"
    elif orig_subject:
        thread_subject = orig_subject
    else:
        thread_subject = subject

    msg_id_holder = []
    success, sender = send_email_via_smtp(
        valid_em or to_email,
        thread_subject,
        plain,
        html,
        active_prof,
        in_reply_to=orig_msg_id,
        references=orig_msg_id,
        out_msg_id_holder=msg_id_holder
    )
    if success:
        db.mark_followup_sent(lead["id"], new_count)
        db.log_outreach_event(lead["id"], lead["business_name"], to_email, sender, email_type, thread_subject, "SENT", business_id=lead_biz)
        del_today = db.get_sender_delivered_today(sender, business_id=lead_biz)
        ui.log_email_dispatch(lead["business_name"], to_email, f"[Follow-up {new_count}{elapsed_str}] {thread_subject}", True, sender=f"{sender} [{del_today}/{max_q} Delivered Today]")
        delay = get_adaptive_dispatch_delay()
        time.sleep(delay)
        return True, "SENT"
    else:
        db.log_outreach_event(lead["id"], lead["business_name"], to_email, sender, email_type, thread_subject, "FAILED", business_id=lead_biz)
        ui.log_email_dispatch(lead["business_name"], to_email, thread_subject, False, "SMTP Error", sender=sender)
        return False, "SMTP_ERROR"

def run_pre_dispatch_inbox_audit():
    """
    Executes a pre-flight scan of all sender inboxes before dispatching an outreach wave.
    Ensures any fresh incoming reply or bounce across all 11 accounts is caught,
    registered in replied_contacts, and barred from receiving follow-ups.
    """
    try:
        from agents.sentinel_agent import HotelSentinelAgent
        sentinel = HotelSentinelAgent()
        print(f"  {ui.C_CYAN}[🛡️ PRE-DISPATCH SENTINEL]{ui.RESET} Verifying inboxes for new replies & bounces across all accounts...")
        sentinel.execute_inbox_scan()
    except Exception as e:
        print(f"  {ui.C_YELLOW}[⚠️ PRE-DISPATCH SENTINEL WARNING]{ui.RESET} Inbox pre-scan skipped: {e}")

def dispatch_initial_emails(limit=10, profile_name=None, business_id=None):
    run_pre_dispatch_inbox_audit()
    ready_leads = db.get_leads_ready_for_initial_email(business_id=business_id, limit=limit)
    print(f"  {ui.C_MAGENTA}[⚡ EMAIL ENGINE]{ui.RESET} Found {ui.C_WHITE}{len(ready_leads)}{ui.RESET} verified leads ready for initial pitch...")

    sent_count = 0
    seen_in_batch = set()
    for lead in ready_leads:
        if sent_count >= limit:
            break
        success, reason = send_single_initial_email(
            lead,
            profile_name=profile_name,
            business_id=business_id,
            seen_in_batch=seen_in_batch
        )
        if success:
            sent_count += 1
        elif reason == "QUOTA_EXHAUSTED":
            break

    return sent_count

def dispatch_followups(profile_name=None, business_id=None, limit=None):
    run_pre_dispatch_inbox_audit()
    interval_days = getattr(config, "FOLLOW_UP_INTERVAL_DAYS", 3)
    ready_followups = db.get_leads_ready_for_followup(
        business_id=business_id,
        interval_days=interval_days,
        max_followups=config.MAX_FOLLOW_UPS
    )
    cap_text = f" (Cap: {limit})" if limit is not None else ""
    print(f"  {ui.C_MAGENTA}[⚡ FOLLOW-UP ENGINE]{ui.RESET} Found {ui.C_WHITE}{len(ready_followups)}{ui.RESET} leads ready for {interval_days}-day scheduled follow-up{cap_text}...")

    sent_count = 0
    for lead in ready_followups:
        if limit is not None and sent_count >= limit:
            print(f"  {ui.C_CYAN}[⚡ FOLLOW-UP LIMIT REACHED]{ui.RESET} Sent {sent_count} follow-up batch successfully.")
            break
        success, reason = send_single_followup_email(
            lead,
            profile_name=profile_name,
            business_id=business_id
        )
        if success:
            sent_count += 1
        elif reason == "QUOTA_EXHAUSTED":
            break

    return sent_count

def dispatch_interleaved_wave(limit=5, followup_limit=None, profile_name=None, business_id=None, on_step=None):
    """
    Balanced Interleaved Outreach Dispatcher:
    Alternates sending newly audited leads (INITIAL Day 0 pitches) and overdue follow-ups
    in a 1-to-1 interleaved cadence until quotas or limits are reached.
    Guarantees new leads are contacted immediately while follow-ups continue smoothly.
    """
    run_pre_dispatch_inbox_audit()
    effective_fu_limit = followup_limit if followup_limit is not None else limit
    ready_initial = db.get_leads_ready_for_initial_email(business_id=business_id, limit=limit)
    interval_days = getattr(config, "FOLLOW_UP_INTERVAL_DAYS", 3)
    ready_fu = db.get_leads_ready_for_followup(
        business_id=business_id,
        interval_days=interval_days,
        max_followups=config.MAX_FOLLOW_UPS
    )

    print(f"\n  {ui.C_MAGENTA}[⚡ BALANCED INTERLEAVED DISPATCH]{ui.RESET} Starting balanced outreach...")
    print(f"    * Fresh Leads Queue:      {ui.C_GREEN}{len(ready_initial)}{ui.RESET} (Target: {limit})")
    print(f"    * Overdue Follow-ups Queue: {ui.C_CYAN}{len(ready_fu)}{ui.RESET} (Target: {effective_fu_limit})")

    initial_sent = 0
    fu_sent = 0
    init_idx = 0
    fu_idx = 0
    seen_in_batch = set()

    while (init_idx < len(ready_initial) and initial_sent < limit) or (fu_idx < len(ready_fu) and fu_sent < effective_fu_limit):
        # 1. Dispatch 1 Fresh Lead
        if init_idx < len(ready_initial) and initial_sent < limit:
            lead = ready_initial[init_idx]
            init_idx += 1
            ok, reason = send_single_initial_email(
                lead,
                profile_name=profile_name,
                business_id=business_id,
                seen_in_batch=seen_in_batch
            )
            if ok:
                initial_sent += 1
                if on_step:
                    on_step(f"Cold pitch dispatched to '{lead.get('business_name')}' ({lead.get('email')}) ✓")
            elif reason == "QUOTA_EXHAUSTED":
                if on_step:
                    on_step("Daily swarm delivered quota reached. Pausing dispatch until next cycle.")
                break

        # 2. Dispatch 1 Scheduled Follow-up (Interleaved)
        if fu_idx < len(ready_fu) and fu_sent < effective_fu_limit:
            lead = ready_fu[fu_idx]
            fu_idx += 1
            ok, reason = send_single_followup_email(
                lead,
                profile_name=profile_name,
                business_id=business_id
            )
            if ok:
                fu_sent += 1
                if on_step:
                    on_step(f"Bump follow-up dispatched to '{lead.get('business_name')}' ({lead.get('email')}) ✓")
            elif reason == "QUOTA_EXHAUSTED":
                if on_step:
                    on_step("Daily swarm delivered quota reached. Pausing dispatch until next cycle.")
                break

    print(f"  {ui.C_GREEN}[⚡ BALANCED WAVE SUMMARY]{ui.RESET} Dispatched: {initial_sent} fresh pitches + {fu_sent} scheduled follow-ups.")
    return {
        "initial_sent": initial_sent,
        "followup_sent": fu_sent,
        "total_sent": initial_sent + fu_sent
    }
