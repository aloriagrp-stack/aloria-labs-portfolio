"""
Aloria Labs Autonomous Intelligence & Dynamic Pitch Brain
Author: Aloria Labs Engineering Architecture
Engineers hyper-personalized, flaw-aware, niche-specific outreach for modern businesses.
"""

import os
import re
import json
import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger("AloriaBrain")

# Niche Classification & Pain-Point Intelligence Playbooks
NICHE_PLAYBOOKS = {
    "commercial_hvac_facility_maintenance": {
        "keywords": [
            "hvac", "mechanical", "commercial hvac", "cooling", "heating", "refrigeration",
            "facility maintenance", "commercial roofing", "mep", "boiler", "chiller",
            "air conditioning", "industrial ventilation", "facilities", "building maintenance",
            "plumbing", "piping", "sheet metal", "energy management"
        ],
        "industry_name": "Commercial HVAC & Facility Contractors",
        "pain_point": "Heavy reliance on word-of-mouth or public bid boards while national consolidators capture high-margin preventative maintenance agreements for corporate plazas, healthcare facilities, and logistics centers",
        "automation_name": "Direct Property Manager B2B Acquisition Engine & Preventative Maintenance Pipeline",
        "solution_desc": "an automated B2B acquisition pipeline that directly positions {company} in front of regional commercial property managers, asset directors, and warehouse facility operators before preventative maintenance contracts hit public bid boards.",
        "value_prop": "Bypasses low-margin public bidding wars and positions {company} as the preferred preventative maintenance partner for corporate properties."
    },
    "dental_aesthetic_clinics": {
        "keywords": [
            "dental", "dentist", "clinic", "dermatolog", "skin", "hair", "plastic",
            "aesthetic", "orthodont", "implant", "cosmetic", "surgery", "healthcare",
            "hospital", "wellness", "physio", "chiro", "pediatric"
        ],
        "industry_name": "Dental & Aesthetic Clinics",
        "pain_point": "Missed phone inquiries during busy hours, high consultation no-show rates, and slow response to patient queries",
        "automation_name": "24/7 AI WhatsApp Consultation Engine & Smart Appointment Scheduler",
        "solution_desc": "a 24/7 automated WhatsApp consultation & slot-booking assistant for {company}. When a patient inquiries, it immediately qualifies their treatment need, shares procedure FAQs, and reserves a consultation slot with zero-friction automated calendar reminders that reduce no-shows by 40%.",
        "value_prop": "Stops high-ticket patient leakage to competing clinics and completely eliminates receptionist phone bottlenecks."
    },
    "interior_designers_architects": {
        "keywords": [
            "interior", "designer", "architect", "decor", "renovation", "furnish",
            "studio", "modular", "home decor", "construction", "civil", "landscape"
        ],
        "industry_name": "Interior Design & Architecture Studios",
        "pain_point": "Non-serious leads consuming design team bandwidth and manual delays in calculating and sharing preliminary project estimates",
        "automation_name": "Instant AI Project Cost Estimator & High-Speed Visual Portfolio",
        "solution_desc": "an interactive AI Project Cost Estimator tailored for {company}. Potential clients select their property type, square footage, and design tier to receive an instant branded estimate PDF on WhatsApp within 30 seconds, automatically filtering high-budget homeowners for your senior designers.",
        "value_prop": "Filters high-intent luxury homeowners in seconds while eliminating manual quote generation for unqualified inquiries."
    },
    "boutique_hotels_resorts": {
        "keywords": [
            "hotel", "resort", "stay", "villa", "cottage", "inn", "homestay",
            "suites", "palace", "retreat", "lodging", "hostel", "guest house"
        ],
        "industry_name": "Boutique Hotels & Luxury Stays",
        "pain_point": "Losing 20-25% of top-line revenue to OTA commissions (MakeMyTrip, Booking.com) and slow response to high-ticket banquet/wedding inquiries",
        "automation_name": "Direct 0% Commission Booking Engine & Instant WhatsApp Concierge",
        "solution_desc": "a direct, zero-commission mobile booking engine integrated with an instant 24/7 WhatsApp Concierge for {company}. Guests reserve rooms and banquet events directly with instant UPI/Card payments, bypassing third-party OTA fees entirely.",
        "value_prop": "Recovers 20-25% lost margin on guest bookings and captures high-ticket event inquiries instantly."
    },
    "restaurants_cafes_bars": {
        "keywords": [
            "restaurant", "cafe", "bar", "bistro", "lounge", "dining", "food",
            "bakery", "pizzeria", "pub", "eatery", "kitchen", "brewery", "dhaba"
        ],
        "industry_name": "Premium Restaurants & Cafes",
        "pain_point": "Aggregator margin drain (up to 30% to Zomato/Swiggy) and staff friction handling manual table reservations and menu queries during peak rush",
        "automation_name": "Direct QR/WhatsApp Table Reservation & Digital Menu Pre-Ordering Engine",
        "solution_desc": "a direct WhatsApp Table Reservation & Instant Menu Ordering system for {company}. Diners can browse menus, reserve priority seating, and place repeat orders directly via WhatsApp without aggregator commissions.",
        "value_prop": "Fills tables during off-peak hours and drives 100% direct customer repeat loyalty without platform fees."
    },
    "real_estate_property": {
        "keywords": [
            "real estate", "realtor", "property", "builder", "developer",
            "estate agent", "broker", "housing", "realty", "infra", "plots"
        ],
        "industry_name": "Real Estate & Property Advisory",
        "pain_point": "Portal leads (99acres, MagicBricks, Meta ads) cooling off after 30 minutes due to delayed manual agent callback times",
        "automation_name": "30-Second Speed-to-Lead AI WhatsApp Qualifier & Site Tour Scheduler",
        "solution_desc": "a 30-Second Speed-to-Lead AI Assistant for {company}. As soon as a buyer expresses interest, the assistant automatically engages them via WhatsApp, qualifies their budget, configuration, and timeline, and schedules a confirmed site visit directly on your sales team's calendar.",
        "value_prop": "Engages high-intent property buyers while interest is at its peak and delivers pre-qualified site tours."
    },
    "high_ticket_services": {
        "keywords": [
            "solar", "legal", "law", "advocate", "accounting", "tax", "consult",
            "agency", "contractor", "commercial", "finance", "audit", "wealth"
        ],
        "industry_name": "High-Ticket Commercial & Professional Services",
        "pain_point": "Manual back-and-forth scheduling, unvetted cold inquiries, and fragmented follow-up pipelines",
        "automation_name": "Autonomous Inbound Lead Qualification Pipeline & Instant Calendar Sync",
        "solution_desc": "an automated client intake & appointment pipeline for {company}. Incoming prospects are scored against your ideal client profile and guided directly into scheduled consultation calls with relevant project documentation gathered in advance.",
        "value_prop": "Stops time-wasting exploratory calls and places vetted decision-makers directly into partner calendars."
    },
    "general_business": {
        "keywords": [],
        "industry_name": "Premier Local Businesses",
        "pain_point": "Lost inquiries due to slow digital follow-ups and lack of instant self-serve options for mobile customers",
        "automation_name": "High-Performance Modern Web System & 24/7 AI Lead Auto-Responder",
        "solution_desc": "a dedicated, high-speed digital presence combined with a 24/7 instant WhatsApp auto-responder for {company} that captures customer demand and converts visitors into verified bookings around the clock.",
        "value_prop": "Maximizes conversion from your high-rated Google Maps presence into confirmed customers."
    }
}

