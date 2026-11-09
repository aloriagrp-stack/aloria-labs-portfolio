import os
import sys
import time
import re
import urllib.parse
import asyncio
import concurrent.futures
from typing import List, Dict, Any

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure Playwright browser path is set
if os.name == "nt" and os.path.exists("D:\\playwright-browsers"):
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "D:\\playwright-browsers"

from playwright.async_api import async_playwright
import config
import db
import ui
import json
from pathlib import Path
import website_auditor

LOCATIONS_DB_PATH = Path(__file__).resolve().parent / "india_locations.json"
INDIA_LOCATIONS_DATA = {}
STATE_DISTRICTS_INDEX = {}
ALL_DISTRICTS_INDEX = set()

def load_india_locations():
    global INDIA_LOCATIONS_DATA, STATE_DISTRICTS_INDEX, ALL_DISTRICTS_INDEX
    if LOCATIONS_DB_PATH.exists():
        try:
            with open(LOCATIONS_DB_PATH, "r", encoding="utf-8") as f:
                INDIA_LOCATIONS_DATA = json.load(f)

            # Index 28 States
            for state in INDIA_LOCATIONS_DATA.get("states", []):
                s_name = state.get("name", "").strip().lower()
                districts = state.get("districts", [])
                STATE_DISTRICTS_INDEX[s_name] = districts
                for d in districts:
                    ALL_DISTRICTS_INDEX.add(d.strip().lower())

            # Index 8 Union Territories
            for ut in INDIA_LOCATIONS_DATA.get("union_territories", []):
                ut_name = ut.get("name", "").strip().lower()
                districts = ut.get("districts_current_2026", ut.get("districts", []))
                STATE_DISTRICTS_INDEX[ut_name] = districts
                for d in districts:
                    ALL_DISTRICTS_INDEX.add(d.strip().lower())

            # Common State & Region Aliases
            aliases = {
                "up": "uttar pradesh",
                "u.p.": "uttar pradesh",
                "mp": "madhya pradesh",
                "m.p.": "madhya pradesh",
                "hp": "himachal pradesh",
                "h.p.": "himachal pradesh",
                "uk": "uttarakhand",
                "u.k.": "uttarakhand",
                "ap": "andhra pradesh",
                "a.p.": "andhra pradesh",
                "tn": "tamil nadu",
                "t.n.": "tamil nadu",
                "wb": "west bengal",
                "w.b.": "west bengal",
                "mh": "maharashtra",
                "rj": "rajasthan",
                "gj": "gujarat",
                "ka": "karnataka",
                "kl": "kerala",
                "jk": "jammu and kashmir",
                "j&k": "jammu and kashmir",
                "kashmir": "jammu and kashmir",
                "delhi": "delhi (nct of delhi)",
                "ncr": "delhi (nct of delhi)",
                "new delhi": "delhi (nct of delhi)"
            }
            for alias, target in aliases.items():
                if target in STATE_DISTRICTS_INDEX:
                    STATE_DISTRICTS_INDEX[alias] = STATE_DISTRICTS_INDEX[target]

        except Exception as e:
            print(f"  [!] Could not load india_locations.json: {e}")

load_india_locations()

