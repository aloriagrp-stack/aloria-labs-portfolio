import os
import sys
import time
from pathlib import Path

# Ensure UTF-8 console on Windows
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
    except Exception:
        pass

import colorama
from colorama import Fore, Back, Style

colorama.init(autoreset=True)

# Color shortcuts
C_CYAN = Fore.CYAN + Style.BRIGHT
C_GREEN = Fore.GREEN + Style.BRIGHT
C_RED = Fore.RED + Style.BRIGHT
C_YELLOW = Fore.YELLOW + Style.BRIGHT
C_MAGENTA = Fore.MAGENTA + Style.BRIGHT
C_BLUE = Fore.BLUE + Style.BRIGHT
C_WHITE = Fore.WHITE + Style.BRIGHT
C_DIM = Style.DIM
RESET = Style.RESET_ALL

# Set environment
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "D:\\playwright-browsers"
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import db
import config
import business_manager
import maps_crawler
import website_auditor
import email_engine

def print_banner():
    banner = f"""
{C_CYAN}  █████╗ ██╗      ██████╗ ██████╗ ██╗ █████╗     ██╗  ██╗██╗   ██╗███╗   ██╗████████╗███████╗██████╗ 
{C_CYAN} ██╔══██╗██║     ██╔═══██╗██╔══██╗██║██╔══██╗    ██║  ██║██║   ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗
{C_BLUE} ███████║██║     ██║   ██║██████╔╝██║███████║    ███████║██║   ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝
{C_BLUE} ██╔══██║██║     ██║   ██║██╔══██╗██║██╔══██║    ██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗
{C_MAGENTA} ██║  ██║███████╗╚██████╔╝██║  ██║██║██║  ██║    ██║  ██║╚██████╔╝██║ ╚████║   ██║   ███████╗██║  ██║
{C_MAGENTA} ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
{C_WHITE}                       [ AUTONOMOUS B2B INTELLIGENCE & COLD OUTREACH ENGINE ]
{C_DIM}                 Multi-Business Automation System • 100% Deterministic • Aloria Labs
"""
    print(banner)