def clean_company_name(raw_name: str) -> str:
    """Cleans business title from legal suffixes and punctuation."""
    if not raw_name:
        return "Your Company"
    name = raw_name.strip()
    patterns = [
        r"(?i)\s*(pvt\.?\s*ltd\.?|private\s+limited|ltd\.?|limited)$",
        r"(?i)\s*(llc|inc\.?|corp\.?|corporation|gmbh|co\.?)$",
        r"(?i)\s*(sarl|eurl|s\.p\.a\.?|snc)$",
    ]
    for p in patterns:
        name = re.sub(p, "", name).strip()
    return name or raw_name.strip()

def match_niche(lead_niche: str = "") -> str:
    """Classifies lead niche into the optimal playbook category."""
    norm = (lead_niche or "").lower().strip()
    for cat_key, cat_data in NICHE_PLAYBOOKS.items():
        if cat_key == "general_business":
            continue
        for kw in cat_data["keywords"]:
            if kw in norm:
                return cat_key
    return "general_business"

def diagnose_lead_flaws(lead: Dict[str, Any]) -> Dict[str, str]:
    """
    Analyzes scanned audit signals and online footprint to determine
    the precise technical and business vulnerability.
    """
    has_website = bool(lead.get("has_website") and lead.get("website_url"))
    audit_text = (lead.get("audit_summary") or "").lower()

    if not has_website:
        return {
            "type": "NO_WEBSITE",
            "flaw_title": "Zero Official Digital Presence",
            "flaw_diagnosis": "You currently do not have an official website or direct booking portal linked to your Google profile. When local clients search on their phones, they frequently default to competitors who offer instant online previews and direct booking.",
            "impact": "High-intent searchers on Google Maps are bouncing to competing businesses simply because there is no direct channel to book or view pricing."
        }

    # Flaw branch for businesses that have a website
    if "latency" in audit_text or "slow" in audit_text:
        return {
            "type": "SLOW_LATENCY",
            "flaw_title": "High Server Response Latency & Mobile Bounce Hazard",
            "flaw_diagnosis": "Our technical scanner noted that your web server has high response latency, taking several seconds to load on mobile devices. Today's mobile visitors abandon pages that take more than 2.5 seconds to load, impacting both customer conversions and Google search ranking.",
            "impact": "Mobile visitors abandon the page before reviewing your offerings, driving up bounce rates."
        }
    elif "whatsapp" in audit_text:
        return {
            "type": "MISSING_WHATSAPP",
            "flaw_title": "Missing Instant Speed-to-Lead Channel",
            "flaw_diagnosis": "Your site currently lacks an instant 1-click WhatsApp speed-to-lead mechanism. Over 70% of prospective clients prefer instant WhatsApp messaging over filling out static email forms and waiting hours for a callback.",
            "impact": "Prospects who want immediate answers leave for alternatives who provide instant WhatsApp engagement."
        }
    elif "booking" in audit_text or "interactive" in audit_text:
        return {
            "type": "LACKS_SELF_SERVE",
            "flaw_title": "Missing Automated Self-Serve Booking Engine",
            "flaw_diagnosis": "Your website operates primarily as a static brochure without an automated self-serve scheduling or quote estimation engine, forcing interested clients into manual phone calls during office hours.",
            "impact": "After-hours inquiries go unanswered, creating an operational bottleneck for your staff."
        }
    elif "viewport" in audit_text:
        return {
            "type": "MOBILE_RENDERING",
            "flaw_title": "Mobile Viewport Rendering Breakdown",
            "flaw_diagnosis": "Your site lacks optimized mobile viewport formatting, causing text and key action buttons to shift awkwardly on modern smartphone screens.",
            "impact": "Creates a poor first impression on mobile users who represent the vast majority of local searches."
        }
    elif "ssl" in audit_text or "non-secure" in audit_text:
        return {
            "type": "SECURITY_SSL",
            "flaw_title": "Non-Secure HTTP Connection Warning",
            "flaw_diagnosis": "Your site triggers browser security notices ('Not Secure') due to missing or unconfigured SSL encryption, eroding trust before clients even read your services.",
            "impact": "High-ticket clients hesitate to transact or submit personal details on non-SSL domains."
        }
    else:
        return {
            "type": "CONVERSION_LEAK",
            "flaw_title": "Modern Conversion Architecture Gap",
            "flaw_diagnosis": "While your business has strong local reviews, your website is not structured to automatically capture and qualify incoming visitors with instant interactive workflows.",
            "impact": "Sub-optimal visitor-to-consultation conversion rate compared to modern automated setups."
        }

