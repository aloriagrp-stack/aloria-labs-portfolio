import os
import sys
import socket
import threading
import time
from pathlib import Path

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import db
import business_manager
import maps_crawler
import website_auditor
import email_engine

# ANSI Escape Sequences for Mobile Termux
C_CYAN = "\033[1;36m"
C_GREEN = "\033[1;32m"
C_RED = "\033[1;31m"
C_YELLOW = "\033[1;33m"
C_MAGENTA = "\033[1;35m"
C_BLUE = "\033[1;34m"
C_WHITE = "\033[1;37m"
C_DIM = "\033[2m"
RESET = "\033[0m"
CLEAR = "\033[2J\033[H"

BANNER = f"""{CLEAR}
{C_CYAN}  █████╗ ██╗      ██████╗ ██████╗ ██╗ █████╗     ██╗  ██╗██╗   ██╗███╗   ██╗████████╗███████╗██████╗ 
{C_CYAN} ██╔══██╗██║     ██╔═══██╗██╔══██╗██║██╔══██╗    ██║  ██║██║   ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗
{C_BLUE} ███████║██║     ██║   ██║██████╔╝██║███████║    ███████║██║   ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝
{C_BLUE} ██╔══██║██║     ██║   ██║██╔══██╗██║██╔══██║    ██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗
{C_MAGENTA} ██║  ██║███████╗╚██████╔╝██║  ██║██║██║  ██║    ██║  ██║╚██████╔╝██║ ╚████║   ██║   ███████╗██║  ██║
{C_MAGENTA} ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
{C_WHITE}                       [ MOBILE TERMUX COMMAND TERMINAL • LAPTOP ENGINE ]
{C_DIM}                 Multi-Business Automation System • 100% Deterministic • Aloria Labs{RESET}
"""