# Destination Micro-Locality Knowledge Base (for deep city neighborhood partitions)
DESTINATION_MICRO_ZONES = {
    # Pan-India Nationwide Top Travel & Hotel Clusters across all States
    "india": [
        "Goa", "Jaipur Rajasthan", "Udaipur Rajasthan", "Manali Himachal", "Rishikesh Uttarakhand",
        "Munnar Kerala", "Shimla Himachal", "Ooty Tamil Nadu", "Lonavala Maharashtra", "Varanasi UP",
        "Mussoorie Uttarakhand", "Coorg Karnataka", "Dharamshala Himachal", "Pondicherry", "Agra UP",
        "Srinagar Kashmir", "Kolkata West Bengal", "Bengaluru Karnataka", "Mumbai Maharashtra", "Delhi NCR",
        "Amritsar Punjab", "Darjeeling West Bengal", "Pushkar Rajasthan", "Mount Abu Rajasthan",
        "Alleppey Kerala", "Jodhpur Rajasthan", "Jaisalmer Rajasthan", "Nainital Uttarakhand",
        "Mysore Karnataka", "Hampi Karnataka", "Gokarna Karnataka", "Kodaikanal Tamil Nadu",
        "Mahabaleshwar Maharashtra", "Gangtok Sikkim", "Shillong Meghalaya", "Hyderabad Telangana",
        "Puri Odisha", "Indore Madhya Pradesh", "Dehradun Uttarakhand", "Kochi Kerala", "Kasol Himachal", "Wayanad Kerala"
    ],
    "all india": [
        "Goa", "Jaipur Rajasthan", "Udaipur Rajasthan", "Manali Himachal", "Rishikesh Uttarakhand",
        "Munnar Kerala", "Shimla Himachal", "Ooty Tamil Nadu", "Lonavala Maharashtra", "Varanasi UP",
        "Mussoorie Uttarakhand", "Coorg Karnataka", "Dharamshala Himachal", "Pondicherry", "Agra UP",
        "Srinagar Kashmir", "Kolkata West Bengal", "Bengaluru Karnataka", "Mumbai Maharashtra", "Delhi NCR",
        "Amritsar Punjab", "Darjeeling West Bengal", "Pushkar Rajasthan", "Mount Abu Rajasthan",
        "Alleppey Kerala", "Jodhpur Rajasthan", "Jaisalmer Rajasthan", "Nainital Uttarakhand",
        "Mysore Karnataka", "Hampi Karnataka", "Gokarna Karnataka", "Kodaikanal Tamil Nadu",
        "Mahabaleshwar Maharashtra", "Gangtok Sikkim", "Shillong Meghalaya", "Hyderabad Telangana",
        "Puri Odisha", "Indore Madhya Pradesh", "Dehradun Uttarakhand", "Kochi Kerala", "Kasol Himachal", "Wayanad Kerala"
    ],
    # Specific Cities / Destinations Micro-Neighborhoods
    "goa": [
        "Calangute", "Candolim", "Anjuna", "Panaji", "Baga",
        "Morjim", "Colva", "Palolem", "Margao", "Vagator",
        "Mandrem", "Arambol", "Ashwem", "Siolim", "Cavelossim"
    ],
    "mumbai": [
        "Bandra", "Andheri", "Juhu", "Colaba", "Powai",
        "Malad", "Thane", "Navi Mumbai", "Dadar", "Borivali",
        "Lower Parel", "Worli"
    ],
    "delhi": [
        "Connaught Place", "Aerocity", "Karol Bagh", "Paharganj", "Saket",
        "Hauz Khas", "Dwarka", "South Extension", "Rohini", "Vasant Kunj",
        "Noida", "Gurugram"
    ],
    "jaipur": [
        "Bani Park", "C Scheme", "Malviya Nagar", "Mansarovar", "Vaishali Nagar",
        "Amer", "Tonk Road", "Raja Park", "MI Road", "Civil Lines",
        "Kukas", "Ajmer Road"
    ],
    "manali": [
        "Old Manali", "Mall Road", "Vashisht", "Aleo", "Naggar",
        "Solang Valley", "Jagatsukh", "Simsa", "Kullu", "Prini",
        "Rangri", "Shuru"
    ],
    "udaipur": [
        "Lake Pichola", "Fateh Sagar", "City Palace", "Sukhadia Circle", "Hiran Magri",
        "Ambamata", "Bhuwana", "Saheli Nagar", "Shobhagpura", "Kodiyat"
    ],
    "dubai": [
        "Downtown Dubai", "Dubai Marina", "Deira", "Bur Dubai", "Palm Jumeirah",
        "JBR", "Business Bay", "Al Barsha", "JLT", "Trade Centre",
        "Al Karama", "DIFC"
    ]
}

OTA_DOMAINS = [
    "booking.com", "agoda.com", "tripadvisor", "makemytrip.com",
    "goibibo.com", "expedia.com", "hotels.com", "trivago.com",
    "yatra.com", "cleartrip.com", "easemytrip.com", "oyorooms.com",
    "treebo.com", "fabhotels.com", "ixigo.com", "kayak.com",
    "hostelworld.com", "vrbo.com", "skyscanner", "lonelyplanet.com",
    "holidify.com", "thrillophilia.com", "trip.com", "travelguru.com",
    "facebook.com", "instagram.com", "justdial.com", "indiamart.com",
    "youtube.com", "twitter.com", "x.com", "linkedin.com", "airbnb", "wikipedia.org",
    # Government & Official Public Portals (Strict Zero-Crawl Rule)
    ".gov.in", ".nic.in", "gov.in", "nic.in", ".gov", ".nic", ".mil.in", ".res.in"
]