def generate_dynamic_email(lead: Dict[str, Any], email_type: str = "INITIAL") -> Tuple[str, str, str, Dict[str, Any]]:
    """
    Synthesizes a 10/10 bespoke, hyper-personalized email pitch based on
    exact diagnosed flaws, niche-specific ROI, and frictionless call-to-action.
    Specialized high-ticket American B2B copy for Commercial HVAC & Facility Contractors.
    """
    company_name = clean_company_name(lead.get("business_name") or "Your Company")
    city = lead.get("city") or "your area"
    niche_key = match_niche(lead.get("niche") or "")
    playbook = NICHE_PLAYBOOKS.get(niche_key, NICHE_PLAYBOOKS["general_business"])

    is_commercial_hvac = (niche_key == "commercial_hvac_facility_maintenance")
    is_usa = (str(lead.get("country") or "").upper() in ["USA", "US", "UNITED STATES"] or is_commercial_hvac)

    rating = lead.get("rating") or "4.6"
    reviews_count = lead.get("reviews_count") or "25+"
    flaw_info = diagnose_lead_flaws(lead)
    if is_usa and "WhatsApp" in flaw_info.get("flaw_diagnosis", ""):
        flaw_info["flaw_diagnosis"] = flaw_info["flaw_diagnosis"].replace("WhatsApp", "mobile-optimized 1-click speed-to-lead")
        flaw_info["flaw_title"] = flaw_info["flaw_title"].replace("WhatsApp", "Instant Speed-to-Lead")

    sender_name = "Shriyansh Aloria"
    sender_title = "Founder & Systems Architect"
    company_brand = "Aloria Labs"
    website = "https://alorialabs.in"
    corporate_email = "shriyanshaloria@alorialabs.in"
    direct_phone = "+91 93184 85680"
    
    # Use clean US corporate signoff without international phone prefix for US leads
    contact_line = f"{website} | {corporate_email}" if is_usa else f"{website} | {direct_phone}"

    solution_text = playbook["solution_desc"].format(company=company_name)
    if is_usa:
        solution_text = solution_text.replace("on WhatsApp", "via instant SMS/link").replace("via WhatsApp", "online").replace("WhatsApp", "mobile-optimized")

    if is_commercial_hvac:
        # HIGH-TICKET US B2B COMMERCIAL HVAC & FACILITY PLAYBOOK
        if email_type == "INITIAL":
            subject = f"commercial maintenance contracts in {city} / {company_name}"
            plain_text = f"""Hi {company_name} Team,

Came across {company_name} while reviewing top commercial mechanical & HVAC contractors in the {city} area.

Most commercial contractor leaders we speak with in the region face the same bottleneck: they rely heavily on word-of-mouth or public bid boards, while national consolidators take the high-margin preventative maintenance agreements for corporate plazas, healthcare facilities, and logistics centers.

At Aloria Labs, we engineer automated B2B acquisition pipelines that directly position regional commercial contractors in front of local facility directors and commercial property managers before jobs ever hit public bidding platforms.

Would you be against reviewing a brief 2-minute breakdown of how we're positioning regional contractors to capture commercial maintenance agreements in {city}?

Best regards,

{sender_name}
{sender_title} | {company_brand}
{contact_line}
"""
            html_text = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b; line-height: 1.65; max-width: 620px; font-size: 15px;">
  <p style="margin-top: 0;">Hi {company_name} Team,</p>
  <p>Came across <strong>{company_name}</strong> while reviewing top commercial mechanical & HVAC contractors in the {city} area.</p>
  <p>Most commercial contractor leaders we speak with in the region face the same bottleneck: they rely heavily on word-of-mouth or public bid boards, while national consolidators take the high-margin preventative maintenance agreements for corporate plazas, healthcare facilities, and logistics centers.</p>
  <p>At Aloria Labs, we engineer automated B2B acquisition pipelines that directly position regional commercial contractors in front of local facility directors and commercial property managers before jobs ever hit public bidding platforms.</p>
  <p style="font-weight: 600; color: #0f172a;">Would you be against reviewing a brief 2-minute breakdown of how we're positioning regional contractors to capture commercial maintenance agreements in {city}?</p>
  <br>
  <div style="border-top: 1px solid #e2e8f0; padding-top: 12px;">
    <p style="margin: 0; font-weight: 600; color: #0f172a;">{sender_name}</p>
    <p style="margin: 2px 0; color: #64748b; font-size: 13px;">{sender_title} | {company_brand}</p>
    <p style="margin: 0; font-size: 13px;"><a href="{website}" style="color: #2563eb; text-decoration: none;">{website}</a> | <a href="mailto:{corporate_email}" style="color: #2563eb; text-decoration: none;">{corporate_email}</a></p>
  </div>