def handle_client(client_sock, client_addr):
    try:
        def send(msg):
            client_sock.sendall(msg.encode("utf-8", errors="ignore"))

        def recv_line():
            buf = ""
            while True:
                data = client_sock.recv(1024).decode("utf-8", errors="ignore")
                if not data:
                    return None
                buf += data
                if "\n" in buf or "\r" in buf:
                    return buf.strip()

        while True:
            active_id = business_manager.get_active_business_id()
            active_b = business_manager.get_active_business()
            businesses, _ = business_manager.list_businesses()
            stats = db.get_funnel_stats(business_id=active_id)

            total = stats.get("total", 0)
            audited = stats.get("audited", 0)
            pitched = stats.get("pitch_sent", 0)
            golden = stats.get("golden_leads", 0)
            sent_total = stats.get("emails_sent", 0)

            b_name = active_b.get("name", active_id)
            country = active_b.get("country", "Algeria")
            cities = active_b.get("cities", ["Algiers"])
            niches = active_b.get("default_niches", ["Restaurants"])
            sender = active_b.get("sender_display_name", "Default")

            # Render Screen to Termux
            screen = BANNER + f"""
{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}
  {C_WHITE}ACTIVE BUSINESS:{RESET}   {C_MAGENTA}[ {b_name.upper()} ]{RESET}  {C_DIM}(Press 1-{len(businesses)} to switch profile){RESET}
  {C_WHITE}TARGET SECTOR:{RESET}     {C_YELLOW}{niches[0] if niches else 'N/A'}{RESET} in {C_GREEN}{cities[0] if cities else 'N/A'}, {country}{RESET}
  {C_WHITE}SENDER ACCOUNT:{RESET}    {C_CYAN}{sender}{RESET}
  {C_WHITE}PIPELINE STATS:{RESET}    {C_GREEN}{total}{RESET} Leads │ {C_BLUE}{audited}{RESET} Audited │ {C_YELLOW}{pitched}{RESET} Pitched │ {C_MAGENTA}{golden}{RESET} Golden No-Web │ {C_CYAN}{sent_total}{RESET} Sent
{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}

  {C_YELLOW}─── [SWITCH BUSINESS PROFILE] ─────────────────────────────────────────────────────────────{RESET}
"""
            keys = list(businesses.keys())
            for idx, b_id in enumerate(keys, 1):
                b = businesses[b_id]
                if b_id == active_id:
                    tag = f"{C_GREEN}● [ACTIVE]{RESET}"
                    name_str = f"{C_GREEN}{b.get('name', b_id)}{RESET}"
                else:
                    tag = f"{C_DIM}○ [STANDBY]{RESET}"
                    name_str = f"{C_WHITE}{b.get('name', b_id)}{RESET}"
                screen += f"  {C_YELLOW}[{idx}]{RESET} {tag} {name_str} {C_DIM}— {b.get('niche', '')} ({b.get('country', '')}){RESET}\n"

            screen += f"""
  {C_CYAN}─── [TERMUX MOBILE OPERATIONS] ────────────────────────────────────────────────────────────{RESET}
  {C_WHITE}[H]{RESET} {C_GREEN}● Live Hunter{RESET}            {C_DIM}— Scrape Google Maps on laptop (Visible or headless){RESET}
  {C_WHITE}[S]{RESET} {C_CYAN}● Silent Ghost Hunter{RESET}    {C_DIM}— Scrape Google Maps in background (Headless){RESET}
  {C_WHITE}[D]{RESET} {C_YELLOW}● Safe Dry-Run{RESET}           {C_DIM}— Scrape & audit leads without sending emails{RESET}
  {C_WHITE}[A]{RESET} {C_BLUE}● Run Website Auditor{RESET}    {C_DIM}— Inspect website speeds, SSL & extract emails{RESET}
  {C_WHITE}[E]{RESET} {C_MAGENTA}● Dispatch Email Queue{RESET}   {C_DIM}— Send tailored Day 0 cold pitches for active business{RESET}
  {C_WHITE}[F]{RESET} {C_YELLOW}● Dispatch Follow-ups{RESET}    {C_DIM}— Send scheduled 2-Day & 4-Day follow-up sequence{RESET}
  {C_WHITE}[R]{RESET} {C_GREEN}● Full Autopilot Wave{RESET}    {C_DIM}— 1-Click Hunt ➔ Audit ➔ Pitch ➔ Follow-up cycle{RESET}
  {C_WHITE}[L]{RESET} {C_CYAN}● Lead Ledger & History{RESET}  {C_DIM}— View all leads, email contacts & outreach status{RESET}
  {C_WHITE}[0]{RESET} {C_RED}● Disconnect{RESET}             {C_DIM}— Close connection to laptop{RESET}

  {C_GREEN}Enter command in Termux: {RESET}"""

            send(screen)
            choice = recv_line()
            if choice is None or choice in ["0", "q", "exit"]:
                send(f"\n{C_CYAN}Termux session closed. Goodbye!{RESET}\n")
                break

            choice = choice.lower()

            # Switch Business
            if choice.isdigit() and 1 <= int(choice) <= len(businesses):
                chosen_id = keys[int(choice) - 1]
                business_manager.set_active_business(chosen_id)
                send(f"\n{C_GREEN}[✓] Switched active business to: {businesses[chosen_id].get('name')}{RESET}\n")
                time.sleep(1)
                continue

            city = cities[0] if cities else "Algiers"
            niche = niches[0] if niches else "Restaurants"

            if choice == "h":
                send(f"\n{C_CYAN}[► LAUNCHING MAPS HUNTER ON LAPTOP]{RESET}\n")
                send(f"Target: {niche} in {city}, {country} for {b_name}\n")
                try:
                    maps_crawler.crawl_google_maps(city=city, country=country, niche=niche, max_places=5, headless=False, business_id=active_id)
                    send(f"\n{C_GREEN}[✓] Hunt wave completed on laptop!{RESET}\n")
                except Exception as e:
                    send(f"\n{C_RED}[!] Crawl error: {e}{RESET}\n")
                send("Press Enter to return to menu...")
                recv_line()

            elif choice == "s":
                send(f"\n{C_CYAN}[► LAUNCHING SILENT MAPS HUNTER]{RESET}\n")
                try:
                    maps_crawler.crawl_google_maps(city=city, country=country, niche=niche, max_places=5, headless=True, business_id=active_id)
                    send(f"\n{C_GREEN}[✓] Silent hunt completed!{RESET}\n")
                except Exception as e:
                    send(f"\n{C_RED}[!] Crawl error: {e}{RESET}\n")
                send("Press Enter to return to menu...")
                recv_line()

            elif choice == "d":
                send(f"\n{C_YELLOW}[► RUNNING SAFE DRY-RUN (NO EMAILS)]{RESET}\n")
                try:
                    maps_crawler.crawl_google_maps(city=city, country=country, niche=niche, max_places=3, headless=True, business_id=active_id)
                    website_auditor.audit_pending_leads(limit=3, business_id=active_id)
                    send(f"\n{C_GREEN}[✓] Dry run completed!{RESET}\n")
                except Exception as e:
                    send(f"\n{C_RED}[!] Error: {e}{RESET}\n")
                send("Press Enter to return to menu...")
                recv_line()

            elif choice == "a":
                send(f"\n{C_BLUE}[► RUNNING WEBSITE AUDITOR]{RESET}\n")
                try:
                    res = website_auditor.audit_pending_leads(limit=10, business_id=active_id)
                    send(f"\n{C_GREEN}[✓] Audited {len(res)} candidate sites!{RESET}\n")
                except Exception as e:
                    send(f"\n{C_RED}[!] Auditor error: {e}{RESET}\n")
                send("Press Enter to return to menu...")
                recv_line()

            elif choice == "e":
                send(f"\n{C_MAGENTA}[► DISPATCHING EMAIL QUEUE]{RESET}\n")
                try:
                    sent = email_engine.dispatch_initial_emails(limit=5, profile_name=active_b.get("sender_profile", "gmail"), business_id=active_id)
                    send(f"\n{C_GREEN}[✓] Dispatched {sent} emails!{RESET}\n")
                except Exception as e:
                    send(f"\n{C_RED}[!] Dispatch error: {e}{RESET}\n")
                send("Press Enter to return to menu...")
                recv_line()

            elif choice == "f":
                send(f"\n{C_YELLOW}[► DISPATCHING SCHEDULED FOLLOW-UPS]{RESET}\n")
                try:
                    sent = email_engine.dispatch_followups(profile_name=active_b.get("sender_profile", "gmail"), business_id=active_id)
                    send(f"\n{C_GREEN}[✓] Dispatched {sent} follow-ups!{RESET}\n")
                except Exception as e:
                    send(f"\n{C_RED}[!] Follow-up error: {e}{RESET}\n")
                send("Press Enter to return to menu...")
                recv_line()

            elif choice == "r":
                send(f"\n{C_MAGENTA}[► RUNNING FULL AUTONOMOUS WAVE ON LAPTOP]{RESET}\n")
                try:
                    maps_crawler.crawl_google_maps(city=city, country=country, niche=niche, max_places=5, headless=True, business_id=active_id)
                    website_auditor.audit_pending_leads(limit=5, business_id=active_id)
                    email_engine.dispatch_initial_emails(limit=5, profile_name=active_b.get("sender_profile", "gmail"), business_id=active_id)
                    email_engine.dispatch_followups(profile_name=active_b.get("sender_profile", "gmail"), business_id=active_id)
                    send(f"\n{C_GREEN}[✓] Full autonomous wave complete!{RESET}\n")
                except Exception as e:
                    send(f"\n{C_RED}[!] Error: {e}{RESET}\n")
                send("Press Enter to return to menu...")
                recv_line()

            elif choice == "l":
                leads = db.get_lead_ledger(business_id=active_id, limit=30)
                send(f"\n{C_CYAN}═══════════════════════════════════════════════════════════════════════{RESET}\n")
                send(f"  {C_WHITE}LEAD LEDGER FOR {C_YELLOW}{b_name.upper()}{RESET} ({len(leads)} leads)\n")
                send(f"{C_CYAN}═══════════════════════════════════════════════════════════════════════{RESET}\n")
                for l in leads:
                    n = l['business_name'][:22]
                    em = (l['email'] or 'No Email')[:24]
                    st = l['status']
                    pres = "NO-WEB" if not l['has_website'] else "WEB"
                    send(f"  {n:<22} [{pres:<6}] {em:<24} {st}\n")
                send(f"{C_CYAN}═══════════════════════════════════════════════════════════════════════{RESET}\n")
                send("Press Enter to return to menu...")
                recv_line()

    except Exception:
        pass
    finally:
        client_sock.close()

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def start_server(port=9000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", port))
    server.listen(5)

    ip = get_local_ip()
    print(f"\n{C_GREEN}🏹 [MOBILE TERMUX TERMINAL SERVER ONLINE]{RESET}")
    print(f"  {C_WHITE}Port:{RESET} 9000 (Pure TCP Terminal Protocol - Zero Browser)")
    print(f"  {C_CYAN}Connect from your Mobile Phone via Termux:{RESET}")
    print(f"    {C_YELLOW}nc {ip} {port}{RESET}   (or {C_YELLOW}telnet {ip} {port}{RESET})\n")

    while True:
        client, addr = server.accept()
        t = threading.Thread(target=handle_client, args=(client, addr), daemon=True)
        t.start()

if __name__ == "__main__":
    start_server()
