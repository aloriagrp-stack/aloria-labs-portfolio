import os
import re
import time
import urllib.parse
from pathlib import Path
from playwright.sync_api import sync_playwright
import db
import business_manager
import ui

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "D:\\playwright-browsers"
SESSION_DIR = Path("D:/playwright-browsers/whatsapp_profile")
SESSION_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

# Known Indian Landline STD codes (cannot have WhatsApp)
INDIAN_LANDLINE_PREFIXES = (
    "011", "022", "033", "044", "080", "0832", "0141", "0294", "01902", 
    "0177", "0135", "01334", "0484", "0477", "0497", "0487", "0413",
    "079", "020", "040", "0522", "0542", "0562", "0755", "0731"
)

def clean_phone_number(raw_phone, default_country_code="91"):
    """
    Cleans phone number and detects whether it is a genuine mobile number or a fixed landline.
    Returns: (cleaned_digits_with_country_code, is_mobile_boolean)
    """
    if not raw_phone:
        return None, False

    raw_str = raw_phone.strip()

    # If starts with a known landline STD code like 0832, 011, 022 etc.
    if any(raw_str.startswith(std) for std in INDIAN_LANDLINE_PREFIXES):
        return None, False

    # Extract all digits
    digits = re.sub(r"[^\d]", "", raw_phone)
    if not digits:
        return None, False

    # If starts with leading 0 (STD notation), strip it
    if digits.startswith("0"):
        digits = digits[1:]

    # Check length and mobile prefix
    if len(digits) == 10:
        # Standard 10-digit Indian number
        # Indian mobile numbers MUST start with 6, 7, 8, or 9
        if digits[0] in "6789":
            return f"{default_country_code}{digits}", True
        else:
            return None, False  # Landline starting with 1-5

    elif len(digits) == 12 and digits.startswith(default_country_code):
        # 12 digits including 91
        mobile_part = digits[2:]
        if mobile_part[0] in "6789":
            return digits, True
        else:
            return None, False

    elif len(digits) > 10 and not digits.startswith(default_country_code):
        # Could be an STD landline where 0 was stripped
        return None, False

    return None, False

def launch_whatsapp_login_qr():
    """
    Opens WhatsApp Web in a visible Chrome window with full User-Agent so the operator can scan the QR code.
    The session is saved permanently in D:/playwright-browsers/whatsapp_profile.
    """
    print(f"\n{ui.C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{ui.RESET}")
    print(f"  {ui.C_WHITE}WHATSAPP WEB QR CODE LOGIN{ui.RESET}")
    print(f"  {ui.C_DIM}Opening Chrome window... Scan the QR code using your phone's WhatsApp.{ui.RESET}")
    print(f"  {ui.C_DIM}(WhatsApp ➔ Linked Devices ➔ Link a Device){ui.RESET}")
    print(f"{ui.C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{ui.RESET}\n")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_DIR),
            headless=False,
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = context.new_page()
        page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=60000)

        print(f"  {ui.C_YELLOW}[!] Waiting for you to scan QR code on screen...{ui.RESET}")

        logged_in = False
        start_time = time.time()
        while time.time() - start_time < 180:
            try:
                has_search = page.locator("div[contenteditable='true'], [aria-label*='Search'], [data-testid='chat-list'], #pane-side").count() > 0
                has_qr = page.locator("canvas[aria-label*='Scan'], [data-ref]").count() > 0

                if has_search or (not has_qr and time.time() - start_time > 10):
                    logged_in = True
                    break
            except Exception:
                pass
            time.sleep(1)

        if logged_in:
            print(f"\n  {ui.C_GREEN}[✓] WhatsApp Web successfully verified and session saved permanently!{ui.RESET}\n")
            time.sleep(2)
        else:
            print(f"\n  {ui.C_YELLOW}[!] Please finish scanning in the open Chrome window.{ui.RESET}\n")

        try:
            context.close()
        except Exception:
            pass
        return logged_in

def is_whatsapp_logged_in():
    """Checks if WhatsApp Web has an active authenticated session on disk."""
    default_dir = SESSION_DIR / "Default" / "IndexedDB"
    if default_dir.exists():
        wa_dbs = list(default_dir.glob("*whatsapp*"))
        if wa_dbs:
            return True
    return False