</div>
"""
        elif email_type == "FOLLOW_UP_1":
            subject = f"Re: commercial maintenance contracts in {city} / {company_name}"
            plain_text = f"""Hi {company_name} Team,

Following up briefly on my note regarding commercial preventative maintenance accounts in {city}.

I know you are busy managing active service dispatch and ongoing mechanical projects, so I'll keep this short:

We help regional commercial mechanical contractors bypass low-margin public bidding by engineering direct, automated pipelines into local property managers and facility directors.

Would you be open to reviewing the 2-minute walkthrough tailored for {company_name}?

Best regards,

{sender_name}
{sender_title} | {company_brand}
{contact_line}
"""
            html_text = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b; line-height: 1.65; max-width: 620px; font-size: 15px;">
  <p style="margin-top: 0;">Hi {company_name} Team,</p>
  <p>Following up briefly on my note regarding commercial preventative maintenance accounts in {city}.</p>
  <p>I know you are busy managing active service dispatch and ongoing mechanical projects, so I'll keep this short:</p>
  <p>We help regional commercial mechanical contractors bypass low-margin public bidding by engineering direct, automated pipelines into local property managers and facility directors.</p>
  <p style="font-weight: 600; color: #0f172a;">Would you be open to reviewing the 2-minute walkthrough tailored for {company_name}?</p>
  <br>
  <p style="margin: 0; font-weight: 600;">{sender_name}</p>
  <p style="margin: 0; color: #64748b; font-size: 13px;">{company_brand} | <a href="{website}" style="color: #2563eb;">{website}</a></p>
</div>
"""
        else: # FOLLOW_UP_2 / Breakup
            subject = f"Closing the loop / commercial accounts at {company_name}"
            plain_text = f"""Hi {company_name} Team,

Reaching out one last time to close the loop. If expanding direct commercial maintenance agreements isn't an active priority for {company_name} right now, no problem at all.

If you ever decide to build a direct pipeline into regional commercial facility managers and corporate properties in {city}, feel free to reach back out anytime.

Wishing {company_name} continued growth this quarter!

Best regards,

{sender_name}
{sender_title} | {company_brand}
{contact_line}
"""
            html_text = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b; line-height: 1.65; max-width: 620px; font-size: 15px;">
  <p style="margin-top: 0;">Hi {company_name} Team,</p>
  <p>Reaching out one last time to close the loop. If expanding direct commercial maintenance agreements isn't an active priority for {company_name} right now, no problem at all.</p>
  <p>If you ever decide to build a direct pipeline into regional commercial facility managers and corporate properties in {city}, feel free to reach back out anytime.</p>
  <p>Wishing {company_name} continued growth this quarter!</p>
  <br>
  <p style="margin: 0; font-weight: 600;">{sender_name}</p>
  <p style="margin: 0; color: #64748b; font-size: 13px;">{sender_title} | {company_brand}</p>
  <p style="margin: 0; font-size: 13px;"><a href="{website}" style="color: #2563eb;">{website}</a></p>