def is_ota_or_social(url: str) -> bool:
    if not url:
        return False
    try:
        from urllib.parse import urlparse
        netloc = urlparse(url).netloc.lower()
        if not netloc:
            netloc = urlparse("https://" + url).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        netloc = netloc.split(":")[0]
    except Exception:
        netloc = url.lower()

    exact_otas = {
        "booking.com", "agoda.com", "makemytrip.com", "goibibo.com",
        "expedia.com", "hotels.com", "trivago.com", "yatra.com",
        "cleartrip.com", "easemytrip.com", "oyorooms.com", "treebo.com",
        "fabhotels.com", "ixigo.com", "kayak.com", "hostelworld.com",
        "vrbo.com", "skyscanner.com", "skyscanner.net", "holidify.com",
        "thrillophilia.com", "trip.com", "travelguru.com", "airbnb.com",
        "facebook.com", "instagram.com", "justdial.com", "indiamart.com",
        "youtube.com", "twitter.com", "x.com", "linkedin.com", "wikipedia.org"
    }
    if any(netloc == dom or netloc.endswith("." + dom) for dom in exact_otas):
        return True
    if "tripadvisor." in netloc or "airbnb." in netloc:
        return True
    if any(netloc.endswith(g) or f".{g}." in netloc for g in [".gov.in", ".nic.in", "gov.in", "nic.in", ".gov", ".nic", ".mil.in", ".res.in"]):
        return True
    return False

def generate_swarm_queries(city: str, country: str, niche: str = "Hotels", count: int = 12, cycle: int = 1) -> List[Dict[str, str]]:
    """
    Partitions the target destination into 10-12 distinct micro-zones or niche variations.
    Rotates queries across cycles so that Cycle 2, 3, 4, 5... hit completely fresh untouched markets!
    - If target is 'India' or nationwide: Rotates across India's top 25+ hotel hubs.
    - If target is a State/UT: Rotates across actual districts from india_locations.json.
    - If target is a specific city: Rotates across micro-zones and specialized niche variations.
    """
    clean_city = (city or "").strip().lower()
    clean_country = (country or "").strip().lower()
    queries = []
    offset = max(0, (cycle - 1) * count)

    # 1. Check if nationwide sweep is requested
    is_nationwide = clean_city in ["india", "all india", "pan india", "bharat", "all", "entire"] or (clean_city == clean_country and clean_country in ["india", "algeria", "uae"])

    if is_nationwide and "india" in (clean_city + " " + clean_country):
        hubs = DESTINATION_MICRO_ZONES["india"]
        for idx in range(count):
            hub = hubs[(offset + idx) % len(hubs)]
            queries.append({
                "worker_id": f"Hunter-{idx+1:02d}",
                "zone": hub,
                "city_override": hub,
                "query": f"{niche} in {hub}, India"
            })
        return queries

    # 2. Check if a State or Union Territory was specified from india_locations.json
    matched_state = None
    matched_districts = None

    for s_name, d_list in STATE_DISTRICTS_INDEX.items():
        if s_name == clean_city or clean_city in s_name or s_name in clean_city:
            matched_state = s_name.title()
            matched_districts = d_list
            break

    if matched_districts:
        # Rotate districts across cycles so subsequent waves hit fresh cities in the state
        for idx in range(count):
            dist = matched_districts[(offset + idx) % len(matched_districts)]
            queries.append({
                "worker_id": f"Hunter-{idx+1:02d}",
                "zone": dist,
                "city_override": dist,
                "query": f"{niche} in {dist}, {matched_state}"
            })
        return queries

    # 3. Check if we have pre-mapped micro-zones for this city
    matched_zones = None
    for k, zones in DESTINATION_MICRO_ZONES.items():
        if k == clean_city or k in clean_city or clean_city in k:
            matched_zones = zones
            break

    if matched_zones:
        # Rotate micro-zones across waves
        for idx in range(count):
            zone = matched_zones[(offset + idx) % len(matched_zones)]
            q = f"{niche} in {zone}, {city}"
            queries.append({
                "worker_id": f"Hunter-{idx+1:02d}",
                "zone": zone,
                "city_override": zone if clean_city in DESTINATION_MICRO_ZONES else city,
                "query": q
            })
        return queries

    # 4. Fallback to high-yield keyword variations + geographical quadrant partitions
    variations = [
        f"Boutique {niche} in {city}, {country}",
        f"Luxury {niche} in {city}, {country}",
        f"Resorts and {niche} in {city}, {country}",
        f"Homestays and {niche} in {city}, {country}",
        f"Independent {niche} in {city}, {country}",
        f"Heritage {niche} in {city}, {country}",
        f"Villas and {niche} in {city}, {country}",
        f"Guest Houses in {city}, {country}",
        f"{niche} in North {city}, {country}",
        f"{niche} in South {city}, {country}",
        f"{niche} in Central {city}, {country}",
        f"Top rated {niche} in {city}, {country}",
        f"Beach stays in {city}, {country}",
        f"Cottages in {city}, {country}",
        f"Bed and Breakfast in {city}, {country}",
        f"Budget {niche} in {city}, {country}"
    ]
    for idx in range(count):
        v = variations[(offset + idx) % len(variations)]
        queries.append({
            "worker_id": f"Hunter-{idx+1:02d}",
            "zone": f"Zone-{idx+1}",
            "city_override": city,
            "query": v
        })

    return queries