def dispatch_whatsapp_queue(limit=5, business_id="gethotelstays", headless=False):
    """
    Dispatches tailored WhatsApp messages to verified MOBILE leads.
    Keeps a SINGLE persistent browser context open for the entire batch to prevent session resets.
    """
    biz = business_manager.get_business(business_id)
    b_name = biz.get("name", business_id) if biz else business_id
    whatsapp_pitch = biz.get("whatsapp_pitch") if biz else None

    if not whatsapp_pitch:
        print(f"  {ui.C_RED}[!] No WhatsApp pitch configured for {b_name}.{ui.RESET}")
        return 0

    ready_leads = db.get_leads_ready_for_whatsapp(business_id=business_id, limit=limit * 2)

    if not ready_leads:
        return 0

    print(f"\n  {ui.C_GREEN}[⚡ WHATSAPP ENGINE]{ui.RESET} Inspecting {ui.C_WHITE}{len(ready_leads)}{ui.RESET} phone contacts for mobile numbers...")

    # Filter out landlines and extract verified mobile leads
    valid_mobile_leads = []
    for lead in ready_leads:
        lead_id = lead["id"]
        hotel_name = lead["business_name"]
        raw_phone = lead["phone"]

        clean_phone, is_mobile = clean_phone_number(raw_phone)
        if not is_mobile or not clean_phone:
            print(f"  {ui.C_DIM}[!] Skipping {hotel_name} ({raw_phone}): Fixed Landline (WhatsApp only supports mobile){ui.RESET}")
            db.mark_whatsapp_sent(lead_id, status="LANDLINE_NO_WHATSAPP")
            continue

        valid_mobile_leads.append((lead, clean_phone))
        if len(valid_mobile_leads) >= limit:
            break

    if not valid_mobile_leads:
        print(f"  {ui.C_YELLOW}[!] All discovered contacts in this batch were landlines. Moving to email outreach.{ui.RESET}")
        return 0

    print(f"  {ui.C_GREEN}[✓] Found {len(valid_mobile_leads)} verified mobile contacts for WhatsApp dispatch.{ui.RESET}")

    sent_count = 0

    # Launch browser ONCE for the entire batch with full Chrome User-Agent
    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(SESSION_DIR),
                headless=headless,
                user_agent=USER_AGENT,
                viewport={"width": 1280, "height": 800},
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = context.new_page()

            for idx, (lead, clean_phone) in enumerate(valid_mobile_leads, 1):
                lead_id = lead["id"]
                hotel_name = lead["business_name"]
                msg = whatsapp_pitch.format(business_name=hotel_name)
                encoded_msg = urllib.parse.quote(msg)
                url = f"https://web.whatsapp.com/send?phone={clean_phone}&text={encoded_msg}"

                print(f"  {ui.C_CYAN}[{idx}/{len(valid_mobile_leads)}]{ui.RESET} Opening WhatsApp chat for {ui.C_WHITE}{hotel_name}{ui.RESET} ({clean_phone})...")

                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=45000)

                    # Wait for either chat input or invalid phone number modal
                    delivered = False
                    start_wait = time.time()

                    while time.time() - start_wait < 25:
                        # 1. Check for invalid number popup
                        dialog = page.locator("div[role='dialog'], [data-testid='popup-contents'], div[data-animate-modal-popup='true']")
                        if dialog.count() > 0 and any(kw in dialog.first.inner_text().lower() for kw in ["invalid", "not allowed", "ok"]):
                            print(f"  {ui.C_YELLOW}[!] Number {clean_phone} is not registered on WhatsApp.{ui.RESET}")
                            db.mark_whatsapp_sent(lead_id, status="NOT_ON_WHATSAPP")
                            try:
                                # Dismiss popup
                                page.locator("button:has-text('OK'), div[role='button']:has-text('OK')").first.click(timeout=1000)
                            except Exception:
                                pass
                            delivered = False
                            break

                        # 2. Check for chat input field
                        chat_input = page.locator("footer div[contenteditable='true'], div[data-tab='10']")
                        if chat_input.count() > 0 and chat_input.first.is_visible():
                            time.sleep(1.5)
                            # Try clicking send button
                            send_btn = page.locator("button[aria-label='Send'], span[data-icon='send'], button[data-tab='11']")
                            if send_btn.count() > 0 and send_btn.first.is_visible():
                                send_btn.first.click()
                            else:
                                chat_input.first.press("Enter")

                            time.sleep(2.5)
                            db.mark_whatsapp_sent(lead_id, status="SENT")
                            sent_count += 1
                            print(f"  {ui.C_GREEN}[✓] WhatsApp successfully DELIVERED to {hotel_name}!{ui.RESET}")
                            delivered = True
                            break

                        time.sleep(1)

                    if not delivered and dialog.count() == 0:
                        print(f"  {ui.C_RED}[✗] WhatsApp chat timed out for {hotel_name}{ui.RESET}")
                        db.mark_whatsapp_sent(lead_id, status="FAILED_TIMEOUT")

                except Exception as ex:
                    print(f"  {ui.C_RED}[!] Error dispatching to {hotel_name}: {ex}{ui.RESET}")
                    db.mark_whatsapp_sent(lead_id, status="FAILED_ERROR")

                # Anti-ban safety delay between messages
                if idx < len(valid_mobile_leads):
                    print(f"  {ui.C_DIM}Waiting 15s (anti-ban pacing)...{ui.RESET}")
                    time.sleep(15)

            context.close()

        except Exception as e:
            print(f"  {ui.C_RED}[!] WhatsApp browser error: {e}{ui.RESET}")

    print(f"\n  {ui.C_GREEN}[✓ WHATSAPP OUTREACH COMPLETE]{ui.RESET} Successfully delivered: {sent_count}/{len(valid_mobile_leads)}\n")
    return sent_count
