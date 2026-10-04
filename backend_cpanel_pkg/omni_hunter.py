import sys
import re
import time
import random
import base64
import urllib.parse
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import requests

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import db
import ui
import email_verifier

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,10}')
PHONE_REGEX = re.compile(r'(?:\+91[\-\s]?)?[6-9]\d{9}|\b0\d{2,4}[\-\s]?\d{6,8}\b')

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
]

OTA_DOMAINS = [
    "booking.com", "agoda.com", "tripadvisor", "makemytrip.com",
    "goibibo.com", "expedia.com", "hotels.com", "trivago.com",
    "yatra.com", "cleartrip.com", "easemytrip.com", "oyorooms.com",
    "treebo.com", "fabhotels.com", "ixigo.com", "kayak.com",
    "hostelworld.com", "vrbo.com", "skyscanner", "lonelyplanet.com",
    "holidify.com", "thrillophilia.com", "trip.com", "travelguru.com",
    "facebook.com", "instagram.com", "justdial.com", "indiamart.com",
    "youtube.com", "twitter.com", "x.com", "linkedin.com", "airbnb", "wikipedia.org",
    "bing.com", "microsoft.com", "google.com", "yahoo.com", "mapsofindia.com"
]

def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1"
    }

def decode_search_url(raw_url: Optional[str]) -> str:
    """Decodes Bing/DuckDuckGo tracking redirects to uncover the real target website."""
    if not raw_url:
        return ""
    if "bing.com/ck/a?" in raw_url:
        match = re.search(r'[?&]u=a1([^&]+)', raw_url)
        if match:
            raw_b64 = match.group(1)
            raw_b64 += "=" * ((4 - len(raw_b64) % 4) % 4)
            try:
                decoded = base64.b64decode(raw_b64).decode("utf-8", errors="ignore")
                return decoded.split("?")[0].strip()
            except Exception:
                pass
    elif "duckduckgo.com/l/?uddg=" in raw_url:
        match = re.search(r'uddg=([^&]+)', raw_url)
        if match:
            return urllib.parse.unquote(match.group(1)).split("?")[0].strip()
    elif "google.com/url?" in raw_url:
        match = re.search(r'url=([^&]+)', raw_url)
        if match:
            return urllib.parse.unquote(match.group(1)).split("?")[0].strip()

    clean = raw_url.split("?")[0].strip()
    if clean and not clean.startswith("http://") and not clean.startswith("https://"):
        clean = "https://" + clean
    return clean

def is_ota_or_social(url: str) -> bool:
    if not url:
        return True
    lower = url.lower()
    return any(dom in lower for dom in OTA_DOMAINS)

