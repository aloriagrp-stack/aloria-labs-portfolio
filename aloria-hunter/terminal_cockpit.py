import os

import sys

import time

import subprocess

from pathlib import Path



# Ensure UTF-8 console on Windows with replacement fallback

if sys.platform == "win32":

    try:

        if hasattr(sys.stdout, "reconfigure"):

            sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore

        if hasattr(sys.stderr, "reconfigure"):

            sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore

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

if os.name == "nt" and os.path.exists("D:\\playwright-browsers"):
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



    interval = getattr(config, "FOLLOW_UP_INTERVAL_DAYS", 3)

    try:

        overdue = db.get_overdue_followups(business_id=active_id, interval_days=interval)

    except Exception:

        overdue = []

    try:

        bl_count = len(db.get_blacklisted_emails(1000))

    except Exception:

        bl_count = 0

    overdue_badge = f"{C_RED}● {len(overdue)} OVERDUE{RESET}" if overdue else f"{C_GREEN}● All Clear{RESET}"



    if active_id == "gethotelstays":

        profiles, _ = config.list_smtp_profiles()

        ghs_keys = [k for k in profiles.keys() if "gethotelstays" in k.lower() and profiles[k].get("password")]

        ghs_emails = [profiles[k].get("email", "") for k in ghs_keys if profiles[k].get("email")]

        if len(ghs_emails) > 1:

            ghs_sender_str = f"⚡ Multi-Sender Swarm ({len(ghs_emails)} Accounts: {' + '.join(ghs_emails)})"

        else:

            ghs_prof_key = active_b.get("sender_profile") or "gethotelstays"

            ghs_prof = config.get_smtp_config(ghs_prof_key)

            ghs_email = ghs_prof.get("email", "gethotelstays02@gmail.com")

            ghs_name = ghs_prof.get("sender_name", "Shriyansh Aloria — GetHotelStays")

            ghs_sender_str = f"{ghs_name} <{ghs_email}>"



        print(f"{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")

        print(f"  {C_WHITE}ACTIVE AGENT:{RESET}       {Back.CYAN}{Fore.BLACK} GETHOTELSTAYS — 24/7 HOTEL PARTNER ONBOARDING {RESET}  {C_DIM}(Press B to switch){RESET}")

        print(f"  {C_WHITE}TARGET DESTINATION:{RESET} {loc_str} │ {niche_str}")

        print(f"  {C_WHITE}SENDER ACCOUNT:{RESET}     {C_GREEN}{ghs_sender_str}{RESET}  {C_YELLOW}[Press S to change]{RESET}")

        print(f"  {C_WHITE}WHATSAPP ENGINE:{RESET}    {wa_badge}")

        print(f"  {C_WHITE}PIPELINE STATS:{RESET}     {C_GREEN}{total}{RESET} Hotels Discovered │ {C_BLUE}{audited}{RESET} Audited │ {C_YELLOW}{pitched}{RESET} Pitched │ {C_CYAN}{sent_total}{RESET} Sent │ {C_RED}{bl_count}{RESET} Bounces Blacklisted")

        swarm_info = db.get_swarm_daily_stats(active_id)

        quota_per_acc = config.get_max_delivered_quota(active_id)

        if swarm_info["accounts"]:

            tot_del = swarm_info["total_delivered_today"]

            max_cap = swarm_info["max_capacity_today"]

            q_badge = f"{C_GREEN}✓ COMPLETE ({tot_del}/{max_cap}){RESET}" if swarm_info["all_quotas_completed"] else f"{C_YELLOW}{tot_del}/{max_cap} Delivered Today{RESET}"

            print(f"  {C_WHITE}SWARM QUOTA:{RESET}        {q_badge} {C_DIM}(Max {quota_per_acc} delivered emails per account across {len(swarm_info['accounts'])} accounts){RESET}")

        print(f"{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}\n")



        if overdue:

            try:

                max_days = overdue[0].get("days_elapsed", 0)

                over_days = overdue[0].get("days_overdue", 0)

            except Exception:

                max_days, over_days = 0, 0

            print(f"  {Back.RED}{Fore.WHITE} ⚠️  ATTENTION BOSS: {len(overdue)} OVERDUE FOLLOW-UPS DETECTED (LAPTOP WAS OFFLINE) {RESET}")

            print(f"  {C_YELLOW}► Initial pitch sent {max_days} days ago ({over_days} days overdue because laptop was turned off).{RESET}")

            print(f"  {C_YELLOW}► {C_GREEN}RECOMMENDED:{RESET} {C_WHITE}Press {C_GREEN}[F]{C_WHITE} to dispatch follow-ups to these warm leads before hunting new ones!{RESET}\n")



        print(f"  {C_YELLOW}─── [ACTIVE AGENT PROFILE] ────────────────────────────────────────────────────────────────{RESET}")

        print(f"  {C_GREEN}● [ACTIVE]{RESET}  {C_WHITE}GetHotelStays{RESET} — Autonomous Hotel Partner Onboarding ({loc_str})")

        print(f"  {C_DIM}○ [STANDBY] Aloria Labs  — Web & Digital Infrastructure Agency (Press [B] to toggle){RESET}")



        print(f"\n  {C_GREEN}─── [AUTONOMOUS 24/7 HOTEL ONBOARDING ENGINE] ─────────────────────────────────────────────{RESET}")

        print(f"  {C_WHITE}[1]{RESET} {C_GREEN}🔥 START 24/7 HOTEL ONBOARDING{RESET}   {C_DIM}— Runs continuously: Discover ➔ Extract ➔ Pitch ➔ Follow-up{RESET}")
        print(f"  {C_WHITE}[A]{RESET} {C_CYAN}🧠 AI Autonomous Closer Engine{RESET}  {C_DIM}— Auto-replies, negotiates & closes hotel replies in your tone{RESET}")

        print(f"  {C_WHITE}[F]{RESET} {C_YELLOW}⚡ Priority Overdue Follow-ups{RESET}  {overdue_badge} {C_DIM}— Offline catch-up before new leads{RESET}")

        print(f"  {C_WHITE}[C]{RESET} {C_MAGENTA}🛡 Scan Inbox Bounces (IMAP){RESET}    {C_CYAN}{bl_count} Blacklisted{RESET} {C_DIM}— Auto-blacklist dead emails{RESET}")

        print(f"  {C_WHITE}[T]{RESET} {C_CYAN}⚙ Set Target City / State{RESET}        {C_DIM}— Destination (Currently: {tgt_city or 'Goa'}, {tgt_country or 'India'}){RESET}")

        print(f"  {C_WHITE}[L]{RESET} {C_YELLOW}📋 Hotel Pipeline & Ledger{RESET}        {C_DIM}— Opens live ledger in a separate pop-up window ↗{RESET}")

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

        aloria_swarm = db.get_swarm_daily_stats("aloria_labs")

        aloria_quota = config.get_max_delivered_quota("aloria_labs")

        if aloria_swarm["accounts"]:

            tot_del = aloria_swarm["total_delivered_today"]

            max_cap = aloria_swarm["max_capacity_today"]

            q_badge = f"{C_GREEN}✓ COMPLETE ({tot_del}/{max_cap}){RESET}" if aloria_swarm["all_quotas_completed"] else f"{C_YELLOW}{tot_del}/{max_cap} Delivered Today{RESET}"

            print(f"  {C_WHITE}DAILY QUOTA:{RESET}        {q_badge} {C_DIM}(Max {aloria_quota} delivered emails per account across {len(aloria_swarm['accounts'])} accounts){RESET}")

        print(f"{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}\n")



        if overdue:

            try:

                max_days = overdue[0].get("days_elapsed", 0)

                over_days = overdue[0].get("days_overdue", 0)

            except Exception:

                max_days, over_days = 0, 0

            print(f"  {Back.RED}{Fore.WHITE} ⚠️  ATTENTION BOSS: {len(overdue)} OVERDUE FOLLOW-UPS DETECTED (LAPTOP WAS OFFLINE) {RESET}")

            print(f"  {C_YELLOW}► Initial pitch sent {max_days} days ago ({over_days} days overdue because laptop was turned off).{RESET}")

            print(f"  {C_YELLOW}► {C_GREEN}RECOMMENDED:{RESET} {C_WHITE}Press {C_GREEN}[F]{C_WHITE} to dispatch follow-ups to these warm leads before hunting new ones!{RESET}\n")



        print(f"  {C_YELLOW}─── [ACTIVE AGENT PROFILE] ────────────────────────────────────────────────────────────────{RESET}")

        print(f"  {C_GREEN}● [ACTIVE]{RESET}  {C_WHITE}Aloria Labs{RESET}  — Web & Custom Software Agency ({loc_str})")

        print(f"  {C_DIM}○ [STANDBY] GetHotelStays — Autonomous Hotel Partner Onboarding (Press [B] to toggle){RESET}")



        print(f"\n  {C_CYAN}─── [AUTONOMOUS 24/7 CLIENT ACQUISITION ENGINE] ───────────────────────────────────────────{RESET}")

        print(f"  {C_WHITE}[1]{RESET} {C_GREEN}🚀 START 24/7 CLIENT ACQUISITION{RESET} {C_DIM}— Non-stop: Maps ➔ Web Audits ➔ Custom Pitches ➔ Follow-up{RESET}")

        print(f"  {C_WHITE}[F]{RESET} {C_YELLOW}⚡ Priority Overdue Follow-ups{RESET}  {overdue_badge} {C_DIM}— Offline catch-up before new leads{RESET}")

        print(f"  {C_WHITE}[C]{RESET} {C_MAGENTA}🛡 Scan Inbox Bounces (IMAP){RESET}    {C_CYAN}{bl_count} Blacklisted{RESET} {C_DIM}— Auto-blacklist dead emails{RESET}")

        print(f"  {C_WHITE}[T]{RESET} {C_CYAN}⚙ Set Target Location / Niche{RESET}   {C_DIM}— Industry & location targeting{RESET}")

        print(f"  {C_WHITE}[L]{RESET} {C_YELLOW}📋 Client Pipeline & Ledger{RESET}       {C_DIM}— Opens live ledger in a separate pop-up window ↗{RESET}")

        print(f"  {C_WHITE}[B]{RESET} {C_BLUE}🔄 Switch to GetHotelStays{RESET}       {C_DIM}— Switch to Hotel Onboarding Agent{RESET}")

        print(f"  {C_WHITE}[0]{RESET} {C_RED}✖ Exit Console{RESET}                    {C_DIM}— Close Hunter Command Center{RESET}\n")