async def _scrape_single_tab(
    page,
    worker_info: Dict[str, str],
    max_places: int = 25,
    business_id: str = "gethotelstays",
    city: str = "",
    country: str = "",
    niche: str = "",
    existing_names: set | None = None
) -> List[Dict[str, Any]]:
    """
    Scrapes Google Maps search results inside a dedicated tab of the single shared Chromium browser.
    """
    worker_id = worker_info["worker_id"]
    query = worker_info["query"]
    zone = worker_info["zone"]
    discovered = []

    try:
        search_url = f"https://www.google.com/maps/search/{urllib.parse.quote_plus(query)}?hl=en"
        for attempt in range(2):
            try:
                await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
                break
            except Exception as nav_err:
                if attempt == 0:
                    await asyncio.sleep(1.0)
                    continue
                raise nav_err

        await asyncio.sleep(1.2)

        # Accept consent if prompted
        try:
            consent_locators = [
                "button:has-text('Accept all')",
                "button:has-text('I agree')",
                "button[aria-label*='Accept all']",
                "form[action*='consent'] button"
            ]
            for c_sel in consent_locators:
                btn = page.locator(c_sel).first
                if await btn.is_visible(timeout=800):
                    await btn.click()
                    await asyncio.sleep(0.8)
                    break
        except Exception:
            pass

        # Wait for results feed
        feed_selector = 'div[role="feed"]'
        try:
            await page.wait_for_selector(feed_selector, timeout=12000)
        except Exception:
            pass

        # Smooth adaptive scroll of results feed (6-10 scrolls with 0.6s delay for full network tile hydration)
        scrolls = max(6, min(12, (max_places // 2) + 2))
        for _ in range(scrolls):
            try:
                feed = page.locator(feed_selector)
                await feed.evaluate("el => el.scrollBy(0, 3500)")
                await asyncio.sleep(0.6)
            except Exception:
                await page.mouse.wheel(0, 1500)
                await asyncio.sleep(0.6)

        # Instant DOM Batch Extraction via JavaScript (0.01 seconds)
        feed_items = await page.evaluate("""() => {
            const results = [];
            const cards = document.querySelectorAll('div[role="feed"] > div');
            for (const card of cards) {
                const link = card.querySelector('a[href*="/maps/place/"]');
                if (!link) continue;
                const title = link.getAttribute('aria-label') || link.innerText.split('\\n')[0] || '';
                if (!title || title.toLowerCase().includes('sponsored') || title.includes('\\ue5d4')) continue;
                
                const webBtn = card.querySelector('a[data-value="Website"], a[aria-label*="Website"], a[aria-label*="website"], a[data-item-id="authority"]');
                const website = webBtn ? webBtn.getAttribute('href') : null;
                const text = card.innerText || '';

                // Extract any mailto links in card
                const mailBtn = card.querySelector('a[href^="mailto:"]');
                let cardEmail = mailBtn ? mailBtn.getAttribute('href').replace(/^mailto:/i, '').split('?')[0].trim() : null;

                // Check text for email regex
                if (!cardEmail && text.includes('@')) {
                    const emMatch = text.match(/[a-zA-Z0-9_.+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}/);
                    if (emMatch) cardEmail = emMatch[0].trim();
                }

                results.push({title, website, text, href: link.getAttribute('href'), email: cardEmail});
            }
            return results;
        }""")

        if existing_names is None:
            existing_names = db.get_existing_business_names_set()
        seen_titles = set()
        count = 0

        # Process extracted items
        for item in feed_items:
            if count >= max_places:
                break

            title = item.get("title", "").strip()
            # ULTRA-FAST DEDUPLICATION: Skip in 0.0001s if already in DB or seen
            if not title or title in seen_titles or title.lower() in existing_names:
                continue
            seen_titles.add(title)

            website_url = item.get("website")
            if website_url and "google.com/url?" in website_url:
                match = re.search(r'url=([^&]+)', website_url)
                if match:
                    website_url = urllib.parse.unquote(match.group(1))

            if website_url:
                if is_ota_or_social(website_url):
                    website_url = None

            card_text = item.get("text", "")
            direct_email = item.get("email")
            if not direct_email and "@" in card_text:
                m_em = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', card_text)
                if m_em:
                    direct_email = m_em.group(0).strip()

            # Extract Phone from card text
            phone_match = re.search(r'(?:\+91[\-\s]?)?[6-9]\d{9}|\b0\d{2,4}[\-\s]?\d{6,8}\b', card_text)
            phone = phone_match.group(0).strip() if phone_match else None

            # Extract Rating from card text
            rating_match = re.search(r'([3-5]\.\d)\s*(?:stars?|rating|\/5|\(\d+\))', card_text)
            rating = rating_match.group(1) if rating_match else None

            # Extract Reviews count
            rev_match = re.search(r'\(([0-9,]+)\)', card_text)
            reviews_count = rev_match.group(1).replace(",", "") if rev_match else None

            # Extract Address from card text
            addr_match = re.search(r'(?:Near|Opposite|Road|Nagar|Colony|Beach|Lane|Street|Marg|Bazaar)[^,\.\n]+', card_text, flags=re.I)
            address = addr_match.group(0).strip() if addr_match else f"{zone or city}, {country}"

            # Only open place detail page if website URL was NOT already present in search card
            place_href = item.get("href")
            if not website_url and place_href and place_href.startswith("http"):
                dp = None
                try:
                    dp = await page.context.new_page()
                    await dp.goto(place_href, wait_until="domcontentloaded", timeout=7000)
                    await asyncio.sleep(0.3)

                    # 1. Extract Website URL
                    web_btn = dp.locator('a[data-item-id="authority"], a[data-tooltip*="website" i], a[aria-label*="website" i], a[data-value="Website"]').first
                    if await web_btn.is_visible(timeout=1000):
                        w_href = await web_btn.get_attribute("href")
                        if w_href and "google.com/url?" in w_href:
                            m = re.search(r'url=([^&]+)', w_href)
                            if m:
                                w_href = urllib.parse.unquote(m.group(1))
                        if w_href and not is_ota_or_social(w_href):
                            website_url = w_href

                    # 2. Extract Phone if not already captured
                    if not phone:
                        try:
                            phone_loc = dp.locator('button[data-tooltip*="phone" i], button[aria-label*="phone" i], button[data-item-id*="phone"]').first
                            if await phone_loc.is_visible(timeout=400):
                                phone_aria = await phone_loc.get_attribute("aria-label") or await phone_loc.inner_text()
                                if phone_aria:
                                    phone_m = re.search(r'(?:\+91[\-\s]?)?[6-9]\d{9}|\b0\d{2,4}[\-\s]?\d{6,8}\b', phone_aria)
                                    if phone_m:
                                        phone = phone_m.group(0).strip()
                        except Exception:
                            pass
                except Exception:
                    pass
                finally:
                    if dp:
                        try:
                            await dp.close()
                        except Exception:
                            pass

            # REAL-TIME WEBSITE & FOOTPRINT EMAIL EXTRACTION (Every Tab Audits Its Leads Live!)
            lead_city = worker_info.get("city_override") or zone or city
            if not direct_email and website_url:
                try:
                    temp_lead = {
                        "id": 0,
                        "business_name": title,
                        "website_url": website_url,
                        "city": lead_city,
                        "email": None,
                        "business_id": business_id
                    }
                    audit_res = await asyncio.to_thread(website_auditor.audit_single_website, temp_lead)
                    if audit_res and audit_res.get("email"):
                        direct_email = audit_res.get("email")
                except Exception:
                    pass

            if not direct_email and not website_url:
                try:
                    fp_emails = await asyncio.to_thread(website_auditor.hunt_email_via_search_footprint, title, lead_city, "")
                    for f_em in fp_emails:
                        verified = website_auditor.clean_and_verify_email(f_em, check_mx=True)
                        if verified:
                            direct_email = verified
                            break
                except Exception:
                    pass

            if direct_email:
                direct_email = website_auditor.clean_email(direct_email)

            # STRICT ACTIONABLE CONTACT GATE:
            # If a candidate has NO website, NO email, AND NO phone number, it's a ghost lead! Discard immediately!
            if not website_url and not direct_email and not phone:
                continue

            # Golden Lead Rule: If lead has NO website, route 100% to Aloria Labs (Web Dev pitch target)
            target_biz_id = "aloria_labs" if not website_url else business_id
            lead_id = db.insert_lead(
                business_name=title,
                country=country or "India",
                city=lead_city,
                niche=niche or "Hotels",
                address=address,
                phone=phone,
                rating=rating,
                reviews_count=reviews_count,
                website_url=website_url,
                business_id=target_biz_id,
                email=direct_email
            )

            existing_names.add(title.lower())
            if lead_id:
                discovered.append({
                    "id": lead_id,
                    "name": title,
                    "has_website": bool(website_url),
                    "website_url": website_url,
                    "phone": phone,
                    "rating": rating,
                    "reviews": reviews_count,
                    "zone": zone,
                    "email": direct_email
                })
                count += 1
                email_badge = f"{ui.C_GREEN}{direct_email}{ui.RESET}" if direct_email else f"{ui.C_DIM}Pending web{ui.RESET}"
                sys.stdout.write(f"\r  {ui.C_GREEN}[✓ {worker_id} (Tab)]{ui.RESET} Harvested: {title[:22]} │ {email_badge} │ Tab: {count}/{max_places}   \n")
                sys.stdout.flush()

    except Exception as e:
        print(f"\n  {ui.C_RED}[!] {worker_id} (Tab) encountered issue on '{query}': {e}{ui.RESET}")

    return discovered

async def _hunt_with_swarm_async(
    city: str = "Goa",
    country: str = "India",
    niche: str = "Hotels",
    goal: int = 150,
    business_id: str = "gethotelstays",
    workers_count: int = 12,
    headless: bool = False,
    cycle: int = 1,
    max_concurrency: int = 12
) -> List[Dict[str, Any]]:
    queries = generate_swarm_queries(city, country, niche, count=workers_count, cycle=cycle)
    per_worker_quota = max(15, min(35, (goal // len(queries)) + 5))

    print(f"  {ui.C_YELLOW}[*] Generated {len(queries)} micro-locality search partitions across {city} (Wave Cycle #{cycle}):{ui.RESET}")
    for q_item in queries:
        print(f"      {ui.C_CYAN}► {q_item['worker_id']}:{ui.RESET} {q_item['query']}")
    print()

    concurrency_limit = max(1, min(12, max_concurrency or workers_count))
    print(f"  {ui.C_CYAN}[⚡ HIGH-EFFICIENCY BROWSER SWARM]{ui.RESET} Launching Chromium engine ({len(queries)} micro-zones, all {concurrency_limit} concurrent tabs active)...")

    async with async_playwright() as p:
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--disable-extensions",
            "--disable-background-networking",
            "--blink-settings=imagesEnabled=false",
            "--js-flags=--max-old-space-size=1024"
        ]
        if headless:
            launch_args.extend(["--headless=new", "--window-position=-2400,-2400"])

        browser = await p.chromium.launch(
            headless=headless,
            args=launch_args
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            locale="en-US"
        )

        # Load existing database names once for all tabs (0.05s)
        shared_existing_names = db.get_existing_business_names_set()

        sem = asyncio.Semaphore(concurrency_limit)

        async def _run_worker(q_info, idx):
            async with sem:
                if idx > 0:
                    await asyncio.sleep(0.25)
                page = await context.new_page()
                try:
                    return await _scrape_single_tab(
                        page=page,
                        worker_info=q_info,
                        max_places=per_worker_quota,
                        business_id=business_id,
                        city=city,
                        country=country,
                        niche=niche,
                        existing_names=shared_existing_names
                    )
                finally:
                    try:
                        await page.close()
                    except Exception:
                        pass

        tasks = [_run_worker(q, i) for i, q in enumerate(queries)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_discovered = []
        for idx, res in enumerate(results):
            q_info = queries[idx]
            if isinstance(res, Exception):
                print(f"\n  {ui.C_RED}[!] Tab {q_info['worker_id']} encountered error: {res}{ui.RESET}")
            elif isinstance(res, list):
                total_discovered.extend(res)
                print(f"\n  {ui.C_GREEN}[✓ Tab {q_info['worker_id']} COMPLETED]{ui.RESET} Captured {len(res)} unique properties in {q_info['zone']}.")

        try:
            await context.close()
        except Exception:
            pass
        try:
            await browser.close()
        except Exception:
            pass
        import gc
        gc.collect()
        return total_discovered

def hunt_with_swarm(
    city: str = "Goa",
    country: str = "India",
    niche: str = "Hotels",
    goal: int = 150,
    business_id: str = "gethotelstays",
    workers_count: int = 12,
    max_concurrency: int = 12,
    auto_audit: bool = True,
    headless: bool | None = None,
    cycle: int = 1
) -> List[Dict[str, Any]]:
    """
    Master 1-Browser Multi-Tab Swarm Coordinator:
    1. Launches 1 SINGLE Chromium browser instance.
    2. Opens tabs inside that single browser window bounded by concurrency semaphore.
    3. Concurrently scrapes partitioned queries across the tabs.
    4. Aggregates all freshly discovered candidate properties.
    5. Automatically launches parallel website auditing & MX email verification (if auto_audit=True).
    """
    if headless is None:
        headless = getattr(config, "HEADLESS", False)

    print(f"\n{ui.C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{ui.RESET}")
    print(f"  {ui.C_WHITE}DEPLOYING 1-BROWSER PARALLEL HUNTER SWARM{ui.RESET}")
    print(f"  {ui.C_WHITE}Target:{ui.RESET} {ui.C_YELLOW}{niche} in {city}, {country}{ui.RESET} │ {ui.C_WHITE}Goal Buffer:{ui.RESET} {ui.C_GREEN}{goal} Leads{ui.RESET} │ {ui.C_WHITE}Partitions:{ui.RESET} {ui.C_MAGENTA}{workers_count} Zones{ui.RESET}")
    print(f"{ui.C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{ui.RESET}\n")

    start_time = time.time()

    # Safely run asyncio in any calling context (whether sync thread or running loop)
    def _run_async(coro_fn, *args):
        def _runner():
            return asyncio.run(coro_fn(*args))

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(_runner).result()
        else:
            return asyncio.run(coro_fn(*args))

    total_discovered = _run_async(
        _hunt_with_swarm_async,
        city,
        country,
        niche,
        goal,
        business_id,
        workers_count,
        headless,
        cycle,
        max_concurrency
    )

    elapsed = round(time.time() - start_time, 1)
    print(f"\n{ui.C_GREEN}═══════════════════════════════════════════════════════════════════════════════════════════════{ui.RESET}")
    print(f"  {ui.C_WHITE}1-BROWSER 10-TAB HUNT COMPLETE:{ui.RESET} Discovered {ui.C_GREEN}{len(total_discovered)}{ui.RESET} properties across {workers_count} tabs in {elapsed}s!")
    print(f"{ui.C_GREEN}═══════════════════════════════════════════════════════════════════════════════════════════════{ui.RESET}\n")

    if auto_audit:
        # Step 2: Concurrently audit websites and extract deliverable MX-verified emails
        print(f"  {ui.C_CYAN}[⚡ LAUNCHING 100-WORKER PARALLEL AUDITOR & MX VERIFIER]{ui.RESET}")
        audited = website_auditor.audit_pending_leads(limit=max(goal, len(total_discovered)), business_id=business_id)
        verified_with_email = sum(1 for a in audited if a.get("email"))
        print(f"\n  {ui.C_GREEN}✓ BUFFERING COMPLETE: {verified_with_email} fresh leads with 100% verified deliverable emails now buffered in database!{ui.RESET}\n")

    return total_discovered

if __name__ == "__main__":
    # Test execution: 1 browser with 4 tabs
    hunt_with_swarm(city="Goa", country="India", niche="Hotels", goal=20, business_id="gethotelstays", workers_count=4, headless=False)
