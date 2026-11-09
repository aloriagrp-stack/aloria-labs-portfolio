import os
import sys
import time
import re
import asyncio
import urllib.parse
from typing import List, Dict, Any, Optional

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Set Playwright browser path if exists
if os.path.exists("D:\\playwright-browsers"):
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "D:\\playwright-browsers"

try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None

import config
import db
import ui
import email_verifier

OTA_DOMAINS = {
    "booking.com", "agoda.com", "makemytrip.com", "goibibo.com",
    "expedia.com", "hotels.com", "trivago.com", "facebook.com",
    "instagram.com", "justdial.com", "indiamart.com", "tripadvisor.com"
}

def is_ota_domain(url: str) -> bool:
    if not url:
        return False
    try:
        from urllib.parse import urlparse
        netloc = urlparse(url if url.startswith("http") else "https://" + url).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        netloc = netloc.split(":")[0]
        return any(netloc == dom or netloc.endswith("." + dom) or dom in netloc for dom in OTA_DOMAINS)
    except Exception:
        return False

async def _inspect_candidate_tab(
    context,
    item: Dict[str, Any],
    city: str,
    country: str,
    niche: str,
    business_id: str,
    sem: asyncio.Semaphore,
    discovered_list: List[Dict[str, Any]],
    existing_names: set,
    on_step=None,
    total_target: int = 100
):
    """
    Inspects a single lead candidate inside a dedicated tab in the shared Chromium browser.
    """
    async with sem:
        title = item.get("title", "").strip()
        if not title or title.lower() in existing_names:
            return

        # Skip sponsored ads / aggregators
        if "sponsored" in title.lower() or "\nby " in title.lower() or "\ue5d4" in title:
            return

        place_url = item.get("href")
        website_url = item.get("website")
        email = item.get("email")
        phone = None
        address = None
        rating = None
        reviews_count = None

        if website_url and "google.com/url?" in website_url:
            m = re.search(r'url=([^&]+)', website_url)
            if m:
                website_url = urllib.parse.unquote(m.group(1))

        if website_url and is_ota_domain(website_url):
            website_url = None

        # Clean email from card if present
        if email:
            valid_em, clean_em = email_verifier.is_valid_clean_email(email)
            email = clean_em if valid_em else None

        # If we need more data (phone, address, reviews, website/email), inspect the detail tab
        if place_url and place_url.startswith("https://"):
            dp = None
            try:
                dp = await context.new_page()
                await dp.goto(place_url, wait_until="domcontentloaded", timeout=18000)
                await asyncio.sleep(0.8)

                # Extract Title if missing
                if not title:
                    try:
                        title_loc = dp.locator('h1.DUwDvf, div.lMbq3e h1, h1[tabindex="-1"]').first
                        if await title_loc.is_visible(timeout=1200):
                            t_text = (await title_loc.inner_text()).strip()
                            if t_text:
                                title = t_text.split("\n")[0].strip()
                    except Exception:
                        pass

                # Extract Website if not already found
                if not website_url:
                    try:
                        web_btn = dp.locator('a[data-item-id="authority"], a[data-tooltip*="website" i], a[aria-label*="website" i], a[data-value="Website"]').first
                        if await web_btn.is_visible(timeout=1000):
                            w_href = await web_btn.get_attribute("href")
                            if w_href and "google.com/url?" in w_href:
                                m = re.search(r'url=([^&]+)', w_href)
                                if m:
                                    w_href = urllib.parse.unquote(m.group(1))
                            if w_href and not is_ota_domain(w_href):
                                website_url = w_href
                    except Exception:
                        pass

                # Extract Email from Mailto or Detail Pane
                if not email:
                    try:
                        mail_loc = dp.locator('a[href^="mailto:"]').first
                        if await mail_loc.is_visible(timeout=600):
                            m_href = await mail_loc.get_attribute("href")
                            if m_href and "@" in m_href:
                                cand_em = m_href.replace("mailto:", "").split("?")[0].strip()
                                valid_em, clean_em = email_verifier.is_valid_clean_email(cand_em)
                                if valid_em:
                                    email = clean_em
                    except Exception:
                        pass

                if not email:
                    try:
                        pane_el = dp.locator('div[role="main"], div.m6QErb').first
                        if await pane_el.is_visible(timeout=600):
                            p_txt = await pane_el.inner_text()
                            if "@" in p_txt:
                                matches = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', p_txt)
                                for cand_em in matches:
                                    valid_em, clean_em = email_verifier.is_valid_clean_email(cand_em)
                                    if valid_em:
                                        email = clean_em
                                        break
                    except Exception:
                        pass

                # Extract Phone
                try:
                    phone_loc = dp.locator('button[data-item-id*="phone:"], button[aria-label*="Phone" i], button[data-tooltip*="phone" i]').first
                    if await phone_loc.is_visible(timeout=800):
                        phone_text = (await phone_loc.inner_text()).strip()
                        clean_p = re.sub(r'[^\d+\-\s\(\)]', '', phone_text).strip()
                        if clean_p:
                            phone = re.sub(r'\s+', ' ', clean_p).strip()
                except Exception:
                    pass

                # Extract Address
                try:
                    addr_loc = dp.locator('button[data-item-id="address"], button[aria-label*="Address"]').first
                    if await addr_loc.is_visible(timeout=800):
                        address = (await addr_loc.inner_text()).strip()
                except Exception:
                    pass

                # Extract Rating & Reviews
                try:
                    rating_loc = dp.locator('div.F7nice span[aria-hidden="true"]').first
                    if await rating_loc.is_visible(timeout=800):
                        rating = (await rating_loc.inner_text()).strip()
                    rev_loc = dp.locator('div.F7nice span[aria-label*="reviews"]').first
                    if await rev_loc.is_visible(timeout=800):
                        reviews_count = re.sub(r'[^\d]', '', (await rev_loc.inner_text()).strip())
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

        if not title or title.lower() in existing_names:
            return

        # STRICT ACTIONABLE CONTACT GATE:
        # If a candidate has NO website, NO email, AND NO phone number, it's a ghost lead! Discard immediately!
        if not website_url and not email and not phone:
            return

        # Insert into SQLite State Machine
        assigned_business_id = business_id or "aloria_labs"
        lead_id = db.insert_lead(
            business_name=title,
            country=country,
            city=city,
            niche=niche,
            address=address,
            phone=phone,
            rating=rating,
            reviews_count=reviews_count,
            website_url=website_url,
            business_id=assigned_business_id,
            email=email
        )

        if lead_id is None:
            existing_names.add(title.lower())
            return

        existing_names.add(title.lower())
        captured_idx = len(discovered_list) + 1
        ui.log_discovered_place(captured_idx, total_target, title, website_url, phone, rating)

        if on_step:
            if email:
                on_step(f"🎯 [{captured_idx}/{total_target}] Captured '{title}' — Email: {email} (Verified) | Site: {website_url or 'None'}")
            elif not website_url:
                on_step(f"★ [{captured_idx}/{total_target}] Golden Lead: '{title}' (Zero Website — Routed to Web Dev)")
            else:
                on_step(f"✓ [{captured_idx}/{total_target}] Captured '{title}' (Domain: {website_url})")

        discovered_list.append({
            "id": lead_id,
            "name": title,
            "has_website": bool(website_url),
            "website_url": website_url,
            "email": email,
            "phone": phone,
            "rating": rating,
            "reviews": reviews_count
        })