def configure_target(b_id):

    b = business_manager.get_business(b_id)

    b_name = str((b.get("name") if b else None) or b_id or "")

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

    b_name = str((active_b.get("name") if active_b else None) or active_id or "")



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

    input("  Press Enter to close this ledger window...")



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





def handle_direct_hunt(active_id):

    active_b = business_manager.get_business(active_id)

    b_name = str((active_b.get("name") if active_b else None) or active_id or "")

    tgt = business_manager.get_target_settings(active_id)

    default_c = tgt.get("country", "India")

    default_ci = tgt.get("city", "Goa" if active_id == "gethotelstays" else "Mumbai")

    default_ni = tgt.get("niche", "Hotels" if active_id == "gethotelstays" else "Restaurants")



    print(f"\n{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")

    print(f"  {C_WHITE}HUNT FRESH LEADS (1-BROWSER 12-TABS SWARM) — {C_YELLOW}{b_name.upper()}{RESET}")

    print(f"  {C_DIM}This mode strictly discovers & audits new properties. Zero cold emails or follow-ups dispatched.{RESET}")

    print(f"{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")



    city_in = input(f"  {C_WHITE}Target City / State [{default_ci}]: {RESET}").strip() or default_ci

    country_in = input(f"  {C_WHITE}Target Country [{default_c}]: {RESET}").strip() or default_c

    niche_in = input(f"  {C_WHITE}Category / Niche [{default_ni}]: {RESET}").strip() or default_ni

    goal_str = input(f"  {C_WHITE}How many leads to harvest? [50]: {RESET}").strip() or "50"

    try:

        goal = int(goal_str)

    except ValueError:

        goal = 50



    print(f"\n  {C_GREEN}[*] Launching 1-Browser 12-Tabs Harvester for {niche_in} in {city_in}, {country_in}...{RESET}\n")

    try:

        import swarm_hunter

        discovered = swarm_hunter.hunt_with_swarm(

            city=city_in,

            country=country_in,

            niche=niche_in,

            goal=goal,

            business_id=active_id,

            workers_count=12,

            max_concurrency=12,

            headless=True,

            auto_audit=False

        )

    except Exception as sw_err:

        discovered = maps_crawler.crawl_google_maps(

            city=city_in,

            country=country_in,

            niche=niche_in,

            max_places=goal,

            headless=True,

            business_id=active_id

        )

    print(f"\n  {C_CYAN}[*] Auditing discovered websites & extracting MX-verified contacts...{RESET}")

    website_auditor.audit_pending_leads(limit=goal, business_id=active_id)

    print(f"\n  {C_GREEN}[✓] Hunt Finished! Discovered & audited {len(discovered)} fresh leads for {active_id}.{RESET}")

    input("  Press Enter to return to main menu...")