def search_serp(query: str, limit: int = 15) -> List[Dict[str, str]]:
    """
    Executes a lightweight, zero-block SERP query.
    Returns list of {'title': ..., 'url': ..., 'snippet': ...}.
    """
    results = []
    encoded = urllib.parse.quote_plus(query)
    search_url = f"https://www.bing.com/search?q={encoded}&count=25"

    try:
        resp = requests.get(search_url, headers=get_random_headers(), timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            items = soup.select("li.b_algo")
            for it in items:
                if len(results) >= limit:
                    break
                link_elem = it.select_one("h2 a")
                snippet_elem = it.select_one("div.b_caption p, p")

                if link_elem:
                    raw_href = link_elem.get("href")
                    if isinstance(raw_href, str) and raw_href:
                        real_url = decode_search_url(raw_href)
                        title = link_elem.get_text(strip=True)
                        snippet = snippet_elem.get_text(" ", strip=True) if snippet_elem else ""

                        if real_url and not real_url.startswith("https://www.bing.com"):
                            results.append({
                                "title": title,
                                "url": real_url,
                                "snippet": snippet
                            })
    except Exception:
        pass

    return results


# =====================================================================
# CHANNEL 2: GOOGLE DORKING & SEARCH FOOTPRINT ENGINE
# =====================================================================
def hunt_google_dorking(city: str, country: str = "India", niche: str = "Hotels", limit: int = 25, business_id: str = "gethotelstays") -> List[Dict[str, Any]]:
    """
    Executes search footprints (Google/Bing Dorks) to extract direct hotel websites,
    contact pages, and snippet emails without Google Maps limits.
    """
    print(f"  {ui.C_CYAN}[⚡ CHANNEL 2: GOOGLE DORKING FOOTPRINTS]{ui.RESET} Hunting '{niche}' in {city}...")
    dorks = [
        f'"{niche} in {city}" "contact us" "email"',
        f'site:*.in "{niche}" "{city}" "reservations@"',
        f'"{niche} in {city}" "book direct" ("@gmail.com" OR "info@")',
        f'"{niche}" "{city}" "official website" "phone"'
    ]

    discovered = []
    seen_urls = set()

    for dork in dorks:
        if len(discovered) >= limit:
            break

        serp_items = search_serp(dork, limit=12)
        for item in serp_items:
            if len(discovered) >= limit:
                break

            target_url = item["url"]
            if not target_url or is_ota_or_social(target_url) or target_url in seen_urls:
                continue
            seen_urls.add(target_url)

            raw_title = item["title"]
            title = raw_title.split("-")[0].split("|")[0].split("—")[0].replace("Official Site", "").replace("Official Website", "").strip()
            if not title or len(title) < 3:
                continue

            snippet_text = item["snippet"]

            # Extract email directly from snippet if present
            snippet_emails = EMAIL_REGEX.findall(snippet_text)
            clean_em = None
            if snippet_emails:
                for em in snippet_emails:
                    if not any(bad in em.lower() for bad in ["example", "domain", "test", "bootstrap", "sentry"]):
                        clean_em = em.strip().lower()
                        break

            # Extract phone from snippet if present
            phone_match = PHONE_REGEX.search(snippet_text)
            phone_val = phone_match.group(0).strip() if phone_match else None

            lead_id = db.insert_lead(
                business_name=title,
                country=country,
                city=city,
                niche=niche,
                website_url=target_url,
                phone=phone_val,
                business_id=business_id
            )

            if lead_id:
                if clean_em:
                    db.update_audit(lead_id, email=clean_em, audit_summary="Discovered via Dorking Footprint")

                discovered.append({
                    "id": lead_id,
                    "name": title,
                    "website_url": target_url,
                    "email": clean_em,
                    "phone": phone_val,
                    "source": "Dorking Footprints"
                })
                sys.stdout.write(f"\r  {ui.C_GREEN}[✓ Dorking]{ui.RESET} Found: {title[:28]} ➔ {target_url[:35]}   ")
                sys.stdout.flush()

        time.sleep(0.8)

    print(f"\n        {ui.C_GREEN}✓ Channel 2 (Dorking) captured {len(discovered)} direct properties{ui.RESET}")
    return discovered


# =====================================================================
# CHANNEL 3: INSTAGRAM & SOCIAL BIO HUNTER
# =====================================================================
def hunt_instagram_bios(city: str, country: str = "India", niche: str = "Hotels", limit: int = 20, business_id: str = "gethotelstays") -> List[Dict[str, Any]]:
    """
    Extracts boutique hotels, luxury resorts, and homestays from public Instagram bios.
    Extracts direct booking WhatsApp numbers, official email addresses, and bio website links
    without requiring any Instagram login or account.
    """
    print(f"  {ui.C_MAGENTA}[⚡ CHANNEL 3: INSTAGRAM SOCIAL BIO HUNTER]{ui.RESET} Hunting boutique stays in {city}...")
    queries = [
        f'site:instagram.com "{niche}" "{city}" ("email" OR "reservations" OR "bookings" OR "contact")',
        f'site:instagram.com "resort in {city}" ("wa.me" OR "+91" OR "@gmail.com")',
        f'site:instagram.com "boutique stay in {city}" ("booking" OR "dm")'
    ]

    discovered = []
    seen_handles = set()

    for q in queries:
        if len(discovered) >= limit:
            break

        serp_items = search_serp(q, limit=12)
        for item in serp_items:
            if len(discovered) >= limit:
                break

            raw_title = item["title"]
            # Instagram title format: "Hotel Name (@handle) • Instagram photos and videos"
            handle_match = re.search(r'\(@([a-zA-Z0-9_.]+)\)', raw_title)
            handle = handle_match.group(1) if handle_match else None

            if handle and handle in seen_handles:
                continue
            if handle:
                seen_handles.add(handle)

            biz_name = raw_title.split("(@")[0].split("•")[0].replace("Instagram", "").strip()
            if not biz_name or len(biz_name) < 3:
                biz_name = f"@{handle}" if handle else f"{city} Boutique Stay"

            snippet = item["snippet"]

            # Extract email from bio snippet
            found_emails = EMAIL_REGEX.findall(snippet)
            bio_email = found_emails[0].strip().lower() if found_emails else None

            # Extract phone/WhatsApp from bio snippet
            phone_match = PHONE_REGEX.search(snippet)
            phone_val = phone_match.group(0).strip() if phone_match else None

            # Extract external website link from bio snippet if mentioned
            web_match = re.search(r'(https?://[^\s]+|www\.[^\s]+)', snippet)
            bio_url = None
            if web_match:
                raw_w = web_match.group(1)
                if not is_ota_or_social(raw_w) and "instagram.com" not in raw_w:
                    bio_url = decode_search_url(raw_w)

            lead_id = db.insert_lead(
                business_name=biz_name,
                country=country,
                city=city,
                niche=niche,
                website_url=bio_url,
                phone=phone_val,
                business_id=business_id
            )

            if lead_id:
                if bio_email:
                    db.update_audit(lead_id, email=bio_email, audit_summary=f"Extracted from Instagram Bio (@{handle or 'public'})")

                discovered.append({
                    "id": lead_id,
                    "name": biz_name,
                    "handle": handle,
                    "email": bio_email,
                    "phone": phone_val,
                    "website_url": bio_url,
                    "source": "Instagram Bio"
                })
                sys.stdout.write(f"\r  {ui.C_MAGENTA}[✓ Instagram]{ui.RESET} Found: {biz_name[:25]} | Bio Email: {bio_email or 'N/A'} | Phone: {phone_val or 'N/A'}   ")
                sys.stdout.flush()

        time.sleep(0.8)

    print(f"\n        {ui.C_GREEN}✓ Channel 3 (Instagram Bio) captured {len(discovered)} social properties{ui.RESET}")
    return discovered


# =====================================================================
# CHANNEL 4: JUSTDIAL & INDIAN DIRECTORY ENGINE
# =====================================================================
def hunt_justdial_directory(city: str, country: str = "India", niche: str = "Hotels", limit: int = 20, business_id: str = "gethotelstays") -> List[Dict[str, Any]]:
    """
    Scrapes independent hotels, lodges, and resorts listed on Justdial.
    Extracts phone numbers, ratings, addresses, and website links across Indian destinations.
    """
    print(f"  {ui.C_YELLOW}[⚡ CHANNEL 4: JUSTDIAL DIRECTORY ENGINE]{ui.RESET} Scanning directory listings in {city}...")
    clean_c = city.lower().replace(" ", "-")

    # Use search footprints for Justdial to avoid anti-bot blocks
    dork = f'site:justdial.com/{clean_c} "{niche}" "Contact" OR "Phone"'
    discovered = []
    seen_titles = set()

    serp_items = search_serp(dork, limit=limit)
    for item in serp_items:
        if len(discovered) >= limit:
            break

        raw_title = item["title"]
        title = raw_title.split("in ")[0].split("-")[0].replace("Justdial", "").strip()
        if not title or title in seen_titles or len(title) < 3:
            continue
        seen_titles.add(title)

        snippet = item["snippet"]

        # Extract phone number from snippet
        phone_match = PHONE_REGEX.search(snippet)
        phone_val = phone_match.group(0).strip() if phone_match else None

        # Extract address if present
        addr_match = re.search(r'(?:Near|Opposite|Road|Nagar|Colony|Beach|Lane)[^,\.]+', snippet, flags=re.I)
        addr_val = addr_match.group(0).strip() if addr_match else f"{city}, {country}"

        lead_id = db.insert_lead(
            business_name=title,
            country=country,
            city=city,
            niche=niche,
            address=addr_val,
            phone=phone_val,
            business_id=business_id
        )

        if lead_id:
            discovered.append({
                "id": lead_id,
                "name": title,
                "phone": phone_val,
                "address": addr_val,
                "source": "Justdial Directory"
            })
            sys.stdout.write(f"\r  {ui.C_YELLOW}[✓ Justdial]{ui.RESET} Found: {title[:28]} | Phone: {phone_val or 'N/A'}   ")
            sys.stdout.flush()

    print(f"\n        {ui.C_GREEN}✓ Channel 4 (Justdial) captured {len(discovered)} directory listings{ui.RESET}")
    return discovered


# =====================================================================
# CHANNEL 5: OTA REVERSE-LOOKUP (TRIPADVISOR / MMT TO DIRECT WEBSITE)
# =====================================================================
def hunt_ota_reverse(city: str, country: str = "India", niche: str = "Hotels", limit: int = 20, business_id: str = "gethotelstays") -> List[Dict[str, Any]]:
    """
    Discovers top independent hotels listed on TripAdvisor and MakeMyTrip,
    then automatically resolves their official direct website URL to bypass OTA commissions.
    """
    print(f"  {ui.C_BLUE}[⚡ CHANNEL 5: OTA REVERSE-LOOKUP ENGINE]{ui.RESET} Hunting top OTA properties in {city}...")
    dorks = [
        f'site:tripadvisor.in/Hotel_Review "{city}"',
        f'site:tripadvisor.in "Hotels in {city}" OR "Resorts in {city}"',
        f'site:makemytrip.com/hotels/ "hotels in {city}"'
    ]
    discovered = []
    seen_hotels = set()

    for dork in dorks:
        if len(discovered) >= limit:
            break
        serp_items = search_serp(dork, limit=12)
        for it in serp_items:
            if len(discovered) >= limit:
                break
            
            raw_title = it.get("title", "")
            snippet = it.get("snippet", "")
            
            candidates = []
            JUNK_TERMS = [
                "save upto", "save up to", "discount", "lowest price", "booking", "book ",
                "compare", "prices", "deals", "search", "ratings", "reviews", "online",
                "best hotels", "top hotels", "hotels in", "resorts in", "stay in", "properties",
                "flights", "holiday packages", "tariff"
            ]

            # Method A: Title contains hotel name (e.g. "Taj Fort Aguada Resort & Spa (Candolim) - Reviews - Tripadvisor")
            if "tripadvisor" in raw_title.lower() or "makemytrip" in raw_title.lower():
                cand_from_title = raw_title.split("(")[0].split("-")[0].split("—")[0].split("|")[0]
                for noise in ["Tripadvisor", "TripAdvisor", "MakeMyTrip", "THE 10 BEST", "Hotels in", "Resorts in"]:
                    cand_from_title = cand_from_title.replace(noise, "")
                cand_from_title = cand_from_title.strip()
                cand_lower = cand_from_title.lower()
                if len(cand_from_title) > 4 and not any(j in cand_lower for j in JUNK_TERMS):
                    if any(w in cand_lower for w in ["hotel", "resort", "inn", "villa", "stay", "palace", "suites", "retreat", "haveli", "cottage", "taj", "leela", "marriott", "hyatt"]):
                        candidates.append(cand_from_title)
            
            # Method B: Numbered list in snippet
            snippet_matches = re.findall(r'\d+[\.\)]\s*([A-Za-z0-9\s&\'\-]+?(?:Hotel|Resort|Inn|Villas?|Stays?|Palace|Suites?|Retreat|Haveli|Cottage))', snippet)
            for sm in snippet_matches:
                if not any(j in sm.lower() for j in JUNK_TERMS):
                    candidates.append(sm)

            for cand in candidates:
                if len(discovered) >= limit:
                    break
                cand_clean = cand.strip()
                if not cand_clean or cand_clean in seen_hotels or len(cand_clean) < 4:
                    continue
                if any(j in cand_clean.lower() for j in JUNK_TERMS):
                    continue
                seen_hotels.add(cand_clean)

                # Resolve official website for this hotel via direct search
                resolve_dork = f'"{cand_clean}" "{city}" "official website"'
                resolved_items = search_serp(resolve_dork, limit=3)
                resolved_url = None
                for r_item in resolved_items:
                    u = r_item["url"]
                    if u and not is_ota_or_social(u):
                        resolved_url = u
                        break

                # Only capture if official direct website was successfully resolved
                if not resolved_url:
                    continue

                lead_id = db.insert_lead(
                    business_name=cand_clean,
                    country=country,
                    city=city,
                    niche=niche,
                    website_url=resolved_url,
                    business_id=business_id
                )

                if lead_id:
                    discovered.append({
                        "id": lead_id,
                        "name": cand_clean,
                        "website_url": resolved_url,
                        "source": "OTA Reverse-Lookup"
                    })
                    sys.stdout.write(f"\r  {ui.C_BLUE}[✓ OTA Reverse]{ui.RESET} Resolved: {cand_clean[:25]} ➔ {resolved_url or 'Official Domain Pending'}   ")
                    sys.stdout.flush()

                time.sleep(0.5)

    print(f"\n        {ui.C_GREEN}✓ Channel 5 (OTA Reverse) captured {len(discovered)} direct properties{ui.RESET}")
    return discovered


# =====================================================================
# MASTER OMNICHANNEL SWARM COORDINATOR
# =====================================================================
# CHANNEL 1: ZERO-BROWSER GOOGLE MAPS & LOCAL FOOTPRINTS
# =====================================================================
def hunt_maps_footprints(city: str, country: str = "India", niche: str = "Hotels", limit: int = 25, business_id: str = "gethotelstays") -> List[Dict[str, Any]]:
    """
    Extracts direct property websites, phone numbers, and ratings from Google Maps & local SERP listings
    WITHOUT launching any heavy Playwright browsers. 0% RAM overhead, 100% lightweight HTTP.
    """
    print(f"  {ui.C_GREEN}[⚡ CHANNEL 1: ZERO-BROWSER GOOGLE MAPS FOOTPRINTS]{ui.RESET} Hunting '{niche}' in {city}...")
    
    sub_zones = [
        f"{city}", f"North {city}", f"South {city}", f"Central {city}",
        f"Calangute {city}", f"Candolim {city}", f"Anjuna {city}", f"Panaji {city}",
        f"Baga {city}", f"Morjim {city}", f"Palolem {city}", f"Vagator {city}"
    ] if "goa" in city.lower() else [f"{city}", f"North {city}", f"South {city}", f"Central {city}", f"East {city}", f"West {city}"]
    
    dorks = []
    for z in sub_zones[:6]:
        dorks.append(f'site:google.com/maps "{niche}" "{z}"')
        dorks.append(f'"{niche} in {z}" "official website" OR "contact"')
        dorks.append(f'"{niche} in {z}" "phone" "address" "reviews"')

    discovered = []
    seen_urls = set()

    for dork in dorks:
        if len(discovered) >= limit:
            break

        serp_items = search_serp(dork, limit=10)
        for item in serp_items:
            if len(discovered) >= limit:
                break

            target_url = item["url"]
            if not target_url or is_ota_or_social(target_url) or target_url in seen_urls:
                continue
            seen_urls.add(target_url)

            raw_title = item["title"]
            title = raw_title.split("-")[0].split("|")[0].split("—")[0].replace("Google Maps", "").replace("Official Site", "").strip()
            if not title or len(title) < 3:
                continue

            snippet_text = item["snippet"]

            phone_match = PHONE_REGEX.search(snippet_text)
            phone_val = phone_match.group(0).strip() if phone_match else None

            rating_match = re.search(r'([3-5]\.\d)\s*(?:stars?|rating|\/5|\(\d+\))', snippet_text, re.I)
            rating_val = rating_match.group(1) if rating_match else "4.2"

            lead_id = db.insert_lead(
                business_name=title,
                country=country,
                city=city,
                niche=niche,
                website_url=target_url,
                phone=phone_val,
                rating=rating_val,
                business_id=business_id
            )

            if lead_id:
                discovered.append({
                    "id": lead_id,
                    "name": title,
                    "website_url": target_url,
                    "phone": phone_val,
                    "rating": rating_val,
                    "source": "Zero-Browser Maps Footprints"
                })
                sys.stdout.write(f"\r  {ui.C_GREEN}[✓ Maps Zero-Browser]{ui.RESET} Found: {title[:28]} ➔ {target_url[:35]}   ")
                sys.stdout.flush()

        time.sleep(0.5)

    print(f"\n        {ui.C_GREEN}✓ Channel 1 (Maps Footprints) captured {len(discovered)} direct properties (0 browsers used){ui.RESET}")
    return discovered


# =====================================================================
# MASTER OMNICHANNEL SWARM COORDINATOR (2X HARVEST & 100-WORKER SCREENING)
# =====================================================================
def hunt_omnichannel_swarm(city: str = "Goa", country: str = "India", niche: str = "Hotels", goal: int = 150, business_id: str = "gethotelstays") -> Dict[str, Any]:
    """
    Coordinates the Complete 2X Harvest & 100-Worker Screening Pipeline:
    1. Harvests 2X Buffer (e.g. Target 500 -> 1000 Raw Leads harvested).
    2. Uses High-Volume Google Maps Swarm (12 Zones, 4 safe concurrent browsers)
       combined with parallel Dorking, Instagram, Justdial, and OTA Reverse.
    3. The 100-Worker Auditor Swarm screens all 1000 leads:
       - Leads WITH website: Audited, flaws diagnosed, and MX-verified for outreach email.
       - Leads WITHOUT website (Golden Leads): Automatically routed 100% to ALORIA LABS
         for custom Web Development & Direct Booking Platform pitches!
    """
    # 2X Harvest Goal Buffer (e.g. 500 target -> 1000 leads harvested)
    harvest_goal = max(goal * 2, 60)
    per_channel_goal = max(20, harvest_goal // 5)

    print(f"\n{ui.C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{ui.RESET}")
    print(f"  {ui.C_WHITE}DEPLOYING 2X HARVEST & 100-WORKER SCREENING ENGINE{ui.RESET}")
    print(f"  {ui.C_WHITE}Target Goal:{ui.RESET} {ui.C_YELLOW}{goal} Leads{ui.RESET} │ {ui.C_WHITE}Harvest Buffer (2X):{ui.RESET} {ui.C_GREEN}{harvest_goal} Raw Leads{ui.RESET}")
    print(f"  {ui.C_WHITE}Channels:{ui.RESET} {ui.C_GREEN}[1] Maps Swarm{ui.RESET} │ {ui.C_CYAN}[2] Dorking{ui.RESET} │ {ui.C_MAGENTA}[3] Instagram{ui.RESET} │ {ui.C_YELLOW}[4] Justdial{ui.RESET} │ {ui.C_BLUE}[5] OTA Reverse{ui.RESET}")
    print(f"  {ui.C_WHITE}Screening:{ui.RESET} {ui.C_MAGENTA}100-Worker Parallel Auditor ➔ [With Web: Mail] │ [No Web: Aloria Labs Golden Lead]{ui.RESET}")
    print(f"{ui.C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{ui.RESET}\n")

    start_t = time.time()

    # Step 1A: Launch Channels 2, 3, 4, 5 in Parallel Threads
    import concurrent.futures
    import swarm_hunter

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        f_ch2 = executor.submit(hunt_google_dorking, city, country, niche, per_channel_goal, business_id)
        f_ch3 = executor.submit(hunt_instagram_bios, city, country, niche, per_channel_goal, business_id)
        f_ch4 = executor.submit(hunt_justdial_directory, city, country, niche, per_channel_goal, business_id)
        f_ch5 = executor.submit(hunt_ota_reverse, city, country, niche, per_channel_goal, business_id)

        # Step 1B: High-Volume Google Maps Swarm (12 Zones, 4 safe concurrent browsers)
        ch1_leads = swarm_hunter.hunt_with_swarm(
            city=city,
            country=country,
            niche=niche,
            goal=harvest_goal // 2,
            business_id=business_id,
            workers_count=12,
            max_concurrency=4,
            auto_audit=False
        )

        ch2_leads = f_ch2.result()
        ch3_leads = f_ch3.result()
        ch4_leads = f_ch4.result()
        ch5_leads = f_ch5.result()

    total_count = len(ch1_leads) + len(ch2_leads) + len(ch3_leads) + len(ch4_leads) + len(ch5_leads)
    elapsed = round(time.time() - start_t, 1)

    print(f"\n{ui.C_GREEN}═══════════════════════════════════════════════════════════════════════════════════════════════{ui.RESET}")
    print(f"  {ui.C_WHITE}2X HARVEST COMPLETE ({elapsed}s):{ui.RESET} Harvested {ui.C_GREEN}{total_count}{ui.RESET} raw leads into database!")
    print(f"  {ui.C_DIM}Breakdown ➔ Maps Swarm: {len(ch1_leads)} │ Dorking: {len(ch2_leads)} │ Instagram: {len(ch3_leads)} │ Justdial: {len(ch4_leads)} │ OTA Reverse: {len(ch5_leads)}{ui.RESET}")
    print(f"{ui.C_GREEN}═══════════════════════════════════════════════════════════════════════════════════════════════{ui.RESET}\n")

    # Step 2: Concurrently audit websites and extract deliverable MX-verified emails using 100 WORKERS
    import website_auditor
    print(f"  {ui.C_CYAN}[⚡ LAUNCHING 100-WORKER LIGHTWEIGHT AUDITOR & MX VERIFIER]{ui.RESET}")
    print(f"  {ui.C_DIM}Screening {total_count} leads in parallel: With Website ➔ Email Outreach │ No Website ➔ Aloria Labs Golden Leads...{ui.RESET}")
    audited = website_auditor.audit_pending_leads(limit=max(harvest_goal, total_count), business_id=business_id)
    
    verified_with_email = sum(1 for a in audited if a.get("email"))
    golden_leads_count = sum(1 for a in audited if "Golden Lead" in (a.get("audit") or ""))

    print(f"\n{ui.C_GREEN}═══════════════════════════════════════════════════════════════════════════════════════════════{ui.RESET}")
    print(f"  {ui.C_WHITE}100-WORKER SCREENING COMPLETE:{ui.RESET}")
    print(f"  {ui.C_CYAN}► Websites Audited & MX-Verified for Email Outreach:{ui.RESET} {ui.C_GREEN}{verified_with_email} Leads{ui.RESET}")
    print(f"  {ui.C_YELLOW}► Golden Leads (No Website) Auto-Assigned to ALORIA LABS:{ui.RESET} {ui.C_GREEN}{golden_leads_count} Leads{ui.RESET}")
    print(f"{ui.C_GREEN}═══════════════════════════════════════════════════════════════════════════════════════════════{ui.RESET}\n")

    return {
        "total_harvested": total_count,
        "maps": len(ch1_leads),
        "dorking": len(ch2_leads),
        "instagram": len(ch3_leads),
        "justdial": len(ch4_leads),
        "ota_reverse": len(ch5_leads),
        "verified_emails": verified_with_email,
        "golden_leads": golden_leads_count
    }

if __name__ == "__main__":
    hunt_omnichannel_swarm(city="Goa", country="India", niche="Hotels", goal=30)


