import os
import time
import re
from urllib.parse import quote_plus, unquote

# Set Playwright browser path on D drive before importing playwright
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "D:\\playwright-browsers"

from playwright.sync_api import sync_playwright
import config
import db
import ui

def crawl_google_maps(city="Algiers", country="Algeria", niche="Restaurants", max_places=25, headless=None, business_id="aloria_labs", on_step=None, should_stop=None):
    if headless is None:
        headless = config.HEADLESS

    query = f"{niche} in {city}, {country}"
    print(f"  {ui.C_CYAN}[⚡ GOOGLE MAPS CRAWLER]{ui.RESET} Query: '{ui.C_WHITE}{query}{ui.RESET}' │ Quota: {ui.C_YELLOW}{max_places}{ui.RESET}")
    if on_step:
        on_step(f"Starting Google Maps sweep for {max_places} {niche} in {city}, {country}...")

    discovered = []

    with sync_playwright() as p:
        browser = None
        context = None
        try:
            if should_stop and should_stop():
                return discovered

            browser = p.chromium.launch(
                headless=headless,
                args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
            )
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                locale="en-US"
            )
            page = context.new_page()
            import urllib.parse
            search_url = f"https://www.google.com/maps/search/{urllib.parse.quote_plus(query)}?hl=en"
            ui.log_crawler_step(1, 4, f"Navigating to {ui.C_WHITE}{search_url}{ui.RESET}")
            if on_step:
                on_step(f"Navigating to Google Maps search viewport...")
            page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(2)

            # Accept cookies/consent dialog if present
            try:
                consent_locators = [
                    "button:has-text('Accept all')",
                    "button:has-text('I agree')",
                    "button[aria-label*='Accept all']",
                    "form[action*='consent'] button"
                ]
                for c_sel in consent_locators:
                    btn = page.locator(c_sel).first
                    if btn.is_visible(timeout=1500):
                        btn.click()
                        time.sleep(1.5)
                        break
            except Exception:
                pass

            # Wait for results feed
            ui.log_crawler_step(2, 4, "Syncing Google Maps listings stream...")
            feed_selector = 'div[role="feed"]'
            try:
                page.wait_for_selector(feed_selector, timeout=20000)
            except Exception:
                # Fallback: check for search box and re-submit if needed
                try:
                    search_box = page.locator("#searchboxinput")
                    if search_box.is_visible(timeout=3000):
                        search_box.fill(query)
                        page.keyboard.press("Enter")
                        page.wait_for_selector(feed_selector, timeout=15000)
                except Exception:
                    pass

            time.sleep(3)

            # Scroll the feed to load results
            ui.log_crawler_step(3, 4, "Streaming listings viewport...")
            scroll_count = max(4, min(25, (max_places // 2) + 2))
            for scroll_idx in range(scroll_count):
                try:
                    feed = page.locator(feed_selector)
                    feed.evaluate("el => el.scrollBy(0, 3000)")
                    time.sleep(1.2)
                except Exception:
                    page.mouse.wheel(0, 1000)
                    time.sleep(1)

            # Find all place card links in the feed
            place_links = page.locator('div[role="feed"] a[href*="/maps/place/"]').all()
            ui.log_crawler_step(4, 4, f"Discovered {ui.C_GREEN}{len(place_links)}{ui.RESET} candidates. Extracting metadata...")
            if on_step:
                on_step(f"Discovered {len(place_links)} candidate locations in viewport. Beginning inspection...")

            seen_titles = set()
            count = 0

            for idx, link_loc in enumerate(place_links):
                if count >= max_places:
                    break

                if should_stop and should_stop():
                    if on_step:
                        on_step("Halt directive received from operator. Safely stopping sweep.")
                    break

                try:
                    # Click place card to open detail panel
                    link_loc.click(timeout=5000)
                    time.sleep(1.8)

                    # Extract Business Title
                    title = ""
                    try:
                        title_loc = page.locator('h1.DUwDvf, div.lMbq3e h1, h1[tabindex="-1"]').first
                        if title_loc.is_visible(timeout=3000):
                            title = title_loc.inner_text().strip()
                            if title:
                                title = title.split("\n")[0].strip()
                    except Exception:
                        pass

                    if not title or title in seen_titles:
                        continue

                    # Filter out sponsored ads / aggregators
                    if "sponsored" in title.lower() or "\nby " in title.lower() or "\ue5d4" in title:
                        continue
                    seen_titles.add(title)

                    if on_step:
                        on_step(f"Inspecting candidate [{count + 1}/{max_places}]: '{title}'...")

                    # Extract Website Link
                    website_url = None
                    try:
                        # Authority website button
                        web_btn = page.locator('a[data-item-id="authority"], a[aria-label*="Website"], a[aria-label*="website"]').first
                        if web_btn.is_visible(timeout=1500):
                            website_url = web_btn.get_attribute("href")
                            # Clean google redirect if needed
                            if website_url and "google.com/url?" in website_url:
                                match = re.search(r'url=([^&]+)', website_url)
                                if match:
                                    import urllib.parse
                                    website_url = urllib.parse.unquote(match.group(1))

                            # Filter out OTA aggregators / social links to prevent bouncing on 3rd party domains
                            if website_url:
                                lower_url = website_url.lower()
                                ota_domains = [
                                    "booking.com", "agoda.com", "tripadvisor", "makemytrip.com",
                                    "goibibo.com", "expedia.com", "hotels.com", "trivago.com",
                                    "facebook.com", "instagram.com", "justdial.com", "indiamart.com"
                                ]
                                if any(dom in lower_url for dom in ota_domains):
                                    website_url = None
                    except Exception:
                        pass

                    # Extract Phone Number
                    phone = None
                    try:
                        phone_loc = page.locator('button[data-item-id*="phone:"], button[aria-label*="Phone"]').first
                        if phone_loc.is_visible(timeout=1000):
                            phone_text = phone_loc.inner_text().strip()
                            phone = re.sub(r'[^\d+\-\s\(\)]', '', phone_text).strip()
                            if phone:
                                phone = re.sub(r'\s+', ' ', phone).strip()
                    except Exception:
                        pass

                    # Extract Address
                    address = None
                    try:
                        addr_loc = page.locator('button[data-item-id="address"], button[aria-label*="Address"]').first
                        if addr_loc.is_visible(timeout=1000):
                            address = addr_loc.inner_text().strip()
                    except Exception:
                        pass

                    # Extract Rating & Reviews
                    rating = None
                    reviews_count = None
                    try:
                        rating_loc = page.locator('div.F7nice span[aria-hidden="true"]').first
                        if rating_loc.is_visible(timeout=1000):
                            rating = rating_loc.inner_text().strip()
                        rev_loc = page.locator('div.F7nice span[aria-label*="reviews"]').first
                        if rev_loc.is_visible(timeout=1000):
                            reviews_count = re.sub(r'[^\d]', '', rev_loc.inner_text().strip())
                    except Exception:
                        pass

                    # Insert into SQLite State Machine
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
                        business_id=business_id
                    )

                    ui.log_discovered_place(count + 1, max_places, title, website_url, phone, rating)
                    if on_step:
                        on_step(f"Verified & saved to ledger [{count + 1}/{max_places}]: {title} {'(Domain: ' + website_url + ')' if website_url else '(No Website - Golden Lead)'}")

                    discovered.append({
                        "id": lead_id,
                        "name": title,
                        "has_website": bool(website_url),
                        "website_url": website_url,
                        "phone": phone,
                        "rating": rating,
                        "reviews": reviews_count
                    })
                    count += 1

                except Exception as e:
                    # Skip problematic individual card and keep crawling
                    continue

        except Exception as e:
            print(f"  {ui.C_RED}[!] Crawler exception: {e}{ui.RESET}")
        finally:
            if context:
                try:
                    context.close()
                except Exception:
                    pass
            if browser:
                try:
                    browser.close()
                except Exception:
                    pass

    print(f"  {ui.C_CYAN}[✓ CRAWL COMPLETE]{ui.RESET} Captured {ui.C_GREEN}{len(discovered)}{ui.RESET} leads in this wave.")
    return discovered

if __name__ == "__main__":
    # Test run
    crawl_google_maps(city="Algiers", country="Algeria", niche="Restaurants", max_places=5, headless=False)
