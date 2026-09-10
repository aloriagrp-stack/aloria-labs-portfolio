import time
import re
from playwright.sync_api import sync_playwright
import config
import db
import ui

def crawl_google_maps(city="Algiers", country="Algeria", niche="Restaurants", max_places=25, headless=None, business_id="aloria_labs"):
    if headless is None:
        headless = config.HEADLESS

    query = f"{niche} in {city}, {country}"
    print(f"  {ui.C_CYAN}[⚡ GOOGLE MAPS CRAWLER]{ui.RESET} Query: '{ui.C_WHITE}{query}{ui.RESET}' │ Quota: {ui.C_YELLOW}{max_places}{ui.RESET}")

    discovered = []

    with sync_playwright() as p:
        # Launch Chromium from D:\playwright-browsers
        browser = p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
        )
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            locale="en-US"
        )
        page = context.new_page()

        try:
            import urllib.parse
            search_url = f"https://www.google.com/maps/search/{urllib.parse.quote_plus(query)}?hl=en"
            ui.log_crawler_step(1, 4, f"Navigating to {ui.C_WHITE}{search_url}{ui.RESET}")
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
            for scroll_idx in range(4):
                try:
                    feed = page.locator(feed_selector)
                    feed.evaluate("el => el.scrollBy(0, 3000)")
                    time.sleep(1.5)
                except Exception:
                    page.mouse.wheel(0, 1000)
                    time.sleep(1)

            # Find all place card links in the feed
            place_links = page.locator('div[role="feed"] a[href*="/maps/place/"]').all()
            ui.log_crawler_step(4, 4, f"Discovered {ui.C_GREEN}{len(place_links)}{ui.RESET} candidates. Extracting metadata...")

            seen_titles = set()
            count = 0

            for idx, link_loc in enumerate(place_links):
                if count >= max_places:
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
                    except Exception:
                        pass

                    if not title or title in seen_titles:
                        continue
                    seen_titles.add(title)

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
                    except Exception:
                        pass

                    # Extract Phone Number
                    phone = None
                    try:
                        phone_loc = page.locator('button[data-item-id*="phone:"], button[aria-label*="Phone"]').first
                        if phone_loc.is_visible(timeout=1000):
                            phone_text = phone_loc.inner_text().strip()
                            phone = re.sub(r'[^\d+\-\s\(\)]', '', phone_text).strip()
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
            browser.close()

    print(f"  {ui.C_CYAN}[✓ CRAWL COMPLETE]{ui.RESET} Captured {ui.C_GREEN}{len(discovered)}{ui.RESET} leads in this wave.")
    return discovered

if __name__ == "__main__":
    # Test run
    crawl_google_maps(city="Algiers", country="Algeria", niche="Restaurants", max_places=5, headless=False)
