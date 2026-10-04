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
    # Pan-India Nationwide Top Travel & Hotel Clusters
    "india": [
        "Goa", "Jaipur", "Udaipur", "Manali", "Rishikesh",
        "Munnar Kerala", "Shimla", "Ooty", "Lonavala", "Varanasi",
        "Mussoorie", "Coorg", "Dharamshala", "Pondicherry", "Agra",
        "Srinagar", "Kolkata", "Bengaluru", "Mumbai", "Delhi",
        "Amritsar", "Darjeeling", "Pushkar", "Mount Abu"
    ],
    "all india": [
        "Goa", "Jaipur", "Udaipur", "Manali", "Rishikesh",
        "Munnar Kerala", "Shimla", "Ooty", "Lonavala", "Varanasi",
        "Mussoorie", "Coorg", "Dharamshala", "Pondicherry", "Agra",
        "Srinagar", "Kolkata", "Bengaluru", "Mumbai", "Delhi",
        "Amritsar", "Darjeeling", "Pushkar", "Mount Abu"
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
    "youtube.com", "twitter.com", "x.com", "linkedin.com", "airbnb", "wikipedia.org"
]

def generate_swarm_queries(city: str, country: str, niche: str = "Hotels", count: int = 12) -> List[Dict[str, str]]:
    """
    Partitions the target destination into 10-12 distinct micro-zones or niche variations.
    - If target is 'India' or nationwide: Spreads 12 workers across India's top hotel hubs.
    - If target is a State/UT (e.g. 'Uttar Pradesh', 'Maharashtra', 'Kerala'): Pulls 12 actual districts from india_locations.json.
    - If target is a specific city: Pulls micro-zones or generates 12 keyword variations.
    """
    clean_city = (city or "").strip().lower()
    clean_country = (country or "").strip().lower()
    queries = []

    # 1. Check if nationwide sweep is requested (city is 'india', 'all india', 'pan india', or city matches country)
    is_nationwide = clean_city in ["india", "all india", "pan india", "bharat", "all", "entire"] or (clean_city == clean_country and clean_country in ["india", "algeria", "uae"])

    if is_nationwide and "india" in (clean_city + " " + clean_country):
        hubs = DESTINATION_MICRO_ZONES["india"]
        for idx, hub in enumerate(hubs[:count]):
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
        # User specified a state (e.g., "Uttar Pradesh", "Himachal Pradesh", "Kerala")
        # Distribute 12 workers across 12 distinct districts/cities in that state
        for idx, dist in enumerate(matched_districts[:count]):
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
        for idx, zone in enumerate(matched_zones[:count]):
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
        f"Top rated {niche} in {city}, {country}"
    ]
    for idx, v in enumerate(variations[:count]):
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
    niche: str = ""
) -> List[Dict[str, Any]]:
    """
    Scrapes Google Maps search results inside a dedicated tab of the single shared Chromium browser.
    """
    worker_id = worker_info["worker_id"]
    query = worker_info["query"]
    zone = worker_info["zone"]
    discovered = []

    try:
        # Route Interception: Abort images, fonts, media to keep RAM and CPU feather-light
        async def _block_heavy_assets(route):
            try:
                req_type = route.request.resource_type
                if req_type in ["image", "media", "font"]:
                    await route.abort()
                elif any(bad in route.request.url for bad in ["google-analytics", "doubleclick", "googletagmanager"]):
                    await route.abort()
                else:
                    await route.continue_()
            except Exception:
                pass

        await page.route("**/*", _block_heavy_assets)

        search_url = f"https://www.google.com/maps/search/{urllib.parse.quote_plus(query)}?hl=en"
        await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
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

        # Fast smooth scroll of results feed (3-5 scrolls)
        scrolls = max(3, min(6, (max_places // 5) + 1))
        for _ in range(scrolls):
            try:
                feed = page.locator(feed_selector)
                await feed.evaluate("el => el.scrollBy(0, 4000)")
                await asyncio.sleep(0.35)
            except Exception:
                await page.mouse.wheel(0, 1500)
                await asyncio.sleep(0.35)

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
                results.push({title, website, text, href: link.getAttribute('href')});
            }
            return results;
        }""")

        seen_titles = set()
        count = 0

        # Process extracted items
        for item in feed_items:
            if count >= max_places:
                break

            title = item.get("title", "").strip()
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)

            website_url = item.get("website")
            if website_url and "google.com/url?" in website_url:
                match = re.search(r'url=([^&]+)', website_url)
                if match:
                    website_url = urllib.parse.unquote(match.group(1))

            if website_url:
                lower_url = website_url.lower()
                if any(dom in lower_url for dom in OTA_DOMAINS):
                    website_url = None

            card_text = item.get("text", "")

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

            # Quick click on card if website button wasn't immediately on card face
            if not website_url and count < 6:
                try:
                    card_link = page.locator(f'a[aria-label="{title}"], a[href*="/maps/place/"]:has-text("{title[:15]}")').first
                    if await card_link.is_visible(timeout=400):
                        await card_link.click(timeout=600)
                        await asyncio.sleep(0.25)
                        web_btn = page.locator('a[data-item-id="authority"], a[aria-label*="Website"], a[aria-label*="website"]').first
                        if await web_btn.is_visible(timeout=400):
                            w_href = await web_btn.get_attribute("href")
                            if w_href and "google.com/url?" in w_href:
                                m = re.search(r'url=([^&]+)', w_href)
                                if m:
                                    w_href = urllib.parse.unquote(m.group(1))
                            if w_href and not any(dom in w_href.lower() for dom in OTA_DOMAINS):
                                website_url = w_href
                except Exception:
                    pass

            # Insert into SQLite Database
            lead_city = worker_info.get("city_override") or zone or city
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
                business_id=business_id
            )

            if lead_id:
                discovered.append({
                    "id": lead_id,
                    "name": title,
                    "has_website": bool(website_url),
                    "website_url": website_url,
                    "phone": phone,
                    "rating": rating,
                    "reviews": reviews_count,
                    "zone": zone
                })
                count += 1
                sys.stdout.write(f"\r  {ui.C_GREEN}[✓ {worker_id} (Tab)]{ui.RESET} Harvested: {title[:26]} ({zone}) | Tab: {count}/{max_places}   ")
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
    workers_count: int = 10,
    headless: bool = False
) -> List[Dict[str, Any]]:
    queries = generate_swarm_queries(city, country, niche, count=workers_count)
    per_worker_quota = max(15, min(35, (goal // len(queries)) + 5))

    print(f"  {ui.C_YELLOW}[*] Generated {len(queries)} micro-locality search partitions across {city}:{ui.RESET}")
    for q_item in queries:
        print(f"      {ui.C_CYAN}► {q_item['worker_id']}:{ui.RESET} {q_item['query']}")
    print()

    print(f"  {ui.C_CYAN}[⚡ 1-BROWSER 10-TABS ARCHITECTURE]{ui.RESET} Launching 1 single Chromium browser with {len(queries)} parallel tabs...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage"
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            locale="en-US"
        )

        # Create all tabs inside the SAME single browser window
        tabs = [await context.new_page() for _ in range(len(queries))]
        print(f"  {ui.C_GREEN}[✓]{ui.RESET} Opened {len(tabs)} tabs in single browser window. Executing parallel scraping across all tabs...\n")

        async def _run_tab(tab_idx):
            page = tabs[tab_idx]
            q_info = queries[tab_idx]
            if tab_idx > 0:
                await asyncio.sleep(tab_idx * 0.35)  # 350ms smooth stagger
            return await _scrape_single_tab(
                page=page,
                worker_info=q_info,
                max_places=per_worker_quota,
                business_id=business_id,
                city=city,
                country=country,
                niche=niche
            )

        tasks = [_run_tab(i) for i in range(len(queries))]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_discovered = []
        for idx, res in enumerate(results):
            q_info = queries[idx]
            if isinstance(res, Exception):
                print(f"\n  {ui.C_RED}[!] Tab {q_info['worker_id']} encountered error: {res}{ui.RESET}")
            elif isinstance(res, list):
                total_discovered.extend(res)
                print(f"\n  {ui.C_GREEN}[✓ Tab {q_info['worker_id']} COMPLETED]{ui.RESET} Captured {len(res)} unique properties in {q_info['zone']}.")

        await context.close()
        await browser.close()
        return total_discovered

def hunt_with_swarm(
    city: str = "Goa",
    country: str = "India",
    niche: str = "Hotels",
    goal: int = 150,
    business_id: str = "gethotelstays",
    workers_count: int = 10,
    max_concurrency: int = 10,
    auto_audit: bool = True,
    headless: bool | None = None
) -> List[Dict[str, Any]]:
    """
    Master 1-Browser Multi-Tab Swarm Coordinator:
    1. Launches 1 SINGLE Chromium browser instance.
    2. Opens 10 tabs inside that single browser window.
    3. Concurrently scrapes partitioned queries across the 10 tabs.
    4. Aggregates all freshly discovered candidate properties.
    5. Automatically launches parallel website auditing & MX email verification (if auto_audit=True).
    """
    if headless is None:
        headless = getattr(config, "HEADLESS", False)

    print(f"\n{ui.C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{ui.RESET}")
    print(f"  {ui.C_WHITE}DEPLOYING 1-BROWSER 10-TABS PARALLEL HUNTER SWARM{ui.RESET}")
    print(f"  {ui.C_WHITE}Target:{ui.RESET} {ui.C_YELLOW}{niche} in {city}, {country}{ui.RESET} │ {ui.C_WHITE}Goal Buffer:{ui.RESET} {ui.C_GREEN}{goal} Leads{ui.RESET} │ {ui.C_WHITE}Tabs in 1 Browser:{ui.RESET} {ui.C_MAGENTA}{workers_count} Tabs{ui.RESET}")
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
        headless
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