def print_clean_dashboard():
    active_id = business_manager.get_active_business_id()
    active_b = business_manager.get_active_business()
    if isinstance(active_b, str):
        active_b = business_manager.get_business(active_b)
    if not isinstance(active_b, dict):
        active_b = {}
    stats = db.get_funnel_stats(business_id=active_id)

    total = stats.get("total", 0)
    audited = stats.get("audited", 0)
    pitched = stats.get("pitch_sent", 0)
    sent_total = stats.get("emails_sent", 0)

    tgt = business_manager.get_target_settings(active_id)
    tgt_country = tgt.get("country") or ("India" if active_id == "gethotelstays" else "India")
    tgt_city = tgt.get("city") or ("Goa" if active_id == "gethotelstays" else "")
    tgt_niche = tgt.get("niche") or ("Hotels" if active_id == "gethotelstays" else "")

    if tgt_country and tgt_city:
        loc_str = f"{C_GREEN}{tgt_city}, {tgt_country}{RESET}"
    else:
        loc_str = f"{C_YELLOW}[NOT SET - Press T to choose]{RESET}"

    niche_str = f"{C_CYAN}{tgt_niche}{RESET}" if tgt_niche else f"{C_YELLOW}[NOT SET - Press T to choose]{RESET}"

    import whatsapp_engine
    is_wa = whatsapp_engine.is_whatsapp_logged_in()
    wa_badge = f"{C_GREEN}● Connected{RESET}" if is_wa else f"{C_YELLOW}○ Not Linked (Press Q){RESET}"

    import bounce_detector
    interval = getattr(config, "FOLLOW_UP_INTERVAL_DAYS", 3)
    overdue = db.get_overdue_followups(business_id=active_id, interval_days=interval)
    bl_count = len(db.get_blacklisted_emails(1000))
    overdue_badge = f"{C_RED}● {len(overdue)} OVERDUE{RESET}" if overdue else f"{C_GREEN}● All Clear{RESET}"

    if active_id == "gethotelstays":
        ghs_prof_key = active_b.get("sender_profile") or "gethotelstays_india"
        ghs_prof = config.get_smtp_config(ghs_prof_key)
        ghs_email = ghs_prof.get("email", "gethotelstays.india@gmail.com")
        ghs_name = ghs_prof.get("sender_name", "Shriyansh Aloria — GetHotelStays")

        print(f"{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")
        print(f"  {C_WHITE}ACTIVE AGENT:{RESET}       {Back.CYAN}{Fore.BLACK} GETHOTELSTAYS — 24/7 HOTEL PARTNER ONBOARDING {RESET}  {C_DIM}(Press B to switch){RESET}")
        print(f"  {C_WHITE}TARGET DESTINATION:{RESET} {loc_str} │ {niche_str}")
        print(f"  {C_WHITE}SENDER ACCOUNT:{RESET}     {C_GREEN}{ghs_name} <{ghs_email}>{RESET}  {C_YELLOW}[Press S to change]{RESET}")
        print(f"  {C_WHITE}WHATSAPP ENGINE:{RESET}    {wa_badge}")
        print(f"  {C_WHITE}PIPELINE STATS:{RESET}     {C_GREEN}{total}{RESET} Hotels Discovered │ {C_BLUE}{audited}{RESET} Audited │ {C_YELLOW}{pitched}{RESET} Pitched │ {C_CYAN}{sent_total}{RESET} Sent │ {C_RED}{bl_count}{RESET} Bounces Blacklisted")
        print(f"{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}\n")

        if overdue:
            max_days = overdue[0]["days_elapsed"]
            over_days = overdue[0]["days_overdue"]
            print(f"  {Back.RED}{Fore.WHITE} ⚠️  ATTENTION BOSS: {len(overdue)} OVERDUE FOLLOW-UPS DETECTED (LAPTOP WAS OFFLINE) {RESET}")
            print(f"  {C_YELLOW}► Initial pitch sent {max_days} days ago ({over_days} days overdue because laptop was turned off).{RESET}")
            print(f"  {C_YELLOW}► {C_GREEN}RECOMMENDED:{RESET} {C_WHITE}Press {C_GREEN}[F]{C_WHITE} to dispatch follow-ups to these warm leads before hunting new ones!{RESET}\n")

        print(f"  {C_YELLOW}─── [ACTIVE AGENT PROFILE] ────────────────────────────────────────────────────────────────{RESET}")
        print(f"  {C_GREEN}● [ACTIVE]{RESET}  {C_WHITE}GetHotelStays{RESET} — Autonomous Hotel Partner Onboarding ({loc_str})")
        print(f"  {C_DIM}○ [STANDBY] Aloria Labs  — Web & Digital Infrastructure Agency (Press [B] to toggle){RESET}")

        print(f"\n  {C_GREEN}─── [AUTONOMOUS 24/7 HOTEL ONBOARDING ENGINE] ─────────────────────────────────────────────{RESET}")
        print(f"  {C_WHITE}[1]{RESET} {C_GREEN}🔥 START 24/7 HOTEL ONBOARDING{RESET}   {C_DIM}— Runs continuously: Discover ➔ Extract ➔ Pitch ➔ Follow-up{RESET}")
        print(f"  {C_WHITE}[S]{RESET} {C_CYAN}✉ Choose Sender Account{RESET}        {C_DIM}— Switch sender email (Active: {ghs_email}){RESET}")
        print(f"  {C_WHITE}[F]{RESET} {C_YELLOW}⚡ Priority Overdue Follow-ups{RESET}  {overdue_badge} {C_DIM}— Offline catch-up before new leads{RESET}")
        print(f"  {C_WHITE}[C]{RESET} {C_MAGENTA}🛡 Scan Inbox Bounces (IMAP){RESET}    {C_CYAN}{bl_count} Blacklisted{RESET} {C_DIM}— Auto-blacklist dead emails{RESET}")
        print(f"  {C_WHITE}[T]{RESET} {C_CYAN}⚙ Set Target City / State{RESET}        {C_DIM}— Destination (Currently: {tgt_city or 'Goa'}, {tgt_country or 'India'}){RESET}")
        print(f"  {C_WHITE}[L]{RESET} {C_YELLOW}📋 Hotel Pipeline & Ledger{RESET}        {C_DIM}— View discovered hotels, contacts & onboarding stages{RESET}")
        print(f"  {C_WHITE}[Q]{RESET} {C_MAGENTA}💬 WhatsApp Web QR Login{RESET}          {wa_badge} {C_DIM}— Re-scan or manage WhatsApp Web session{RESET}")
        print(f"  {C_WHITE}[B]{RESET} {C_BLUE}🔄 Switch to Aloria Labs{RESET}          {C_DIM}— Switch profile to Web & Software Agency{RESET}")
        print(f"  {C_WHITE}[0]{RESET} {C_RED}✖ Exit Console{RESET}                    {C_DIM}— Close Hunter Command Center{RESET}\n")

    else:
        # ALORIA LABS SPECIFIC CLEAN DASHBOARD
        aloria_prof_key = active_b.get("sender_profile") or "gmail"
        aloria_prof = config.get_smtp_config(aloria_prof_key)
        aloria_email = aloria_prof.get("email", "alorialabs@gmail.com")
        aloria_name = aloria_prof.get("sender_name", "Shriyansh Aloria — Aloria Labs")

        print(f"{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")
        print(f"  {C_WHITE}ACTIVE AGENT:{RESET}       {Back.CYAN}{Fore.BLACK} ALORIA LABS — CLIENT ACQUISITION {RESET}  {C_DIM}(Press B to switch){RESET}")
        print(f"  {C_WHITE}TARGET REGION:{RESET}      {loc_str} │ {niche_str}")
        print(f"  {C_WHITE}SENDER ACCOUNT:{RESET}     {C_CYAN}{aloria_name} <{aloria_email}>{RESET}  {C_YELLOW}[Press S to change]{RESET}")
        print(f"  {C_WHITE}PIPELINE STATS:{RESET}     {C_GREEN}{total}{RESET} Leads Discovered │ {C_BLUE}{audited}{RESET} Audited │ {C_YELLOW}{pitched}{RESET} Pitched │ {C_CYAN}{sent_total}{RESET} Sent │ {C_RED}{bl_count}{RESET} Bounces Blacklisted")
        print(f"{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}\n")

        if overdue:
            max_days = overdue[0]["days_elapsed"]
            over_days = overdue[0]["days_overdue"]
            print(f"  {Back.RED}{Fore.WHITE} ⚠️  ATTENTION BOSS: {len(overdue)} OVERDUE FOLLOW-UPS DETECTED (LAPTOP WAS OFFLINE) {RESET}")
            print(f"  {C_YELLOW}► Initial pitch sent {max_days} days ago ({over_days} days overdue because laptop was turned off).{RESET}")
            print(f"  {C_YELLOW}► {C_GREEN}RECOMMENDED:{RESET} {C_WHITE}Press {C_GREEN}[F]{C_WHITE} to dispatch follow-ups to these warm leads before hunting new ones!{RESET}\n")

        print(f"  {C_YELLOW}─── [ACTIVE AGENT PROFILE] ────────────────────────────────────────────────────────────────{RESET}")
        print(f"  {C_GREEN}● [ACTIVE]{RESET}  {C_WHITE}Aloria Labs{RESET}  — Web & Custom Software Agency ({loc_str})")
        print(f"  {C_DIM}○ [STANDBY] GetHotelStays — Autonomous Hotel Partner Onboarding (Press [B] to toggle){RESET}")

        print(f"\n  {C_CYAN}─── [AUTONOMOUS 24/7 CLIENT ACQUISITION ENGINE] ───────────────────────────────────────────{RESET}")
        print(f"  {C_WHITE}[1]{RESET} {C_GREEN}🚀 START 24/7 CLIENT ACQUISITION{RESET} {C_DIM}— Non-stop: Maps ➔ Web Audits ➔ Custom Pitches ➔ Follow-up{RESET}")
        print(f"  {C_WHITE}[S]{RESET} {C_CYAN}✉ Choose Sender Account{RESET}        {C_DIM}— Switch sender email (Active: {aloria_email}){RESET}")
        print(f"  {C_WHITE}[F]{RESET} {C_YELLOW}⚡ Priority Overdue Follow-ups{RESET}  {overdue_badge} {C_DIM}— Offline catch-up before new leads{RESET}")
        print(f"  {C_WHITE}[C]{RESET} {C_MAGENTA}🛡 Scan Inbox Bounces (IMAP){RESET}    {C_CYAN}{bl_count} Blacklisted{RESET} {C_DIM}— Auto-blacklist dead emails{RESET}")
        print(f"  {C_WHITE}[T]{RESET} {C_CYAN}⚙ Set Target Location / Niche{RESET}   {C_DIM}— Industry & location targeting{RESET}")
        print(f"  {C_WHITE}[L]{RESET} {C_YELLOW}📋 Client Pipeline & Ledger{RESET}       {C_DIM}— View all leads & outreach status{RESET}")
        print(f"  {C_WHITE}[B]{RESET} {C_BLUE}🔄 Switch to GetHotelStays{RESET}       {C_DIM}— Switch to Hotel Onboarding Agent{RESET}")
        print(f"  {C_WHITE}[0]{RESET} {C_RED}✖ Exit Console{RESET}                    {C_DIM}— Close Hunter Command Center{RESET}\n")