</div>
"""
    else:
        # Standard niche handling
        if email_type == "INITIAL":
            if flaw_info["type"] == "NO_WEBSITE":
                subject = f"Digital booking concept for {company_name} ({rating} stars on Google Maps)"
            elif flaw_info["type"] == "SLOW_LATENCY":
                subject = f"Quick note regarding {company_name}'s web performance & mobile conversions"
            elif flaw_info["type"] == "MISSING_WHATSAPP":
                subject = f"Idea for {company_name}: 24/7 instant WhatsApp speed-to-lead"
            else:
                subject = f"Question regarding client intake & digital operations at {company_name}"

            plain_text = f"""Hi {company_name} Team,

I came across {company_name} while researching premier {playbook['industry_name'].lower()} in {city}. Your reputation is impressive - {rating} stars across {reviews_count} reviews on Google Maps.

While inspecting your digital setup, I noticed a specific area where potential revenue is currently slipping through:

• {flaw_info['flaw_diagnosis']}

For modern {playbook['industry_name'].lower()}, we engineer {solution_text}

This {playbook['value_prop'].lower()}

I put together a brief 60-second interactive preview demonstrating how this automated setup would work specifically for {company_name}.

Would you be open to checking it out? Just reply "YES" and I'll send the preview link over.

Best regards,