def handle_bounce_scan(active_id):

    print(f"\n{C_MAGENTA}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")

    print(f"  {C_WHITE}HOTELSTAYS SENTINEL: INBOX REPLIES & BOUNCE AUDIT ENGINE{RESET}")

    print(f"{C_MAGENTA}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")

    from agents.sentinel_agent import HotelSentinelAgent

    print(f"  {C_DIM}Scanning connected Gmail accounts for incoming partner replies & bounce reports...{RESET}\n")

    sentinel = HotelSentinelAgent()

    sentinel.execute_inbox_scan()

    total_bl = len(db.get_blacklisted_emails(1000))

    print(f"\n  {C_GREEN}[✓] Sentinel Audit Complete!{RESET}")

    print(f"  {C_WHITE}Replies Detected:{RESET} {C_GREEN}{sentinel.total_replies_found}{RESET} hotel partners marked REPLIED (Follow-ups halted)")

    print(f"  {C_WHITE}Bounces Blacklisted:{RESET} {C_YELLOW}{sentinel.total_bounces_found}{RESET} dead inboxes protected")

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



    if not def_country or def_country.lower() in ["united states of america", "usa", "us"]:

        def_country = "India"



    # 1. State / Destination Prompt with Intelligent Country Detection

    state_input = input(f"  {C_WHITE}1. Target Destination / State / City (e.g. Goa, Rajasthan, Dubai, Kerala) [{def_city}]: {RESET}").strip()

    raw_dest = state_input or def_city

    raw_lower = raw_dest.lower()



    if "," in raw_dest:

        parts = [p.strip() for p in raw_dest.split(",", 1)]

        city = parts[0]

        country = parts[1]

    elif any(k in raw_lower for k in ["dubai", "uae", "emirates", "abu dhabi", "sharjah", "ajman", "ras al khaimah"]):

        city = "Dubai" if "dubai" in raw_lower else raw_dest

        country = "UAE"

    elif any(k in raw_lower for k in ["singapore"]):

        city = "Singapore"

        country = "Singapore"

    elif any(k in raw_lower for k in ["bangkok", "phuket", "pattaya", "thailand", "chiang mai"]):

        city = raw_dest

        country = "Thailand"

    elif any(k in raw_lower for k in ["bali", "jakarta", "indonesia"]):

        city = raw_dest

        country = "Indonesia"

    elif any(k in raw_lower for k in ["london", "uk", "united kingdom", "manchester", "edinburgh"]):

        city = raw_dest

        country = "UK"

    elif any(k in raw_lower for k in ["usa", "united states", "new york", "miami", "florida", "california"]):

        city = raw_dest

        country = "USA"

    else:

        city = raw_dest

        country = def_country or "India"



    niche = "Hotels"

    business_manager.set_target_settings(active_id, country=country, city=city, niche=niche)



    # 2. Channel & Sender Email Selection

    import whatsapp_engine

    is_wa = whatsapp_engine.is_whatsapp_logged_in()

    wa_label = f"{C_GREEN}[CONNECTED]{RESET}" if is_wa else f"{C_YELLOW}[NOT CONNECTED - QR REQUIRED]{RESET}"



    profiles, _ = config.list_smtp_profiles()

    ghs_keys = [k for k in profiles.keys() if "gethotelstays" in k.lower() and profiles[k].get("password")]

    ghs_emails = [profiles[k].get("email", "") for k in ghs_keys if profiles[k].get("email")]

    pool_label = f"Multi-Sender Swarm ({len(ghs_emails)} Accounts: {' + '.join(ghs_emails)})" if len(ghs_emails) > 1 else (ghs_emails[0] if ghs_emails else "gethotelstays02@gmail.com")



    print(f"\n  {C_WHITE}2. Select Outreach Channel & Sender Account:{RESET}")

    print(f"     {C_CYAN}[1]{RESET} Dual Multi-Channel — Both Email ({C_GREEN}{pool_label}{RESET}) + WhatsApp {wa_label} {C_YELLOW}(Recommended - Fastest){RESET}")

    print(f"     {C_CYAN}[2]{RESET} Email Only         — via {C_GREEN}{pool_label}{RESET}")

    print(f"     {C_CYAN}[3]{RESET} WhatsApp Only      — via Linked WhatsApp Web {wa_label}")

    print(f"     {C_CYAN}[S]{RESET} Switch Specific Sender — (Active Pool: {C_YELLOW}{len(ghs_emails)} Accounts Rotating{RESET})")

    ch_choice = input(f"     Choice [1-3, or S to switch sender] (Default 1): ").strip().lower()



    selected_prof_key = None

    if ch_choice == "s":

        selected_prof_key = select_sender_account_interactive(active_id)

        ghs_prof = config.get_smtp_config(selected_prof_key)

        ghs_email = ghs_prof.get("email", "gethotelstays02@gmail.com")

        print(f"\n  {C_GREEN}Single sender locked to: {ghs_email}. Now select outreach channel:{RESET}")

        print(f"     {C_CYAN}[1]{RESET} Dual Multi-Channel │ {C_CYAN}[2]{RESET} Email Only │ {C_CYAN}[3]{RESET} WhatsApp Only")

        ch_choice = input(f"     Choice [1-3] (Default 1): ").strip()



    if ch_choice == "2":

        channel_mode = "EMAIL"

    elif ch_choice == "3":

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



    # 4. Follow-up Strategy Selection (Skip Follow-ups Option)

    print(f"\n  {C_WHITE}4. Follow-up Strategy:{RESET}")

    print(f"     {C_CYAN}[1]{RESET} Standard: Fresh Pitches + Scheduled Follow-ups {C_GREEN}(Default){RESET}")

    print(f"     {C_CYAN}[2]{RESET} Skip Follow-ups: Fresh Pitches ONLY {C_YELLOW}(Follow-ups OFF — 100% fresh leads){RESET}")

    fu_choice = input(f"     Choice [1-2] (Default 1): ").strip()

    enable_followups = (fu_choice != "2")

    fu_badge = f"{C_GREEN}Active (2-day cycle){RESET}" if enable_followups else f"{C_YELLOW}DISABLED (Fresh Leads Only){RESET}"



    print(f"\n{C_GREEN}╔═══════════════════════════════════════════════════════════════════════════════════════════════╗{RESET}")

    print(f"  {C_GREEN}║             🔥 MISSION CONFIRMED: {target_goal} DELIVERED HOTEL OUTREACHES                            ║{RESET}")

    print(f"  {C_GREEN}╚═══════════════════════════════════════════════════════════════════════════════════════════════╝{RESET}")

    print(f"  {C_WHITE}Target Region:{RESET}  {C_YELLOW}{city}, {country}{RESET}")

    print(f"  {C_WHITE}Channel Mode:{RESET}   {C_CYAN}{channel_mode}{RESET}")

    print(f"  {C_WHITE}Delivery Goal:{RESET}  {C_GREEN}{target_goal} DELIVERED HOTELS{RESET}")

    print(f"  {C_WHITE}Follow-ups:{RESET}     {fu_badge}")

    print(f"  {C_DIM}The engine will crawl, audit and dispatch continuously until {target_goal} hotels are reached.{RESET}")

    print(f"  {C_DIM}Press Ctrl+C at any time to pause or return to menu.{RESET}\n")

    time.sleep(2)



    # Establish baseline delivered count before this mission

    delivered_start = db.get_delivered_count(business_id=active_id, channel=channel_mode)



    # Destination rotation list based on target region

    base_destinations = [city]

    city_lower = city.lower()

    is_nationwide = any(k in city_lower for k in ["india", "all", "nation", "country"])

    if is_nationwide:

        # All-India Top Hospitality Hubs covering all major Indian states & travel corridors

        base_destinations = [

            "Goa", "Jaipur Rajasthan", "Udaipur Rajasthan", "Mumbai Maharashtra", "Delhi NCR", "Manali Himachal", 

            "Munnar Kerala", "Rishikesh Uttarakhand", "Bengaluru Karnataka", "Shimla Himachal", "Kochi Kerala",

            "Agra UP", "Ooty Tamil Nadu", "Chandigarh", "Amritsar Punjab", "Varanasi UP", "Pondicherry",

            "Jodhpur Rajasthan", "Dharamshala Himachal", "Lonavala Maharashtra", "Mussoorie Uttarakhand", "Coorg Karnataka",

            "Kolkata West Bengal", "Srinagar Kashmir", "Jaisalmer Rajasthan", "Nainital Uttarakhand", "Mysore Karnataka",

            "Alleppey Kerala", "Hyderabad Telangana", "Mahabaleshwar Maharashtra", "Gangtok Sikkim", "Shillong Meghalaya",

            "Gokarna Karnataka", "Puri Odisha", "Indore Madhya Pradesh", "Dehradun Uttarakhand", "Wayanad Kerala"

        ]

    elif any(k in city_lower for k in ["dubai", "uae", "emirates"]):

        base_destinations = [

            "Dubai Downtown", "Dubai Marina", "Deira Dubai", "Bur Dubai", "Palm Jumeirah", 

            "Jumeirah Beach Dubai", "Business Bay Dubai", "Al Barsha Dubai", "Al Rigga Dubai", "Al Garhoud Dubai"

        ]

    elif "goa" in city_lower:

        base_destinations += ["North Goa", "South Goa", "Calangute", "Candolim", "Anjuna", "Panaji", "Baga", "Morjim", "Palolem"]

    elif "rajasthan" in city_lower or "jaipur" in city_lower:

        base_destinations += ["Jaipur", "Udaipur", "Jodhpur", "Jaisalmer", "Pushkar", "Mount Abu", "Bikaner"]

    elif "himachal" in city_lower or "manali" in city_lower:

        base_destinations += ["Manali", "Shimla", "Dharamshala", "Kullu", "Chandigarh", "Kalka", "Solan", "Dalhousie", "Rishikesh"]

    elif "kerala" in city_lower:

        base_destinations += ["Munnar", "Kochi", "Alleppey", "Wayanad", "Varkala", "Kovalam", "Thekkady"]

    elif "uttarakhand" in city_lower or "rishikesh" in city_lower:

        base_destinations += ["Rishikesh", "Mussoorie", "Nainital", "Dehradun", "Haridwar", "Auli"]

    elif str(country).upper() == "INDIA":

        base_destinations += ["Goa", "Jaipur", "Udaipur", "Mumbai", "Delhi NCR", "Chandigarh", "Rishikesh", "Shimla", "Manali"]



    # De-duplicate while preserving initial priority

    seen = set()

    clean_destinations = [d for d in base_destinations if not (d.lower() in seen or seen.add(d.lower()))]



    cycle = 1

    delivered_in_wave = 0

    consecutive_zero_passes = 0

    WAVE_GOAL = 50

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



        # Check if email channel is requested, but today's email quota is already 100% full

        if channel_mode in ["EMAIL", "BOTH"]:

            swarm_info = db.get_swarm_daily_stats(active_id)

            working_accs = [a for a in swarm_info["accounts"] if a["key"] not in getattr(email_engine, "_FAILED_AUTH_PROFILES", set())]

            all_quota_done = all(a["quota_reached"] for a in working_accs) if working_accs else True

            if all_quota_done:

                tot_done = sum(a["delivered_today"] for a in working_accs)

                quota_per_acc = config.get_max_delivered_quota(active_id)

                print(f"\n{C_CYAN}  ╔═══════════════════════════════════════════════════════════════════════════════════════╗{RESET}")

                print(f"  {C_GREEN}║             ⭐ AAJ KA DAILY EMAIL OUTREACH QUOTA COMPLETE HO GAYA!                     ║{RESET}")

                print(f"  {C_CYAN}╠═══════════════════════════════════════════════════════════════════════════════════════╣{RESET}")

                print(f"  {C_WHITE}║  Boss, sabhi active accounts se aaj ka {quota_per_acc}-email quota ({tot_done} delivered) poora ho chuka hai! ║{RESET}")

                print(f"  {C_YELLOW}║  Ab agle din raat 12:00 baje ke baad (new calendar day) fresh hunt try karein.        ║{RESET}")

                print(f"  {C_CYAN}╚═══════════════════════════════════════════════════════════════════════════════════════╝{RESET}\n")

                if channel_mode == "EMAIL":

                    input("  Press Enter to return to main menu...")

                    break

                else:

                    print(f"  {C_YELLOW}[ℹ️ EMAIL QUOTA REACHED] Email quota satisfied for today. Continuing with WhatsApp outreach...{RESET}\n")



        try:

            # Step 1: Lead Discovery (Multi-State Swarm for nationwide India / Harvester for local)

            ready_ghs = len(db.get_leads_ready_for_initial_email(business_id=active_id, limit=50))

            if ready_ghs < remaining_to_deliver:

                needed_leads = max(30, min(100, remaining_to_deliver * 3))

                if is_nationwide:

                    try:

                        import swarm_hunter

                        print(f"  {C_CYAN}[1/4] Deploying 1-Browser 12-Tabs Swarm across Indian States (Wave #{cycle})...{RESET}")

                        swarm_hunter.hunt_with_swarm(

                            city="India",

                            country=country,

                            niche="Hotels",

                            goal=needed_leads,

                            business_id=active_id,

                            workers_count=12,

                            max_concurrency=12,

                            cycle=cycle,

                            headless=True,

                            auto_audit=False

                        )

                    except Exception as sw_err:

                        print(f"  {C_YELLOW}[!] Swarm fallback to single crawler: {sw_err}{RESET}")

                        maps_crawler.crawl_google_maps(

                            city=current_city,

                            country=country,

                            niche="Hotels",

                            max_places=needed_leads,

                            headless=True,

                            business_id=active_id

                        )

                else:

                    print(f"  {C_CYAN}[1/4] Discovery buffer needs fresh leads ({ready_ghs} ready). Deploying Google Maps Harvester in {current_city}...{RESET}")

                    maps_crawler.crawl_google_maps(

                        city=current_city,

                        country=country,

                        niche="Hotels",

                        max_places=needed_leads,

                        headless=True,

                        business_id=active_id

                    )

            else:

                print(f"  {C_GREEN}[1/4] Discovery buffer ready ({ready_ghs} fresh verified leads).{RESET}")



            # Step 2: Audit websites & extract verified contacts concurrently

            pending_count = len(db.get_pending_audits(business_id=active_id, limit=100))

            if pending_count > 0:

                print(f"  {C_CYAN}[2/4] Parallel website auditing & live MX email verification ({pending_count} pending)...{RESET}")

                audited = website_auditor.audit_pending_leads(limit=100, business_id=active_id)

                print(f"        {C_GREEN}✓ Extracted details from {len(audited)} properties{RESET}")



            # Step 3: Dispatch Emails if selected

            emails_sent_wave = 0

            if channel_mode in ["EMAIL", "BOTH"]:

                dispatch_desc = pool_label if not selected_prof_key else selected_prof_key

                ready_to_send = len(db.get_leads_ready_for_initial_email(business_id=active_id, limit=remaining_to_deliver))

                if ready_to_send > 0:

                    print(f"  {C_CYAN}[3/4] Dispatching official partner onboarding emails via {dispatch_desc}...{RESET}")

                    emails_sent_wave = email_engine.dispatch_initial_emails(limit=min(20, remaining_to_deliver), profile_name=selected_prof_key, business_id=active_id)

                    print(f"        {C_GREEN}✓ Successfully delivered {emails_sent_wave} onboarding emails{RESET}")

                else:

                    print(f"  {C_YELLOW}[3/4] 0 fresh deliverable emails available in buffer. Skipping dispatch to protect old database leads.{RESET}")



            # Step 4: Dispatch WhatsApp if selected

            wa_sent_wave = 0

            if channel_mode in ["WHATSAPP", "BOTH"]:

                if whatsapp_engine.is_whatsapp_logged_in():

                    print(f"  {C_CYAN}[3b/4] Dispatching WhatsApp onboarding outreach to mobile contacts...{RESET}")

                    wa_sent_wave = whatsapp_engine.dispatch_whatsapp_queue(limit=min(15, remaining_to_deliver), business_id=active_id, headless=True)

                    print(f"        {C_GREEN}✓ Successfully delivered {wa_sent_wave} WhatsApp messages{RESET}")

                else:

                    print(f"  {C_YELLOW}[!] WhatsApp Web is not linked. Run login_whatsapp.bat or Option [Q] to enable dual-channel.{RESET}")



            # Follow-ups (maintain 2-day sequence, or skip if operator requested Fresh Leads Only)

            if enable_followups:

                try:

                    email_engine.dispatch_followups(profile_name=selected_prof_key, business_id=active_id)

                except Exception:

                    pass

            else:

                print(f"  {C_DIM}[ℹ️ FOLLOW-UPS SKIPPED] Operator selected Fresh Pitches Only mode.{RESET}")



            # Update delivered count

            current_total = db.get_delivered_count(business_id=active_id, channel=channel_mode)

            delivered_in_mission = current_total - delivered_start

            remaining_to_deliver = max(0, target_goal - delivered_in_mission)

            pct = min(100.0, (delivered_in_mission / target_goal) * 100) if target_goal > 0 else 0



            print(f"\n  {C_WHITE}MISSION STATUS:{RESET} {C_GREEN}{delivered_in_mission} / {target_goal} DELIVERED{RESET} ({pct:.1f}%) │ {C_YELLOW}{remaining_to_deliver} remaining{RESET}")



            delivered_in_this_pass = (emails_sent_wave or 0) + (wa_sent_wave or 0)

            delivered_in_wave += delivered_in_this_pass

            if delivered_in_this_pass == 0:

                consecutive_zero_passes += 1

            else:

                consecutive_zero_passes = 0



            # Low-RAM memory collection after each pass

            import gc

            gc.collect()



            if delivered_in_mission >= target_goal:

                print(f"\n  {C_GREEN}🎉 MISSION ACCOMPLISHED! Successfully reached goal of {target_goal} DELIVERED outreaches!{RESET}\n")

                input("  Press Enter to return to main menu...")

                break



            # Anti-Stall Guard: If an area has 0 new leads delivered for 2 passes, rotate automatically!

            force_stagnation_rotate = False

            if consecutive_zero_passes >= 2 and delivered_in_wave < WAVE_GOAL:

                force_stagnation_rotate = True

                print(f"\n  {C_YELLOW}⚡ [DYNAMIC ANTI-STALL] Area '{current_city}' yielded 0 new verified deliveries in 2 consecutive passes.{RESET}")

                print(f"  {C_CYAN}Auto-advancing to next destination in rotation to prevent wave stalling!{RESET}")



            # Nationwide Rotation, Wave Goal Completion, or Stagnation Advance

            if is_nationwide or delivered_in_wave >= WAVE_GOAL or force_stagnation_rotate:

                if is_nationwide or force_stagnation_rotate:

                    next_dest = clean_destinations[cycle % len(clean_destinations)]

                    print(f"\n  {C_GREEN}✓ [SMART ROTATION]{RESET} Advancing from {current_city} to next destination: {C_YELLOW}{next_dest}{RESET} (Wave Cycle #{cycle+1})...")

                else:

                    print(f"\n  {C_GREEN}🎉 [✓ WAVE #{cycle} COMPLETED]{RESET} Fulfilled all {delivered_in_wave} verified deliveries for Wave #{cycle}!")

                cycle += 1

                delivered_in_wave = 0

                consecutive_zero_passes = 0

                cooldown = 15

            else:

                remaining_in_wave = WAVE_GOAL - delivered_in_wave

                print(f"\n  {C_CYAN}[WAVE #{cycle} IN PROGRESS]{RESET} {delivered_in_wave}/{WAVE_GOAL} Delivered ({remaining_in_wave} needed). Staying in Wave #{cycle}...")

                cooldown = 10 if delivered_in_this_pass > 0 else 20



            for sec in range(cooldown, 0, -5):

                m, s = divmod(sec, 60)

                sys.stdout.write(f"\r  {C_YELLOW}⏳ Next sweep in {m:02d}:{s:02d} — Wave #{cycle}: {delivered_in_wave}/{WAVE_GOAL} Delivered (Total: {delivered_in_mission}/{target_goal})...{RESET}   ")

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

    country = tgt.get("country") or "USA"

    city = tgt.get("city") or "Houston, TX"

    niche = tgt.get("niche") or "Commercial HVAC"



    print(f"\n{C_CYAN}╔═══════════════════════════════════════════════════════════════════════════════════════════════╗{RESET}")

    print(f"  {C_CYAN}║               🚀 ALORIA LABS CLIENT ACQUISITION & WEB MODERNIZATION ENGINE                    ║{RESET}")

    print(f"  {C_CYAN}║             Mission: High-Converting Web Modernization Discovery & Outreach                  ║{RESET}")

    print(f"  {C_CYAN}╚═══════════════════════════════════════════════════════════════════════════════════════════════╝{RESET}")

    print(f"  {C_WHITE}Target:{RESET}  {C_YELLOW}{niche}{RESET} in {C_CYAN}{city}, {country}{RESET}\n")



    # Ask how many people/leads to email

    try:

        quota_input = input(f"  {C_GREEN}Kitne logon ko email bhejna hai? (Target Goal, e.g. 25, 50, 100) [50]: {RESET}").strip()

        target_goal = int(quota_input) if quota_input.isdigit() and int(quota_input) > 0 else 50

    except (KeyboardInterrupt, EOFError):

        return



    # Ask execution mode: single wave vs continuous

    try:

        mode_choice = input(f"  {C_GREEN}Execution Mode: [1] Stop after {target_goal} emails  [2] 24/7 Continuous Loop [1]: {RESET}").strip()

        stop_on_goal = (mode_choice != "2")

        fu_choice = input(f"  {C_GREEN}Follow-up Strategy: [1] Pitches + Follow-ups  [2] Skip Follow-ups (Fresh Only) [1]: {RESET}").strip()

        enable_followups = (fu_choice != "2")

    except (KeyboardInterrupt, EOFError):

        return



    delivered_start = db.get_delivered_count(business_id=active_id, channel="EMAIL")



    print(f"\n  {C_GREEN}✓ MISSION CONFIRMED: Target goal of {target_goal} DELIVERED EMAILS.{RESET}")

    fu_label = "Active" if enable_followups else "DISABLED (Fresh Leads Only)"

    print(f"  {C_WHITE}Follow-ups:{RESET} {C_YELLOW}{fu_label}{RESET}")

    if stop_on_goal:

        print(f"  {C_DIM}Engine will stop and return to menu once {target_goal} emails are delivered.{RESET}")

    else:

        print(f"  {C_DIM}Mode: 24/7 continuous autonomous execution. Press Ctrl+C anytime to pause.{RESET}")

    print(f"  {C_DIM}Press Ctrl+C anytime to pause/return to menu.{RESET}\n")

    time.sleep(1)



    cycle = 1

    delivered_in_wave = 0

    WAVE_GOAL = 50

    while True:

        # Check progress towards goal

        current_total = db.get_delivered_count(business_id=active_id, channel="EMAIL")

        delivered_in_mission = current_total - delivered_start

        remaining_to_deliver = max(0, target_goal - delivered_in_mission)



        if delivered_in_mission >= target_goal and stop_on_goal:

            print(f"\n{C_GREEN}╔═══════════════════════════════════════════════════════════════════════════════════════════════╗{RESET}")

            print(f"  {C_GREEN}║     🎉 MISSION ACCOMPLISHED: Successfully delivered {delivered_in_mission} emails to {niche} in {city}! ║{RESET}")

            print(f"  {C_GREEN}╚═══════════════════════════════════════════════════════════════════════════════════════════════╝{RESET}\n")

            input("  Press Enter to return to main menu...")

            break



        pct = min(100.0, (delivered_in_mission / target_goal) * 100) if target_goal > 0 else 0

        print(f"\n{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")

        print(f"  {C_WHITE}► [WAVE #{cycle}] CLIENT DISCOVERY WAVE: {C_GREEN}{niche.upper()} IN {city.upper()}, {country.upper()}{RESET}")

        print(f"  {C_YELLOW}PROGRESS: [ {delivered_in_mission} / {target_goal} DELIVERED ] ({pct:.1f}%) │ Remaining Needed: {remaining_to_deliver}{RESET}")

        print(f"{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}")

        # Check if Aloria today's email quota is already reached

        aloria_swarm = db.get_swarm_daily_stats("aloria_labs")

        working_accs = [a for a in aloria_swarm["accounts"] if a["key"] not in getattr(email_engine, "_FAILED_AUTH_PROFILES", set())]

        all_quota_done = all(a["quota_reached"] for a in working_accs) if working_accs else True

        if all_quota_done:

            tot_done = sum(a["delivered_today"] for a in working_accs)

            quota_per_acc = config.get_max_delivered_quota("aloria_labs")

            print(f"\n{C_CYAN}  ╔═══════════════════════════════════════════════════════════════════════════════════════╗{RESET}")

            print(f"  {C_GREEN}║             ⭐ AAJ KA DAILY EMAIL OUTREACH QUOTA COMPLETE HO GAYA!                     ║{RESET}")

            print(f"  {C_CYAN}╠═══════════════════════════════════════════════════════════════════════════════════════╣{RESET}")

            print(f"  {C_WHITE}║  Boss, Aloria Labs se aaj ka {quota_per_acc}-email quota ({tot_done} delivered) poora ho chuka hai!    ║{RESET}")

            print(f"  {C_YELLOW}║  Ab agle din raat 12:00 baje ke baad (new calendar day) fresh hunt try karein.        ║{RESET}")

            print(f"  {C_CYAN}╚═══════════════════════════════════════════════════════════════════════════════════════╝{RESET}\n")

            input("  Press Enter to return to main menu...")

            break



        try:

            # Step 0: Priority Overdue Follow-up Catch-up (Offline Downtime Awareness)

            if enable_followups:

                try:

                    overdue = db.get_overdue_followups(business_id=active_id, interval_days=getattr(config, "FOLLOW_UP_INTERVAL_DAYS", 3))

                    if overdue:

                        print(f"  {C_YELLOW}[0/4] ⚡ PRIORITY PROTOCOL: Found {len(overdue)} overdue follow-up leads (Laptop was offline). Dispatching now...{RESET}")

                        email_engine.dispatch_followups(profile_name="gmail", business_id=active_id)

                except Exception:

                    pass

            else:

                print(f"  {C_DIM}[0/4] ⚡ Follow-ups SKIPPED (Fresh Initial Pitches Only mode active).{RESET}")



            # 1. Google Maps Lead Discovery (Clicks place cards, captures real websites)

            ready_in_db = len(db.get_leads_ready_for_initial_email(business_id=active_id, limit=50, country=country, niche=niche))

            if ready_in_db < remaining_to_deliver:

                needed_leads = max(30, min(100, remaining_to_deliver * 3))

                print(f"  {C_CYAN}[1/4] Discovery buffer needs fresh leads ({ready_in_db} ready). Deploying Google Maps Harvester in {city}...{RESET}")

                maps_crawler.crawl_google_maps(

                    city=city,

                    country=country,

                    niche=niche,

                    max_places=needed_leads,

                    headless=True,

                    business_id=active_id

                )

            else:

                print(f"  {C_GREEN}[1/4] Discovery buffer ready ({ready_in_db} fresh verified leads).{RESET}")



            # 2. Parallel Audit & Contact Extraction

            pending_count = len(db.get_pending_audits(business_id=active_id, limit=50))

            if pending_count > 0:

                print(f"  {C_CYAN}[2/4] Concurrently auditing websites & performing live MX verification ({pending_count} pending)...{RESET}")

                website_auditor.audit_pending_leads(limit=100, business_id=active_id)



            # 3. Dispatch Initial Pitches

            active_b = business_manager.get_business(active_id)

            selected_prof = (active_b.get("sender_profile") if active_b else None) or "gmail"

            aloria_cfg = config.get_smtp_config(selected_prof)

            aloria_email_disp = aloria_cfg.get("email", "alorialabs@gmail.com")

            batch_to_send = min(20, remaining_to_deliver)

            ready_to_send = len(db.get_leads_ready_for_initial_email(business_id=active_id, limit=batch_to_send, country=country, niche=niche))

            sent = 0

            if ready_to_send > 0:

                print(f"  {C_CYAN}[3/4] Dispatching tailored pitches via {aloria_email_disp} (Limit: {batch_to_send})...{RESET}")

                sent = email_engine.dispatch_initial_emails(limit=batch_to_send, profile_name=selected_prof, business_id=active_id, country=country, niche=niche)

                print(f"        {C_GREEN}✓ Dispatched {sent} tailored pitches{RESET}")

            else:

                print(f"  {C_YELLOW}[3/4] 0 fresh deliverable emails in buffer. Skipping dispatch to protect old database leads.{RESET}")



            # 4. Dispatch Follow-ups

            if enable_followups:

                print(f"  {C_CYAN}[4/4] Dispatching scheduled follow-ups via {aloria_email_disp}...{RESET}")

                fu_sent = email_engine.dispatch_followups(profile_name=selected_prof, business_id=active_id)

                print(f"        {C_GREEN}✓ Dispatched {fu_sent} follow-ups{RESET}")

            else:

                print(f"  {C_DIM}[4/4] ⚡ Follow-ups SKIPPED (Fresh Initial Pitches Only mode active).{RESET}")



            # Update delivered count after wave

            current_total = db.get_delivered_count(business_id=active_id, channel="EMAIL")

            delivered_in_mission = current_total - delivered_start

            remaining_to_deliver = max(0, target_goal - delivered_in_mission)



            delivered_in_wave += (sent or 0)



            # Low-RAM memory collection after each pass

            import gc

            gc.collect()



            if delivered_in_mission >= target_goal and stop_on_goal:

                print(f"\n{C_GREEN}╔═══════════════════════════════════════════════════════════════════════════════════════════════╗{RESET}")

                print(f"  {C_GREEN}║     🎉 MISSION ACCOMPLISHED: Successfully delivered {delivered_in_mission} emails to {niche} in {city}! ║{RESET}")

                print(f"  {C_GREEN}╚═══════════════════════════════════════════════════════════════════════════════════════════════╝{RESET}\n")

                input("  Press Enter to return to main menu...")

                break



            # STRICT 50-DELIVERED-EMAILS-PER-WAVE RULE:

            # Do NOT advance to the next wave until the current wave hits 50 delivered emails!

            if delivered_in_wave >= WAVE_GOAL:

                print(f"\n  {C_GREEN}🎉 [✓ WAVE #{cycle} COMPLETED]{RESET} Fulfilled all {delivered_in_wave} verified deliveries for Wave #{cycle}!")

                cycle += 1

                delivered_in_wave = 0

                cooldown = 20

                print(f"  {C_DIM}Wave #{cycle-1} complete. Continuous pacing active ({cooldown}s). Next wave starts automatically...{RESET}")

            else:

                remaining_in_wave = WAVE_GOAL - delivered_in_wave

                print(f"\n  {C_CYAN}[WAVE #{cycle} IN PROGRESS]{RESET} {delivered_in_wave}/{WAVE_GOAL} Delivered in Wave #{cycle} ({remaining_in_wave} needed). Staying in Wave #{cycle} to sweep next partition...")

                cooldown = 12 if sent > 0 else 25



            for sec in range(cooldown, 0, -5):

                m, s = divmod(sec, 60)

                sys.stdout.write(f"\r  {C_YELLOW}⏳ Next sweep in {m:02d}:{s:02d} — Wave #{cycle}: {delivered_in_wave}/{WAVE_GOAL} Delivered (Total: {delivered_in_mission}/{target_goal})...{RESET}   ")

                sys.stdout.flush()

                time.sleep(5)

            print()



        except KeyboardInterrupt:

            print(f"\n\n  {C_YELLOW}[!] Client acquisition engine paused by operator. Delivered: {delivered_in_mission} / {target_goal} emails.{RESET}\n")

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



        # [L] Ledger - Opens in a dedicated pop-up terminal window

        if choice == "l":

            print(f"\n  {C_CYAN}[↗] Opening Pipeline & Ledger in a new popup terminal window...{RESET}")

            script_path = BASE_DIR / "terminal_cockpit.py"

            cmd = f'start "Pipeline & Ledger — {active_id.upper()}" cmd /c "{sys.executable}" "{script_path}" --ledger {active_id}'

            try:

                subprocess.Popen(cmd, shell=True, cwd=str(script_path.parent))

            except Exception:

                show_clean_lead_ledger(active_id)

            time.sleep(0.8)

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



        # [H] Direct Lead Hunt (1-Browser 10-Tabs Swarm)

        if choice == "h":

            handle_direct_hunt(active_id)

            continue



        # [F] Priority Overdue Follow-ups

        if choice == "f":

            handle_priority_followups(active_id)

            continue



        # [A] AI Autonomous Closer Engine
        if choice == "a":
            import ai_closer_engine
            ai_closer_engine.process_and_close_inbound_threads(dry_run=False, limit=35)
            input("\n  Press Enter to return to menu...")
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

    if len(sys.argv) > 2 and sys.argv[1] == "--ledger":

        show_clean_lead_ledger(sys.argv[2])

        sys.exit(0)

    run_cockpit_loop()

