import os
import sys
import time
from pathlib import Path

# Ensure UTF-8 console on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
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
import runner

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
    businesses, _ = business_manager.list_businesses()
    stats = db.get_funnel_stats(business_id=active_id)

    total = stats.get("total", 0)
    audited = stats.get("audited", 0)
    pitched = stats.get("pitch_sent", 0)
    fu1 = stats.get("follow_up_1", 0)
    fu2 = stats.get("follow_up_2", 0)
    golden = stats.get("golden_leads", 0)
    sent_total = stats.get("emails_sent", 0)

    b_name = active_b.get("name", active_id)
    country = active_b.get("country", "Algeria")
    cities = active_b.get("cities", ["Algiers"])
    niches = active_b.get("default_niches", ["Restaurants"])
    sender = active_b.get("sender_display_name", "Default")

    # Clean Header
    print(f"{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"  {C_WHITE}ACTIVE BUSINESS:{RESET}   {Back.CYAN}{Fore.BLACK} {b_name.upper()} {RESET}  {C_DIM}(Press 1-{len(businesses)} to switch business profile){RESET}")
    print(f"  {C_WHITE}TARGET SECTOR:{RESET}     {C_YELLOW}{niches[0] if niches else 'N/A'}{RESET} in {C_GREEN}{cities[0] if cities else 'N/A'}, {country}{RESET}")
    print(f"  {C_WHITE}SENDER ACCOUNT:{RESET}    {C_CYAN}{sender}{RESET}")
    print(f"  {C_WHITE}PIPELINE STATS:{RESET}    {C_GREEN}{total}{RESET} Leads │ {C_BLUE}{audited}{RESET} Audited │ {C_YELLOW}{pitched}{RESET} Pitched │ {C_MAGENTA}{golden}{RESET} Golden No-Web │ {C_CYAN}{sent_total}{RESET} Sent")
    print(f"{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}\n")

    # Business Switcher Options
    print(f"  {C_YELLOW}─── [SWITCH BUSINESS PROFILE] ─────────────────────────────────────────────────────────────{RESET}")
    keys = list(businesses.keys())
    for idx, b_id in enumerate(keys, 1):
        b = businesses[b_id]
        if b_id == active_id:
            tag = f"{C_GREEN}● [ACTIVE]{RESET}"
            name_str = f"{C_GREEN}{b.get('name', b_id)}{RESET}"
        else:
            tag = f"{C_DIM}○ [STANDBY]{RESET}"
            name_str = f"{C_WHITE}{b.get('name', b_id)}{RESET}"
        print(f"  {C_YELLOW}[{idx}]{RESET} {tag} {name_str} {C_DIM}— {b.get('niche', '')} ({b.get('country', '')}){RESET}")

    # Hunter Operations
    print(f"\n  {C_CYAN}─── [AUTOMATION OPERATIONS] ───────────────────────────────────────────────────────────────{RESET}")
    print(f"  {C_WHITE}[H]{RESET} {C_GREEN}● Live Hunter{RESET}            {C_DIM}— Watch visible Chrome window scrape Google Maps live{RESET}")
    print(f"  {C_WHITE}[S]{RESET} {C_CYAN}● Silent Ghost Hunter{RESET}    {C_DIM}— Run Maps crawler silently in background (headless){RESET}")
    print(f"  {C_WHITE}[D]{RESET} {C_YELLOW}● Safe Dry-Run{RESET}           {C_DIM}— Scrape & audit leads without sending emails{RESET}")
    print(f"  {C_WHITE}[A]{RESET} {C_BLUE}● Run Website Auditor{RESET}    {C_DIM}— Inspect website speeds, SSL & extract emails{RESET}")
    print(f"  {C_WHITE}[E]{RESET} {C_MAGENTA}● Dispatch Email Queue{RESET}   {C_DIM}— Send tailored Day 0 cold pitches for active business{RESET}")
    print(f"  {C_WHITE}[F]{RESET} {C_YELLOW}● Dispatch Follow-ups{RESET}    {C_DIM}— Send scheduled 2-Day & 4-Day follow-up sequence{RESET}")
    print(f"  {C_WHITE}[R]{RESET} {C_GREEN}● Full Autopilot Wave{RESET}    {C_DIM}— 1-Click Hunt ➔ Audit ➔ Pitch ➔ Follow-up cycle{RESET}")
    print(f"  {C_WHITE}[L]{RESET} {C_CYAN}● Lead Ledger & History{RESET}  {C_DIM}— View all leads, email contacts & outreach status{RESET}")
    print(f"  {C_WHITE}[M]{RESET} {C_MAGENTA}● Mobile Command App{RESET}     {C_DIM}— Launch phone control server (Open on your mobile){RESET}")
    print(f"  {C_WHITE}[0]{RESET} {C_RED}● Exit Console{RESET}           {C_DIM}— Close Hunter Command Center{RESET}\n")

def show_clean_lead_ledger(active_id):
    leads = db.get_lead_ledger(business_id=active_id, limit=50)
    active_b = business_manager.get_business(active_id)
    b_name = active_b.get("name", active_id) if active_b else active_id

    print(f"\n{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f"  {C_WHITE}LEAD LEDGER FOR {C_YELLOW}{b_name.upper()}{RESET} ({len(leads)} leads recorded)")
    print(f"{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")

    if not leads:
        print(f"\n  {C_DIM}No leads discovered yet for this profile. Run Option [H] to hunt.{RESET}\n")
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

        if choice in ["0", "q", "exit"]:
            print(f"\n  {C_CYAN}Closing Hunter Command Center. Farewell.{RESET}\n")
            break

        # Switch Business Profile
        businesses, _ = business_manager.list_businesses()
        if choice.isdigit() and 1 <= int(choice) <= len(businesses):
            keys = list(businesses.keys())
            idx = int(choice) - 1
            chosen_id = keys[idx]
            business_manager.set_active_business(chosen_id)
            print(f"\n  {C_GREEN}[✓] Switched active business to: {businesses[chosen_id].get('name')}{RESET}")
            time.sleep(1)
            continue

        # [L] Ledger
        if choice == "l":
            active_id = business_manager.get_active_business_id()
            show_clean_lead_ledger(active_id)
            continue

        # Active business parameters
        active_id = business_manager.get_active_business_id()
        active_b = business_manager.get_active_business()
        country = active_b.get("country", "Algeria")
        cities = active_b.get("cities", ["Algiers"])
        niches = active_b.get("default_niches", ["Restaurants"])
        sender_prof = active_b.get("sender_profile", "gmail")
        city = cities[0] if cities else "Algiers"
        niche = niches[0] if niches else "Restaurants"

        # [H] Live Hunter
        if choice == "h":
            print(f"\n  {C_CYAN}[► LAUNCHING LIVE MAPS HUNTER]{RESET}")
            print(f"  Target: {C_WHITE}{niche}{RESET} in {C_GREEN}{city}, {country}{RESET} for {C_YELLOW}{active_b.get('name')}{RESET}")
            cnt = input("  Max places to scrape (default 5): ").strip()
            limit = int(cnt) if cnt.isdigit() else 5
            try:
                maps_crawler.crawl_google_maps(
                    city=city,
                    country=country,
                    niche=niche,
                    max_places=limit,
                    headless=False,
                    business_id=active_id
                )
            except Exception as e:
                print(f"  {C_RED}[!] Error: {e}{RESET}")
            input("\n  Press Enter to return to menu...")

        # [S] Silent Hunter (Headless)
        elif choice == "s":
            print(f"\n  {C_CYAN}[► LAUNCHING SILENT BACKGROUND HUNTER]{RESET}")
            print(f"  Target: {C_WHITE}{niche}{RESET} in {C_GREEN}{city}, {country}{RESET}")
            try:
                maps_crawler.crawl_google_maps(
                    city=city,
                    country=country,
                    niche=niche,
                    max_places=5,
                    headless=True,
                    business_id=active_id
                )
            except Exception as e:
                print(f"  {C_RED}[!] Error: {e}{RESET}")
            input("\n  Press Enter to return to menu...")

        # [D] Safe Dry-Run
        elif choice == "d":
            print(f"\n  {C_YELLOW}[► RUNNING SAFE DRY-RUN (NO EMAILS)]{RESET}")
            try:
                maps_crawler.crawl_google_maps(
                    city=city,
                    country=country,
                    niche=niche,
                    max_places=3,
                    headless=False,
                    business_id=active_id
                )
                website_auditor.audit_pending_leads(limit=3, business_id=active_id)
            except Exception as e:
                print(f"  {C_RED}[!] Error: {e}{RESET}")
            input("\n  Press Enter to return to menu...")

        # [A] Website Auditor
        elif choice == "a":
            print(f"\n  {C_BLUE}[► RUNNING WEBSITE AUDITOR]{RESET}")
            try:
                website_auditor.audit_pending_leads(limit=10, business_id=active_id)
            except Exception as e:
                print(f"  {C_RED}[!] Error: {e}{RESET}")
            input("\n  Press Enter to return to menu...")

        # [E] Dispatch Email Queue
        elif choice == "e":
            print(f"\n  {C_MAGENTA}[► DISPATCHING COLD OUTREACH QUEUE]{RESET}")
            try:
                sent = email_engine.dispatch_initial_emails(limit=5, profile_name=sender_prof, business_id=active_id)
                print(f"\n  {C_GREEN}[✓] Dispatched {sent} initial emails!{RESET}")
            except Exception as e:
                print(f"  {C_RED}[!] Error: {e}{RESET}")
            input("\n  Press Enter to return to menu...")

        # [F] Dispatch Follow-ups
        elif choice == "f":
            print(f"\n  {C_YELLOW}[► DISPATCHING SCHEDULED 2-DAY / 4-DAY FOLLOW-UPS]{RESET}")
            try:
                sent = email_engine.dispatch_followups(profile_name=sender_prof, business_id=active_id)
                print(f"\n  {C_GREEN}[✓] Dispatched {sent} follow-up emails!{RESET}")
            except Exception as e:
                print(f"  {C_RED}[!] Error: {e}{RESET}")
            input("\n  Press Enter to return to menu...")

        # [R] Full Autopilot Wave
        elif choice == "r":
            print(f"\n  {C_MAGENTA}[► RUNNING FULL AUTOPILOT WAVE FOR {active_b.get('name').upper()}]{RESET}")
            try:
                # 1. Hunt
                maps_crawler.crawl_google_maps(city=city, country=country, niche=niche, max_places=5, headless=False, business_id=active_id)
                # 2. Audit
                website_auditor.audit_pending_leads(limit=5, business_id=active_id)
                # 3. Pitch
                email_engine.dispatch_initial_emails(limit=5, profile_name=sender_prof, business_id=active_id)
                # 4. Follow-up
                email_engine.dispatch_followups(profile_name=sender_prof, business_id=active_id)
                print(f"\n  {C_GREEN}[✓] Autopilot wave complete!{RESET}")
            except Exception as e:
                print(f"  {C_RED}[!] Error: {e}{RESET}")
            input("\n  Press Enter to return to menu...")

        # [M] Mobile Server
        elif choice == "m":
            import mobile_server
            mobile_server.run_server()
            input("\n  Press Enter to return to menu...")

if __name__ == "__main__":
    run_cockpit_loop()