{sender_name}
{sender_title} | {company_brand}
{contact_line}
"""
            html_text = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b; line-height: 1.65; max-width: 620px; font-size: 15px;">
  <p style="margin-top: 0;">Hi {company_name} Team,</p>
  <p>I came across <strong>{company_name}</strong> while researching premier {playbook['industry_name'].lower()} in {city}. Your reputation is impressive — <strong>{rating}★ across {reviews_count} reviews</strong> on Google Maps.</p>
  <p>While inspecting your digital setup, I noticed a specific area where potential revenue is currently slipping through:</p>
  <div style="background-color: #f8fafc; border-left: 3px solid #3b82f6; padding: 12px 16px; margin: 16px 0; border-radius: 0 6px 6px 0;">
    <p style="margin: 0; font-weight: 600; color: #0f172a;">{flaw_info['flaw_title']}</p>
    <p style="margin: 4px 0 0 0; color: #475569; font-size: 14px;">{flaw_info['flaw_diagnosis']}</p>
  </div>
  <p>For modern {playbook['industry_name'].lower()}, we engineer {solution_text}</p>
  <p style="color: #059669; font-weight: 500;">✓ {playbook['value_prop']}</p>
  <p>I put together a brief 60-second interactive preview demonstrating how this automated setup would work specifically for {company_name}.</p>
  <p style="font-weight: 600; color: #0f172a;">Would you be open to checking it out? Just reply "YES" and I'll send the preview link over.</p>
  <br>
  <div style="border-top: 1px solid #e2e8f0; padding-top: 12px;">
    <p style="margin: 0; font-weight: 600; color: #0f172a;">{sender_name}</p>
    <p style="margin: 2px 0; color: #64748b; font-size: 13px;">{sender_title} | {company_brand}</p>
    <p style="margin: 0; font-size: 13px;"><a href="{website}" style="color: #2563eb; text-decoration: none;">{website}</a> | {corporate_email}</p>
  </div>
</div>
"""
        elif email_type == "FOLLOW_UP_1":
            subject = f"Re: Digital booking concept for {company_name}"
            plain_text = f"""Hi {company_name} Team,

Following up briefly on my earlier note regarding {company_name}'s client intake setup in {city}.

I know you are busy managing day-to-day operations, so I'll keep this short:

We've seen similar {playbook['industry_name'].lower()} increase direct bookings by 35% simply by deploying an automated speed-to-lead assistant and eliminating manual scheduling friction.

I still have the interactive prototype ready for {company_name}. Should I send over the 60-second video walkthrough?

Best regards,

{sender_name}
{company_brand} | {website}
"""
            html_text = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b; line-height: 1.65; max-width: 620px; font-size: 15px;">
  <p style="margin-top: 0;">Hi {company_name} Team,</p>
  <p>Following up briefly on my earlier note regarding {company_name}'s client intake setup in {city}.</p>
  <p>I know you are busy managing day-to-day operations, so I'll keep this short:</p>
  <p>We've seen similar {playbook['industry_name'].lower()} increase direct bookings by 35% simply by deploying an automated speed-to-lead assistant and eliminating manual scheduling friction.</p>
  <p style="font-weight: 600; color: #0f172a;">I still have the interactive prototype ready for {company_name}. Should I send over the 60-second video walkthrough?</p>
  <br>
  <p style="margin: 0; font-weight: 600;">{sender_name}</p>
  <p style="margin: 0; color: #64748b; font-size: 13px;">{company_brand} | <a href="{website}" style="color: #2563eb;">{website}</a></p>