async def _async_multi_tab_crawl_maps(
    city: str = "Mumbai",
    country: str = "India",
    niche: str = "Restaurants",
    max_places: int = 100,
    headless: bool = True,
    business_id: str = "aloria_labs",
    on_step=None,
    should_stop=None
) -> List[Dict[str, Any]]:
    """
    Single Browser Instance + Parallel Multi-Tab Swarm (Jaala Fekna)
    Runs 1 Chromium process, opens 1 Master Tab to collect candidate cards,
    and deploys 8-10 parallel worker tabs inside the SAME browser to capture 100 leads concurrently.
    """
    discovered: List[Dict[str, Any]] = []

    if async_playwright is None:
        err = "Playwright async is not available. Please ensure playwright is installed."
        print(f"  {ui.C_RED}[ERROR] {err}{ui.RESET}")
        if on_step:
            on_step(f"Error: {err}")
        return discovered

    # Clean query formatting (avoid redundant "Hotels in Dubai, UAE, UAE" or "Hotels in Dubai, India")
    clean_city = str(city or "").strip()
    clean_country = str(country or "").strip()
    if clean_country and clean_country.lower() in clean_city.lower():
        query = f"{niche} in {clean_city}"
    elif clean_country:
        query = f"{niche} in {clean_city}, {clean_country}"
    else:
        query = f"{niche} in {clean_city}"

    print(f"  {ui.C_CYAN}[⚡ MULTI-TAB SWARM NET]{ui.RESET} Query: '{ui.C_WHITE}{query}{ui.RESET}' │ Target: {ui.C_YELLOW}{max_places}{ui.RESET} leads │ Tabs: {ui.C_GREEN}8 Concurrent{ui.RESET}")
    if on_step:
        on_step(f"Launching Single-Browser Multi-Tab Swarm Net for {max_places} {niche} in {clean_city}...")

    async with async_playwright() as p:
        browser = None
        context = None
        try:
            launch_args = [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-default-apps",
                "--blink-settings=imagesEnabled=false",
                "--js-flags=--max-old-space-size=512"
            ]
            if headless:
                launch_args.extend(["--headless=new", "--window-position=-2400,-2400"])
            else:
                launch_args.append("--start-maximized")

            # 1 SINGLE CHROMIUM BROWSER INSTANCE
            browser = await p.chromium.launch(headless=headless, args=launch_args)
            context = await browser.new_context(
                viewport={"width": 1366, "height": 768},
                locale="en-US"
            )

            # MASTER TAB: Navigates Google Maps & Streams Feed
            master_page = await context.new_page()
            search_url = f"https://www.google.com/maps/search/{urllib.parse.quote_plus(query)}?hl=en"
            ui.log_crawler_step(1, 4, f"Master Tab navigating to {ui.C_WHITE}{search_url}{ui.RESET}")
            if on_step:
                on_step(f"Master Tab opening Google Maps search stream...")

            await master_page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(2)

            # Accept consent if prompted
            try:
                consent_locators = [
                    "button:has-text('Accept all')",
                    "button:has-text('I agree')",
                    "button[aria-label*='Accept all']",
                    "form[action*='consent'] button"
                ]
                for c_sel in consent_locators:
                    btn = master_page.locator(c_sel).first
                    if await btn.is_visible(timeout=1200):
                        await btn.click()
                        await asyncio.sleep(1)
                        break
            except Exception:
                pass

            # Wait for results feed
            feed_selector = 'div[role="feed"]'
            try:
                await master_page.wait_for_selector(feed_selector, timeout=18000)
            except Exception:
                pass

            # FAST FEED STREAMING (Jaala Scroll: Scrolls enough to populate target quota)
            ui.log_crawler_step(2, 4, f"Streaming Google Maps viewport to gather candidate cards...")
            if on_step:
                on_step(f"Casting the Net: Hydrating feed for {max_places} candidate businesses...")

            scroll_cycles = max(8, min(45, int(max_places * 0.4) + 6))
            for s_idx in range(scroll_cycles):
                if should_stop and should_stop():
                    break
                try:
                    feed = master_page.locator(feed_selector)
                    await feed.evaluate("el => el.scrollBy(0, 4000)")
                    await asyncio.sleep(0.7)
                    if s_idx % 4 == 0:
                        card_cnt = await master_page.locator('div[role="feed"] a[href*="/maps/place/"]').count()
                        if card_cnt >= max_places + 20:
                            break
                except Exception:
                    await master_page.mouse.wheel(0, 1800)
                    await asyncio.sleep(0.7)

            # DOM FAST EXTRACTION via JavaScript (0.02 seconds)
            ui.log_crawler_step(3, 4, "Extracting candidate cards from DOM...")
            candidate_items = await master_page.evaluate("""() => {
                const results = [];
                const cards = document.querySelectorAll('div[role="feed"] > div');
                for (const card of cards) {
                    const link = card.querySelector('a[href*="/maps/place/"]');
                    if (!link) continue;
                    const aria = link.getAttribute('aria-label') || '';
                    const title = aria.split('·')[0].split('\\n')[0].trim() || (card.innerText || '').split('\\n')[0].trim();
                    if (!title || title.toLowerCase().includes('sponsored') || title.includes('\\ue5d4')) continue;
                    
                    const webBtn = card.querySelector('a[data-value="Website"], a[aria-label*="Website"], a[aria-label*="website"], a[data-item-id="authority"]');
                    const website = webBtn ? webBtn.getAttribute('href') : null;
                    const text = card.innerText || '';

                    // Check mailto link in card
                    const mailBtn = card.querySelector('a[href^="mailto:"]');
                    let cardEmail = mailBtn ? mailBtn.getAttribute('href').replace(/^mailto:/i, '').split('?')[0].trim() : null;
                    if (!cardEmail && text.includes('@')) {
                        const m = text.match(/[a-zA-Z0-9_.+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}/);
                        if (m) cardEmail = m[0].trim();
                    }

                    results.push({
                        title: title,
                        href: link.getAttribute('href'),
                        website: website,
                        email: cardEmail,
                        card_text: text
                    });
                }
                return results;
            }""")

            # Close Master Tab to free memory
            try:
                await master_page.close()
            except Exception:
                pass

            existing_names = db.get_existing_business_names_set(city, country)
            ui.log_crawler_step(4, 4, f"Casting Multi-Tab Swarm across {ui.C_GREEN}{len(candidate_items)}{ui.RESET} candidates...")
            if on_step:
                on_step(f"Deploying 8 concurrent worker tabs in single browser for parallel extraction...")

            # MULTI-TAB PARALLEL WORKER POOL (Jaala Fekna - 8 Tabs Concurrently)
            sem = asyncio.Semaphore(8)
            tasks = []
            for item in candidate_items:
                if len(discovered) >= max_places:
                    break
                if should_stop and should_stop():
                    break
                t_name = item.get("title", "").strip().lower()
                if t_name in existing_names or "sponsored" in t_name or "\ue5d4" in t_name:
                    continue
                tasks.append(_inspect_candidate_tab(
                    context=context,
                    item=item,
                    city=city,
                    country=country,
                    niche=niche,
                    business_id=business_id,
                    sem=sem,
                    discovered_list=discovered,
                    existing_names=existing_names,
                    on_step=on_step,
                    total_target=max_places
                ))

            # Run all worker tabs in parallel batches
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            print(f"  {ui.C_RED}[!] Swarm Crawler Exception: {e}{ui.RESET}")
            if on_step:
                on_step(f"Swarm Crawler Exception: {e}")
        finally:
            if context:
                try:
                    await context.close()
                except Exception:
                    pass
            if browser:
                try:
                    await browser.close()
                except Exception:
                    pass
            import gc
            gc.collect()

    print(f"  {ui.C_CYAN}[✓ MULTI-TAB SWARM COMPLETE]{ui.RESET} Captured {ui.C_GREEN}{len(discovered)}{ui.RESET} qualified leads.")
    if on_step:
        on_step(f"Multi-Tab Swarm Complete: Successfully captured {len(discovered)} qualified leads.")
    return discovered

def crawl_google_maps(
    city: str = "Mumbai",
    country: str = "India",
    niche: str = "Restaurants",
    max_places: int = 100,
    headless: Optional[bool] = None,
    business_id: str = "aloria_labs",
    on_step=None,
    should_stop=None
) -> List[Dict[str, Any]]:
    """
    Standard synchronous entry point for all callers.
    Safely executes the async Multi-Tab Swarm crawler under the hood.
    """
    if headless is None:
        headless = getattr(config, "HEADLESS", True)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(
                asyncio.run,
                _async_multi_tab_crawl_maps(
                    city=city,
                    country=country,
                    niche=niche,
                    max_places=max_places,
                    headless=headless,
                    business_id=business_id,
                    on_step=on_step,
                    should_stop=should_stop
                )
            ).result()
    else:
        return asyncio.run(
            _async_multi_tab_crawl_maps(
                city=city,
                country=country,
                niche=niche,
                max_places=max_places,
                headless=headless,
                business_id=business_id,
                on_step=on_step,
                should_stop=should_stop
            )
        )

if __name__ == "__main__":
    # Standalone quick test
    crawl_google_maps(city="Mumbai", country="India", niche="Restaurants", max_places=10, headless=True)
