import os
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "D:\\playwright-browsers"
from pathlib import Path
from playwright.sync_api import sync_playwright

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

SESSION_DIR = Path("D:/playwright-browsers/whatsapp_profile")
with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=str(SESSION_DIR),
        headless=True,
        user_agent=USER_AGENT,
        viewport={"width": 1280, "height": 800},
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = context.new_page()
    url = "https://web.whatsapp.com"
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    print("Page URL:", page.url)
    page.screenshot(path="scratch/wa_test_ua.png")
    print("Screenshot saved to scratch/wa_test_ua.png")
    context.close()
