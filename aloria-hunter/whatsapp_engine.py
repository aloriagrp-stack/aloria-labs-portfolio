import os
import re
import time
import urllib.parse
from pathlib import Path
from playwright.sync_api import sync_playwright
import db
import business_manager
import ui

SESSION_DIR = Path("D:/playwright-browsers/whatsapp_profile")
SESSION_DIR.mkdir(parents=True, exist_ok=True)

def clean_phone_number(raw_phone, default_country_code="91"):
    if not raw_phone:
        return None
    # Strip everything except digits
    digits = re.sub(r"[^\d]", "", raw_phone)
    if not digits:
        return None
    # If 10 digits (common for India / standard mobile), prefix default country code
    if len(digits) == 10:
        digits = f"{default_country_code}{digits}"
    elif len(digits) == 11 and digits.startswith("0"):
        digits = f"{default_country_code}{digits[1:]}"
    return digits

def launch_whatsapp_login_qr():
    """
    Opens WhatsApp Web in a visible Chrome window so the operator can scan the QR code once.
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
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = context.new_page()
        page.goto("https://web.whatsapp.com", wait_until="load", timeout=60000)

        print(f"  {ui.C_YELLOW}[!] Waiting for you to scan QR code on screen...{ui.RESET}")

        logged_in = False
        start_time = time.time()
        # Wait up to 3 minutes for QR scan
        while time.time() - start_time < 180:
            try:
                # 1. Check if chat list or search bar is visible
                has_search = page.locator("div[contenteditable='true'], [aria-label*='Search'], [data-testid='chat-list'], #pane-side, [role='textbox'], [aria-label='Chats']").count() > 0
                has_qr = page.locator("canvas[aria-label*='Scan'], [data-ref]").count() > 0

                if has_search or (not has_qr and time.time() - start_time > 8):
                    logged_in = True
                    break
            except Exception:
                pass
            time.sleep(1)

        if logged_in or is_whatsapp_logged_in():
            print(f"\n  {ui.C_GREEN}[✓] WhatsApp Web successfully verified and session saved permanently!{ui.RESET}\n")
            time.sleep(2)
        else:
            print(f"\n  {ui.C_YELLOW}[!] Session check completed. Profile saved in D:/playwright-browsers/whatsapp_profile.{ui.RESET}\n")

        try:
            context.close()
        except Exception:
            pass
        return True

def is_whatsapp_logged_in():
    """Instant check to see if WhatsApp Web has an active authenticated session on disk."""
    default_dir = SESSION_DIR / "Default" / "IndexedDB"
    if default_dir.exists():
        wa_dbs = list(default_dir.glob("*whatsapp*"))
        if wa_dbs:
            return True
    return False

def send_whatsapp_message(phone_number, message_text, headless=True):
    """
    Sends a WhatsApp message via WhatsApp Web without any Meta API keys.
    Returns: (success: bool, status_str: str)
    """
    clean_phone = clean_phone_number(phone_number)
    if not clean_phone or len(clean_phone) < 10:
        return False, "INVALID_PHONE_FORMAT"

    encoded_msg = urllib.parse.quote(message_text)
    url = f"https://web.whatsapp.com/send?phone={clean_phone}&text={encoded_msg}"

    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(SESSION_DIR),
                headless=headless,
                viewport={"width": 1280, "height": 800},
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=45000)

            # Wait for either chat box to appear OR invalid number alert
            time.sleep(5)

            # Check for invalid number alert
            invalid_popup = page.locator("text='Phone number shared via url is invalid', text='Starting chat is not allowed'")
            try:
                if invalid_popup.is_visible(timeout=3000):
                    context.close()
                    return False, "NUMBER_NOT_ON_WHATSAPP"
            except Exception:
                pass

            # Locate send button
            # WhatsApp Web send button selectors
            send_btn = page.locator("button[data-testid='compose-btn-send'], button[aria-label='Send'], span[data-icon='send']")
            try:
                send_btn.wait_for(state="visible", timeout=15000)
                send_btn.click()
                time.sleep(3)
                context.close()
                return True, "SENT"
            except Exception:
                # Try pressing Enter inside the active input field
                try:
                    chat_input = page.locator("footer div[contenteditable='true']")
                    if chat_input.is_visible(timeout=3000):
                        chat_input.press("Enter")
                        time.sleep(3)
                        context.close()
                        return True, "SENT"
                except Exception as ex2:
                    context.close()
                    return False, f"SEND_FAILED: {ex2}"

                context.close()
                return False, "SEND_BUTTON_NOT_FOUND"

        except Exception as e:
            return False, f"BROWSER_ERROR: {e}"

def dispatch_whatsapp_queue(limit=5, business_id="gethotelstays", headless=True):
    """
    Dispatches tailored WhatsApp messages to leads that have a phone number.
    Prioritizes leads with no verified email.
    """
    biz = business_manager.get_business(business_id)
    b_name = biz.get("name", business_id) if biz else business_id
    whatsapp_pitch = biz.get("whatsapp_pitch") if biz else None

    if not whatsapp_pitch:
        print(f"  {ui.C_RED}[!] No WhatsApp pitch configured for {b_name}.{ui.RESET}")
        return 0

    ready_leads = db.get_leads_ready_for_whatsapp(business_id=business_id, limit=limit)
    print(f"\n  {ui.C_GREEN}[⚡ WHATSAPP ENGINE]{ui.RESET} Found {ui.C_WHITE}{len(ready_leads)}{ui.RESET} phone contacts ready for WhatsApp outreach...")

    if not ready_leads:
        print(f"  {ui.C_DIM}No pending WhatsApp leads found for {b_name}.{ui.RESET}")
        return 0

    sent_count = 0
    for idx, lead in enumerate(ready_leads, 1):
        lead_id = lead["id"]
        hotel_name = lead["business_name"]
        raw_phone = lead["phone"]

        msg = whatsapp_pitch.format(business_name=hotel_name)

        print(f"  {ui.C_CYAN}[{idx}/{len(ready_leads)}]{ui.RESET} Sending WhatsApp to {ui.C_WHITE}{hotel_name}{ui.RESET} ({raw_phone})...")
        success, status = send_whatsapp_message(raw_phone, msg, headless=headless)

        if success:
            db.mark_whatsapp_sent(lead_id, status="SENT")
            sent_count += 1
            print(f"  {ui.C_GREEN}[✓] WhatsApp delivered to {hotel_name}!{ui.RESET}")
        else:
            db.mark_whatsapp_sent(lead_id, status=f"FAILED_{status}")
            print(f"  {ui.C_RED}[✗] WhatsApp failed for {hotel_name}: {status}{ui.RESET}")

        # Anti-ban human delay between messages (20-30 seconds)
        if idx < len(ready_leads):
            print(f"  {ui.C_DIM}Waiting 20 seconds (anti-ban safety delay)...{ui.RESET}")
            time.sleep(20)

    print(f"\n  {ui.C_GREEN}[✓ WHATSAPP OUTREACH WAVE COMPLETE]{ui.RESET} Sent: {sent_count}/{len(ready_leads)}\n")
    return sent_count
