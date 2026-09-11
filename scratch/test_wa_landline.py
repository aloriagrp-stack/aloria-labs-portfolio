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
    url_landline = "https://web.whatsapp.com/send?phone=918326643333&text=Test"
    page.goto(url_landline, wait_until="domcontentloaded")
    
    # Wait for the progress bar to disappear
    print("Waiting for WhatsApp to finish initial sync...")
    try:
        page.wait_for_selector("#pane-side, [data-testid='chat-list'], div[role='dialog']", timeout=30000)
    except Exception as e:
        print("Wait err:", e)

    page.wait_for_timeout(3000)
    page.screenshot(path="scratch/wa_landline_loaded.png")
    
    # Check dialogs
    dialogs = page.locator("div[role='dialog'], [data-testid='popup-contents'], div[data-animate-modal-popup='true']").all()
    print("Dialogs count:", len(dialogs))
    for d in dialogs:
        try:
            print("Dialog text:", repr(d.inner_text()))
        except Exception as ex:
            print("Dialog err:", ex)

    context.close()