def configure_target(b_id):
    b = business_manager.get_business(b_id)
    b_name = b.get("name", b_id) if b else b_id
    tgt = business_manager.get_target_settings(b_id)
    old_c = tgt.get("country", "India")
    old_ci = tgt.get("city", "Goa" if b_id == "gethotelstays" else "Mumbai")
    old_ni = tgt.get("niche", "Hotels" if b_id == "gethotelstays" else "Restaurants")

    print(f"\n{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"  {C_WHITE}CONFIGURE TARGET DESTINATION FOR: {C_YELLOW}{b_name.upper()}{RESET}")
    print(f"{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")

    c = input(f"  {C_WHITE}Target Country [{old_c}]: {RESET}").strip() or old_c
    ci = input(f"  {C_WHITE}Target City / State (e.g. Goa, Jaipur, Manali, Udaipur) [{old_ci}]: {RESET}").strip() or old_ci
    ni = input(f"  {C_WHITE}Target Category [{old_ni}]: {RESET}").strip() or old_ni

    business_manager.set_target_settings(b_id, country=c, city=ci, niche=ni)
    print(f"\n  {C_GREEN}[✓] Target saved: {ni} in {ci}, {c}!{RESET}\n")
    time.sleep(1)
    return c, ci, ni

def show_clean_lead_ledger(active_id):
    leads = db.get_lead_ledger(business_id=active_id, limit=50)
    active_b = business_manager.get_business(active_id)
    b_name = active_b.get("name", active_id) if active_b else active_id

    print(f"\n{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"  {C_WHITE}LEAD LEDGER FOR {C_YELLOW}{b_name.upper()}{RESET} ({len(leads)} leads recorded)")
    print(f"{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")

    if not leads:
        print(f"\n  {C_DIM}No leads recorded yet. Start 24/7 Engine [Option 1] to begin.{RESET}\n")
    else:
        print(f"  {C_DIM}{'NAME':<26} {'PRESENCE':<16} {'EMAIL':<28} {'STAGE'}{RESET}")
        print(f"  {C_DIM}{'─' * 26} {'─' * 16} {'─' * 28} {'─' * 14}{RESET}")
        for l in leads:
            name = l["business_name"][:25]
            has_web = l["has_website"]
            pres = f"{C_GREEN}★ NO WEBSITE{RESET}" if not has_web else f"{C_DIM}HAS WEBSITE{RESET}"
            email = (l["email"] or "No Email Found")[:27]
            st = l["status"]
            if "SENT" in st:
                st_color = f"{C_GREEN}{st}{RESET}"
            elif st == "AUDITED":
                st_color = f"{C_CYAN}{st}{RESET}"
            else:
                st_color = f"{C_YELLOW}{st}{RESET}"

            print(f"  {C_WHITE}{name:<26}{RESET} {pres:<25} {C_CYAN}{email:<28}{RESET} {st_color}")

    print(f"\n{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")
    input("  Press Enter to return to main menu...")

def handle_priority_followups(active_id):
    interval = getattr(config, "FOLLOW_UP_INTERVAL_DAYS", 3)
    overdue = db.get_overdue_followups(business_id=active_id, interval_days=interval)
    print(f"\n{C_YELLOW}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"  {C_WHITE}OVERDUE FOLLOW-UP DISPATCH CENTER — {C_YELLOW}{active_id.upper()}{RESET}")
    print(f"{C_YELLOW}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")

    if not overdue:
        print(f"\n  {C_GREEN}[✓] Great news, Boss! No overdue follow-ups found for {active_id}. All leads are up to date!{RESET}\n")
        input("  Press Enter to return to main menu...")
        return

    print(f"\n  {C_YELLOW}[!] Found {len(overdue)} warm leads overdue for follow-up (scheduled after {interval} days).{RESET}")
    print(f"  {C_DIM}These leads were sent an initial pitch, and elapsed time has exceeded the schedule because the laptop was offline.{RESET}\n")
    print(f"  {C_DIM}{'BUSINESS NAME':<30} {'RECIPIENT EMAIL':<30} {'ELAPSED':<12} {'OVERDUE'}{RESET}")
    print(f"  {C_DIM}{'─'*30} {'─'*30} {'─'*12} {'─'*14}{RESET}")
    for lead in overdue[:10]:
        bname = lead["business_name"][:28]
        em = (lead["email"] or "N/A")[:28]
        elapsed = f"{lead['days_elapsed']} days"
        over = f"{C_RED}+{lead['days_overdue']}d overdue{RESET}"
        print(f"  {C_WHITE}{bname:<30}{RESET} {C_CYAN}{em:<30}{RESET} {elapsed:<12} {over}")

    if len(overdue) > 10:
        print(f"  {C_DIM}... and {len(overdue) - 10} more leads waiting in queue.{RESET}")

    confirm = input(f"\n  {C_GREEN}Boss, dispatch follow-ups to these {len(overdue)} warm leads right now? [Y/n]: {RESET}").strip().lower()
    if confirm in ["", "y", "yes"]:
        active_b = business_manager.get_business(active_id)
        prof = (active_b.get("sender_profile") if active_b else None) or ("gethotelstays_india" if active_id == "gethotelstays" else "gmail")
        sent = email_engine.dispatch_followups(profile_name=prof, business_id=active_id)
        print(f"\n  {C_GREEN}[✓] Priority Follow-up Wave Completed! Dispatched {sent} follow-ups via {prof}.{RESET}\n")
    else:
        print(f"\n  {C_YELLOW}[!] Follow-ups deferred by operator.{RESET}\n")
    input("  Press Enter to return to main menu...")

def handle_bounce_scan(active_id):
    print(f"\n{C_MAGENTA}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"  {C_WHITE}IMAP INBOX BOUNCE AUDIT & AUTO-BLACKLIST ENGINE{RESET}")
    print(f"{C_MAGENTA}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")
    import bounce_detector
    print(f"  {C_DIM}Scanning connected Gmail accounts for Mailer-Daemon & Delivery failure reports...{RESET}\n")
    res = bounce_detector.scan_all_profiles()
    total_bl = len(db.get_blacklisted_emails(1000))
    print(f"\n  {C_GREEN}[✓] IMAP Bounce Audit Complete!{RESET}")
    print(f"  {C_WHITE}Newly blacklisted:{RESET} {C_YELLOW}{res['total_newly_blacklisted']}{RESET} invalid email addresses.")
    print(f"  {C_WHITE}Total database blacklist:{RESET} {C_CYAN}{total_bl}{RESET} protected addresses (Never contacted again).\n")
    input("  Press Enter to return to main menu...")


def select_sender_account_interactive(active_id):
    profiles, _ = config.list_smtp_profiles()
    active_b = business_manager.get_business(active_id)
    current_key = active_b.get("sender_profile") if active_b else ("gethotelstays_india" if active_id == "gethotelstays" else "gmail")

    print(f"\n{C_CYAN}╔═══════════════════════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"  {C_CYAN}║                ✉ SELECT SENDER OUTREACH ACCOUNT FOR {active_id.upper():<33} ║{RESET}")
    print(f"  {C_CYAN}╚═══════════════════════════════════════════════════════════════════════════════════════════════╝{RESET}\n")

    profile_keys = list(profiles.keys())
    for idx, key in enumerate(profile_keys, 1):
        prof = profiles[key]
        is_active = (key == current_key)
        badge = f"{C_GREEN}[ACTIVE]{RESET}" if is_active else f"{C_DIM}[AVAILABLE]{RESET}"
        print(f"  {C_WHITE}[{idx}]{RESET} {C_CYAN}{prof.get('name', key)}{RESET} — {badge}")
        print(f"      {C_DIM}Email:{RESET} {C_GREEN}{prof.get('email')}{RESET} │ {C_DIM}Sender:{RESET} {prof.get('sender_name')}\n")

    choice = input(f"  {C_GREEN}Select profile number [1-{len(profile_keys)}] or Enter to cancel: {RESET}").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(profile_keys):
        chosen_key = profile_keys[int(choice) - 1]
        business_manager.set_sender_profile(active_id, chosen_key)
        config.set_active_smtp_profile(chosen_key)
        new_prof = profiles[chosen_key]
        print(f"\n  {C_GREEN}[✓] Active sender for {active_id.upper()} updated to: {new_prof.get('email')} ({chosen_key})!{RESET}\n")
        time.sleep(1.5)
        return chosen_key
    else:
        print(f"\n  {C_YELLOW}Sender profile unchanged.{RESET}\n")
        time.sleep(1)
        return current_key

def run_247_hotel_onboarding_loop():
    active_id = "gethotelstays"
    active_b = business_manager.get_business(active_id)
    tgt = business_manager.get_target_settings(active_id)
    def_country = tgt.get("country") or "India"
    def_city = tgt.get("city") or "Goa"

    print(f"\n{C_CYAN}╔═══════════════════════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"  {C_CYAN}║                   🎯 CONFIGURE HOTEL ONBOARDING MISSION & DELIVERY GOAL                       ║{RESET}")
    print(f"  {C_CYAN}╚═══════════════════════════════════════════════════════════════════════════════════════════════╝{RESET}")

    # 1. State / Destination Prompt
    state_input = input(f"  {C_WHITE}1. Target State / City (e.g. Goa, Rajasthan, Manali, Kerala, Jaipur) [{def_city}]: {RESET}").strip()
    city = state_input or def_city
    country = def_country
    niche = "Hotels"
    business_manager.set_target_settings(active_id, country=country, city=city, niche=niche)

    # 2. Channel & Sender Email Selection
    import whatsapp_engine
    is_wa = whatsapp_engine.is_whatsapp_logged_in()
    wa_label = f"{C_GREEN}[CONNECTED]{RESET}" if is_wa else f"{C_YELLOW}[NOT CONNECTED - QR REQUIRED]{RESET}"

    selected_prof_key = (active_b.get("sender_profile") if active_b else None) or "gethotelstays_india"
    ghs_prof = config.get_smtp_config(selected_prof_key)
    ghs_email = ghs_prof.get("email", "gethotelstays.india@gmail.com")

    print(f"\n  {C_WHITE}2. Select Outreach Channel & Sender Account:{RESET}")
    print(f"     {C_CYAN}[1]{RESET} Email Only         — via {C_GREEN}{ghs_email}{RESET}")
    print(f"     {C_CYAN}[2]{RESET} WhatsApp Only      — via Linked WhatsApp Web {wa_label}")
    print(f"     {C_CYAN}[3]{RESET} Dual Multi-Channel — Both Email ({ghs_email}) + WhatsApp {C_YELLOW}(Recommended){RESET}")
    print(f"     {C_CYAN}[S]{RESET} Switch Sender Email — (Currently: {C_YELLOW}{ghs_email}{RESET})")
    ch_choice = input(f"     Choice [1-3, or S to switch sender] (Default 3): ").strip().lower()

    if ch_choice == "s":
        selected_prof_key = select_sender_account_interactive(active_id)
        ghs_prof = config.get_smtp_config(selected_prof_key)
        ghs_email = ghs_prof.get("email", "gethotelstays.india@gmail.com")
        print(f"\n  {C_GREEN}Sender set to: {ghs_email}. Now select outreach channel:{RESET}")
        print(f"     {C_CYAN}[1]{RESET} Email Only │ {C_CYAN}[2]{RESET} WhatsApp Only │ {C_CYAN}[3]{RESET} Dual Multi-Channel")
        ch_choice = input(f"     Choice [1-3] (Default 3): ").strip()

    if ch_choice == "1":
        channel_mode = "EMAIL"
    elif ch_choice == "2":
        channel_mode = "WHATSAPP"
    else:
        channel_mode = "BOTH"

    # 3. Delivered Goal Selection
    print(f"\n  {C_WHITE}3. Desired DELIVERED Outreach Goal:{RESET}")
    print(f"     {C_DIM}Enter how many hotels must receive DELIVERED outreach emails / WhatsApp messages.{RESET}")
    print(f"     {C_YELLOW}[!] Note: Engine will run continuously until exactly this number of messages are DELIVERED.{RESET}")
    goal_input = input(f"     Target Delivered Hotels (e.g. 50, 100, 500) [100]: ").strip()
    try:
        target_goal = int(goal_input) if goal_input else 100
        if target_goal <= 0:
            target_goal = 100
    except ValueError:
        target_goal = 100

    print(f"\n{C_GREEN}╔═══════════════════════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"  {C_GREEN}║             🔥 MISSION CONFIRMED: {target_goal} DELIVERED HOTEL OUTREACHES                            ║{RESET}")
    print(f"  {C_GREEN}╚═══════════════════════════════════════════════════════════════════════════════════════════════╝{RESET}")
    print(f"  {C_WHITE}Target Region:{RESET}  {C_YELLOW}{city}, {country}{RESET}")
    print(f"  {C_WHITE}Channel Mode:{RESET}   {C_CYAN}{channel_mode}{RESET}")
    print(f"  {C_WHITE}Delivery Goal:{RESET}  {C_GREEN}{target_goal} DELIVERED HOTELS{RESET}")
    print(f"  {C_DIM}The engine will crawl, audit and dispatch continuously until {target_goal} hotels are reached.{RESET}")
    print(f"  {C_DIM}Press Ctrl+C at any time to pause or return to menu.{RESET}\n")
    time.sleep(2)

    # Establish baseline delivered count before this mission
    delivered_start = db.get_delivered_count(business_id=active_id, channel=channel_mode)

    # Destination rotation list based on target region
    base_destinations = [city]
    if "goa" in city.lower():
        base_destinations += ["North Goa", "South Goa", "Calangute", "Candolim", "Anjuna", "Panaji", "Baga", "Morjim", "Palolem"]
    elif "rajasthan" in city.lower() or "jaipur" in city.lower():
        base_destinations += ["Jaipur", "Udaipur", "Jodhpur", "Jaisalmer", "Pushkar", "Mount Abu", "Bikaner"]
    elif "himachal" in city.lower() or "manali" in city.lower():
        base_destinations += ["Manali", "Shimla", "Dharamshala", "Kasol", "Kullu", "Spiti", "Bir"]
    elif "kerala" in city.lower():
        base_destinations += ["Munnar", "Kochi", "Alleppey", "Wayanad", "Varkala", "Kovalam", "Thekkady"]
    elif "uttarakhand" in city.lower() or "rishikesh" in city.lower():
        base_destinations += ["Rishikesh", "Mussoorie", "Nainital", "Dehradun", "Haridwar", "Auli"]
    else:
        base_destinations += [f"{city} Central", f"{city} North", f"{city} South", "Goa", "Jaipur", "Udaipur", "Manali", "Rishikesh"]

    # De-duplicate while preserving initial priority
    seen = set()
    clean_destinations = [d for d in base_destinations if not (d.lower() in seen or seen.add(d.lower()))]

    cycle = 1
    while True:
        # Check current progress toward goal
        current_total = db.get_delivered_count(business_id=active_id, channel=channel_mode)
        delivered_in_mission = current_total - delivered_start
        remaining_to_deliver = max(0, target_goal - delivered_in_mission)

        if delivered_in_mission >= target_goal:
            print(f"\n{C_GREEN}╔═══════════════════════════════════════════════════════════════════════════════════════════════╗{RESET}")
            print(f"  {C_GREEN}║             🎉 MISSION ACCOMPLISHED: {target_goal} DELIVERED OUTREACHES COMPLETED!                 ║{RESET}")
            print(f"  {C_GREEN}╚═══════════════════════════════════════════════════════════════════════════════════════════════╝{RESET}")
            stats = db.get_delivered_breakdown(business_id=active_id)
            print(f"  {C_WHITE}Emails Delivered:{RESET}   {C_CYAN}{stats['emails_delivered']}{RESET}")
            print(f"  {C_WHITE}WhatsApp Delivered:{RESET} {C_GREEN}{stats['whatsapp_delivered']}{RESET}")
            print(f"  {C_WHITE}Total Deliveries:{RESET}   {C_YELLOW}{stats['total_delivered']}{RESET}\n")
            input("  Press Enter to return to main menu...")
            break

        current_city = clean_destinations[(cycle - 1) % len(clean_destinations)]
        pct = min(100.0, (delivered_in_mission / target_goal) * 100) if target_goal > 0 else 0

        print(f"\n{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")
        print(f"  {C_WHITE}► [CYCLE #{cycle}] TARGETING: {C_GREEN}{current_city.upper()} ({country.upper()}){RESET}")
        print(f"  {C_YELLOW}PROGRESS: [ {delivered_in_mission} / {target_goal} DELIVERED ] ({pct:.1f}%) │ Remaining Needed: {remaining_to_deliver}{RESET}")
        print(f"{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")

        try:
            # Step 0: Priority Overdue Follow-up Catch-up (Offline Downtime Awareness)
            try:
                overdue = db.get_overdue_followups(business_id=active_id, interval_days=getattr(config, "FOLLOW_UP_INTERVAL_DAYS", 3))
                if overdue:
                    print(f"  {C_YELLOW}[0/4] ⚡ PRIORITY PROTOCOL: Found {len(overdue)} overdue follow-up leads (Laptop was offline). Dispatching now...{RESET}")
                    email_engine.dispatch_followups(profile_name=selected_prof_key, business_id=active_id)
            except Exception:
                pass

            # Step 1: Scrape candidates on Google Maps (batch of 15 if queue is low)
            ready_ghs = len(db.get_leads_ready_for_initial_email(business_id=active_id, limit=20))
            if ready_ghs < 5:
                print(f"  {C_CYAN}[1/4] Discovery queue low ({ready_ghs} ready). Scraping hotels on Maps in {current_city}...{RESET}")
                discovered = maps_crawler.crawl_google_maps(
                    city=current_city,
                    country=country,
                    niche="Hotels",
                    max_places=15,
                    headless=True,
                    business_id=active_id
                )
                print(f"        {C_GREEN}✓ Discovered {len(discovered)} potential properties on Maps{RESET}")
            else:
                print(f"  {C_GREEN}[1/4] Discovery queue healthy ({ready_ghs} verified leads ready). Skipping map scrape.{RESET}")

            # Step 2: Audit websites & extract verified contacts concurrently
            print(f"  {C_CYAN}[2/4] Parallel website auditing & live MX email verification...{RESET}")
            audited = website_auditor.audit_pending_leads(limit=15, business_id=active_id)
            print(f"        {C_GREEN}✓ Extracted details from {len(audited)} properties{RESET}")

            # Step 3: Dispatch Emails if selected
            emails_sent_wave = 0
            if channel_mode in ["EMAIL", "BOTH"]:
                print(f"  {C_CYAN}[3/4] Dispatching official partner onboarding emails via {ghs_email}...{RESET}")
                emails_sent_wave = email_engine.dispatch_initial_emails(limit=min(15, remaining_to_deliver), profile_name=selected_prof_key, business_id=active_id)
                print(f"        {C_GREEN}✓ Successfully delivered {emails_sent_wave} onboarding emails{RESET}")

            # Step 4: Dispatch WhatsApp if selected
            wa_sent_wave = 0
            if channel_mode in ["WHATSAPP", "BOTH"]:
                if whatsapp_engine.is_whatsapp_logged_in():
                    print(f"  {C_CYAN}[3b/4] Dispatching WhatsApp onboarding outreach to mobile contacts...{RESET}")
                    wa_sent_wave = whatsapp_engine.dispatch_whatsapp_queue(limit=min(5, remaining_to_deliver), business_id=active_id, headless=True)
                    print(f"        {C_GREEN}✓ Successfully delivered {wa_sent_wave} WhatsApp messages{RESET}")

            # Follow-ups (maintain 2-day sequence)
            try:
                email_engine.dispatch_followups(profile_name=selected_prof_key, business_id=active_id)
            except Exception:
                pass

            # Update delivered count
            current_total = db.get_delivered_count(business_id=active_id, channel=channel_mode)
            delivered_in_mission = current_total - delivered_start
            remaining_to_deliver = max(0, target_goal - delivered_in_mission)
            pct = min(100.0, (delivered_in_mission / target_goal) * 100) if target_goal > 0 else 0

            print(f"\n  {C_WHITE}MISSION STATUS:{RESET} {C_GREEN}{delivered_in_mission} / {target_goal} DELIVERED{RESET} ({pct:.1f}%) │ {C_YELLOW}{remaining_to_deliver} remaining{RESET}")

            if delivered_in_mission >= target_goal:
                print(f"\n  {C_GREEN}🎉 MISSION ACCOMPLISHED! Successfully reached goal of {target_goal} DELIVERED outreaches!{RESET}\n")
                input("  Press Enter to return to main menu...")
                break

            cycle += 1

            # High-speed continuous delivery cooldown (15s if deliveries active, 30s otherwise)
            cooldown = 15 if (emails_sent_wave > 0 or wa_sent_wave > 0) else 30
            print(f"\n  {C_DIM}Wave #{cycle-1} complete. Continuous pacing active ({cooldown}s). Next wave starts automatically...{RESET}")
            for sec in range(cooldown, 0, -5):
                m, s = divmod(sec, 60)
                sys.stdout.write(f"\r  {C_YELLOW}⏳ Next hunt wave in {m:02d}:{s:02d} — Goal: {delivered_in_mission}/{target_goal} Delivered (Ctrl+C to pause)...{RESET}   ")
                sys.stdout.flush()
                time.sleep(5)
            print()

        except KeyboardInterrupt:
            print(f"\n\n  {C_YELLOW}[!] Mission paused by operator. Delivered so far: {delivered_in_mission} / {target_goal} hotels.{RESET}")
            print(f"  {C_DIM}You can resume anytime by selecting Option [1] again.{RESET}\n")
            time.sleep(1.5)
            break
        except Exception as e:
            print(f"\n  {C_RED}[!] Error in wave #{cycle}: {e}{RESET}")
            print(f"  {C_DIM}Retrying next batch in 30 seconds...{RESET}")
            time.sleep(30)

def run_247_aloria_loop():
    active_id = "aloria_labs"
    tgt = business_manager.get_target_settings(active_id)
    country = tgt.get("country") or "India"
    city = tgt.get("city") or "Mumbai"
    niche = tgt.get("niche") or "Restaurants"

    print(f"\n{C_CYAN}╔═══════════════════════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"  {C_CYAN}║               🚀 24/7 AUTONOMOUS CLIENT ACQUISITION ENGINE ONLINE                             ║{RESET}")
    print(f"  {C_CYAN}║             Mission: High-Converting Web Modernization Discovery & Outreach                  ║{RESET}")
    print(f"  {C_CYAN}╚═══════════════════════════════════════════════════════════════════════════════════════════════╝{RESET}")
    print(f"  {C_WHITE}Target:{RESET}  {C_YELLOW}{niche}{RESET} in {C_CYAN}{city}, {country}{RESET}")
    print(f"  {C_DIM}Mode: 24/7 continuous autonomous execution. Press Ctrl+C anytime to pause/return.{RESET}\n")

    cycle = 1
    while True:
        print(f"\n{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")
        print(f"  {C_WHITE}► [WAVE #{cycle}] CLIENT DISCOVERY WAVE: {C_GREEN}{niche.upper()} IN {city.upper()}, {country.upper()}{RESET}")
        print(f"{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")

        try:
            # Step 0: Priority Overdue Follow-up Catch-up (Offline Downtime Awareness)
            try:
                overdue = db.get_overdue_followups(business_id=active_id, interval_days=getattr(config, "FOLLOW_UP_INTERVAL_DAYS", 3))
                if overdue:
                    print(f"  {C_YELLOW}[0/4] ⚡ PRIORITY PROTOCOL: Found {len(overdue)} overdue follow-up leads (Laptop was offline). Dispatching now...{RESET}")
                    email_engine.dispatch_followups(profile_name="gmail", business_id=active_id)
            except Exception:
                pass

            # 1. Google Maps Hunt (batch size 15 for high pipeline throughput)
            ready_in_db = len(db.get_leads_ready_for_initial_email(business_id=active_id, limit=20))
            if ready_in_db < 5:
                print(f"  {C_CYAN}[1/4] Discovery queue low ({ready_in_db} ready). Scraping local business listings on Maps...{RESET}")
                maps_crawler.crawl_google_maps(
                    city=city,
                    country=country,
                    niche=niche,
                    max_places=15,
                    headless=True,
                    business_id=active_id
                )
            else:
                print(f"  {C_GREEN}[1/4] Discovery queue healthy ({ready_in_db} verified leads ready). Skipping map scrape.{RESET}")

            # 2. Parallel Audit & Contact Extraction
            print(f"  {C_CYAN}[2/4] Concurrently auditing websites & performing live MX verification...{RESET}")
            website_auditor.audit_pending_leads(limit=15, business_id=active_id)

            # 3. Dispatch Initial Pitches
            active_b = business_manager.get_business(active_id)
            selected_prof = (active_b.get("sender_profile") if active_b else None) or "gmail"
            aloria_cfg = config.get_smtp_config(selected_prof)
            aloria_email_disp = aloria_cfg.get("email", "alorialabs@gmail.com")
            print(f"  {C_CYAN}[3/4] Dispatching tailored pitches via {aloria_email_disp} (Turbo Pacing)...{RESET}")
            sent = email_engine.dispatch_initial_emails(limit=15, profile_name=selected_prof, business_id=active_id)
            print(f"        {C_GREEN}✓ Dispatched {sent} tailored pitches{RESET}")

            # 4. Dispatch Follow-ups
            print(f"  {C_CYAN}[4/4] Dispatching scheduled follow-ups via {aloria_email_disp}...{RESET}")
            fu_sent = email_engine.dispatch_followups(profile_name=selected_prof, business_id=active_id)
            print(f"        {C_GREEN}✓ Dispatched {fu_sent} follow-ups{RESET}")

            cycle += 1

            # High-speed continuous pipeline pacing (15-30s instead of 300s)
            cooldown = 20 if sent > 0 else 45
            print(f"\n  {C_DIM}Wave #{cycle-1} complete. Continuous pacing active ({cooldown}s). Next wave starts automatically...{RESET}")
            for sec in range(cooldown, 0, -5):
                m, s = divmod(sec, 60)
                sys.stdout.write(f"\r  {C_YELLOW}⏳ Next cycle in {m:02d}:{s:02d} — Press Ctrl+C to return to menu...{RESET}   ")
                sys.stdout.flush()
                time.sleep(5)
            print()

        except KeyboardInterrupt:
            print(f"\n\n  {C_YELLOW}[!] Client acquisition engine paused by operator.{RESET}\n")
            time.sleep(1)
            break
        except Exception as e:
            print(f"\n  {C_RED}[!] Error in wave #{cycle}: {e}{RESET}")
            time.sleep(15)

def run_cockpit_loop():
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print_banner()
        print_clean_dashboard()

        try:
            choice = input(f"  {C_GREEN}Select option or key: {RESET}").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print(f"\n  {C_CYAN}Closing Hunter Command Center. Farewell.{RESET}\n")
            break

        if choice in ["0", "exit"]:
            print(f"\n  {C_CYAN}Closing Hunter Command Center. Farewell.{RESET}\n")
            break

        active_id = business_manager.get_active_business_id()

        # Switch Business Profile Toggle via 'b'
        if choice == "b":
            new_id = "aloria_labs" if active_id == "gethotelstays" else "gethotelstays"
            business_manager.set_active_business(new_id)
            print(f"\n  {C_GREEN}[✓] Switched active profile to: {new_id.upper()}{RESET}")
            time.sleep(1)
            continue

        # If user typed '2' to switch between profiles
        if choice == "2":
            new_id = "aloria_labs" if active_id == "gethotelstays" else "gethotelstays"
            business_manager.set_active_business(new_id)
            print(f"\n  {C_GREEN}[✓] Switched active profile to: {new_id.upper()}{RESET}")
            time.sleep(1)
            continue

        # [S] Choose Sender Account
        if choice == "s":
            select_sender_account_interactive(active_id)
            continue

        # [L] Ledger
        if choice == "l":
            show_clean_lead_ledger(active_id)
            continue

        # [T] Configure Target
        if choice == "t":
            configure_target(active_id)
            continue

        # [Q] WhatsApp Login QR
        if choice == "q":
            import whatsapp_engine
            try:
                whatsapp_engine.launch_whatsapp_login_qr()
            except Exception as e:
                print(f"  {C_RED}[!] WhatsApp login error: {e}{RESET}")
            input("\n  Press Enter to return to menu...")
            continue

        # [F] Priority Overdue Follow-ups
        if choice == "f":
            handle_priority_followups(active_id)
            continue

        # [C] Scan Inbox Bounces (IMAP)
        if choice == "c":
            handle_bounce_scan(active_id)
            continue

        # [1] or [Enter] - RUN 24/7 AUTONOMOUS ENGINE
        if choice in ["1", ""]:
            if active_id == "gethotelstays":
                run_247_hotel_onboarding_loop()
            else:
                run_247_aloria_loop()
            continue

        # Handle unrecognized choice
        print(f"\n  {C_YELLOW}[!] Key '{choice}' not recognized. Please select from the menu above.{RESET}")
        time.sleep(1.2)

if __name__ == "__main__":
    run_cockpit_loop()