</div>
"""
        else: # FOLLOW_UP_2
            subject = f"Closing the loop on {company_name}'s automated intake prototype"
            plain_text = f"""Hi {company_name} Team,

Reaching out one final time to close the loop. If automated booking and speed-to-lead aren't an active focus for {company_name} right now, no problem at all.

If you ever decide to modernize your client intake pipeline or reduce third-party fees, feel free to reach out anytime.

Wishing {company_name} continued success in {city}!

Best regards,

{sender_name}
{sender_title} | {company_brand}
{website}
"""
            html_text = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b; line-height: 1.65; max-width: 620px; font-size: 15px;">
  <p style="margin-top: 0;">Hi {company_name} Team,</p>
  <p>Reaching out one final time to close the loop. If automated booking and speed-to-lead aren't an active focus for {company_name} right now, no problem at all.</p>
  <p>If you ever decide to modernize your client intake pipeline or reduce third-party fees, feel free to reach out anytime.</p>
  <p>Wishing {company_name} continued success in {city}!</p>
  <br>
  <p style="margin: 0; font-weight: 600;">{sender_name}</p>
  <p style="margin: 0; color: #64748b; font-size: 13px;">{sender_title} | {company_brand}</p>
  <p style="margin: 0; font-size: 13px;"><a href="{website}" style="color: #2563eb;">{website}</a></p>
</div>
"""

    meta = {
        "niche_key": niche_key,
        "niche_name": playbook["industry_name"],
        "flaw_type": flaw_info["type"],
        "flaw_title": flaw_info["flaw_title"],
        "automation_offered": playbook["automation_name"]
    }

    return subject, plain_text, html_text, meta

def generate_dynamic_whatsapp(lead: Dict[str, Any]) -> str:
    """Generates natural, high-converting WhatsApp message tailored to the business."""
    company_name = clean_company_name(lead.get("business_name") or "Your Team")
    niche_key = match_niche(lead.get("niche") or "")
    playbook = NICHE_PLAYBOOKS.get(niche_key, NICHE_PLAYBOOKS["general_business"])
    flaw_info = diagnose_lead_flaws(lead)
    if is_usa and "WhatsApp" in flaw_info.get("flaw_diagnosis", ""):
        flaw_info["flaw_diagnosis"] = flaw_info["flaw_diagnosis"].replace("WhatsApp", "mobile-optimized 1-click speed-to-lead")
        flaw_info["flaw_title"] = flaw_info["flaw_title"].replace("WhatsApp", "Instant Speed-to-Lead")

    return f"Hi {company_name} Team! I noticed your {lead.get('rating', '4.6')}★ Google presence in {lead.get('city', 'your area')}. We build 24/7 AI WhatsApp speed-to-lead systems for premier {playbook['industry_name'].lower()} that instantly capture and qualify incoming inquiries. I built a 60-second interactive preview for {company_name} — would you like to see how it works?"

def load_intelligence_library():
    """Stub for backwards compatibility with existing callers."""
    return {"status": "ACTIVE", "niches_count": len(NICHE_PLAYBOOKS)}

# Backwards compatibility attributes
_ALL_PROBLEMS = list(NICHE_PLAYBOOKS.keys())
_NICHE_INDEX = {k: v["industry_name"] for k, v in NICHE_PLAYBOOKS.items()}
