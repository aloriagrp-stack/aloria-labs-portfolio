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

def configure_target_remote(b_id, send, recv_line):
    b = business_manager.get_business(b_id)
    b_name = b.get("name", b_id) if b else b_id
    tgt = business_manager.get_target_settings(b_id)
    old_c = tgt.get("country", "")
    old_ci = tgt.get("city", "")
    old_ni = tgt.get("niche", "")

    send(f"\n{C_CYAN}─── [CONFIGURE TARGET FOR {b_name.upper()}] ───{RESET}\n")
    send(f"{C_DIM}Enter target country, city & niche. You choose everything.{RESET}\n")

    hint_c = f" [{old_c}]" if old_c else ""
    send(f"{C_WHITE}Target Country (e.g. India, USA, UAE){hint_c}: {RESET}")
    c_in = recv_line()
    c = c_in.strip() if c_in and c_in.strip() else old_c

    hint_ci = f" [{old_ci}]" if old_ci else ""
    send(f"{C_WHITE}Target City (e.g. Mumbai, Dubai, London){hint_ci}: {RESET}")
    ci_in = recv_line()
    ci = ci_in.strip() if ci_in and ci_in.strip() else old_ci

    def_niche = old_ni or ("Hotels" if b_id == "gethotelstays" else "Restaurants")
    send(f"{C_WHITE}Target Niche / Industry [{def_niche}]: {RESET}")
    ni_in = recv_line()
    ni = ni_in.strip() if ni_in and ni_in.strip() else def_niche

    business_manager.set_target_settings(b_id, country=c, city=ci, niche=ni)
    send(f"\n{C_GREEN}[✓] Target saved: {ni} in {ci}, {c}!{RESET}\n")
    time.sleep(1)
    return c, ci, ni

def get_or_prompt_target_remote(b_id, send, recv_line):
    tgt = business_manager.get_target_settings(b_id)
    c = tgt.get("country", "")
    ci = tgt.get("city", "")
    ni = tgt.get("niche", "")
    if not c or not ci:
        return configure_target_remote(b_id, send, recv_line)
    return c, ci, ni

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
            sender = active_b.get("sender_display_name", "Default")

            tgt = business_manager.get_target_settings(active_id)
            tgt_country = tgt.get("country")
            tgt_city = tgt.get("city")
            tgt_niche = tgt.get("niche")
            loc_str = f"{tgt_city}, {tgt_country}" if (tgt_country and tgt_city) else "[Not Set - Press T]"
            niche_str = tgt_niche or "[Not Set - Press T]"

            # Render Screen to Termux
            screen = BANNER + f"""
{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}
  {C_WHITE}ACTIVE BUSINESS:{RESET}   {C_MAGENTA}[ {b_name.upper()} ]{RESET}  {C_DIM}(Press 1-{len(businesses)} to switch profile){RESET}
  {C_WHITE}TARGET REGION:{RESET}     {C_GREEN}{loc_str}{RESET}
  {C_WHITE}TARGET NICHE:{RESET}      {C_YELLOW}{niche_str}{RESET}
  {C_WHITE}SENDER ACCOUNT:{RESET}    {C_CYAN}{sender}{RESET}
  {C_WHITE}PIPELINE STATS:{RESET}    {C_GREEN}{total}{RESET} Leads │ {C_BLUE}{audited}{RESET} Audited │ {C_YELLOW}{pitched}{RESET} Pitched │ {C_MAGENTA}{golden}{RESET} Golden No-Web │ {C_CYAN}{sent_total}{RESET} Sent
{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}

  {C_YELLOW}─── [SWITCH BUSINESS PROFILE] ─────────────────────────────────────────────────────────────{RESET}
"""
            keys = list(businesses.keys())
            for idx, b_id in enumerate(keys, 1):
                b = businesses[b_id]
                b_tgt = business_manager.get_target_settings(b_id)
                t_loc = f"{b_tgt.get('city')}, {b_tgt.get('country')}" if b_tgt.get('country') else "Location Not Set"
                t_nic = b_tgt.get('niche') or "Niche Not Set"
                if b_id == active_id:
                    tag = f"{C_GREEN}● [ACTIVE]{RESET}"
                    name_str = f"{C_GREEN}{b.get('name', b_id)}{RESET}"
                else:
                    tag = f"{C_DIM}○ [STANDBY]{RESET}"
                    name_str = f"{C_WHITE}{b.get('name', b_id)}{RESET}"
                screen += f"  {C_YELLOW}[{idx}]{RESET} {tag} {name_str} {C_DIM}— {t_nic} ({t_loc}){RESET}\n"

            screen += f"""
  {C_CYAN}─── [TERMUX MOBILE OPERATIONS] ────────────────────────────────────────────────────────────{RESET}
  {C_WHITE}[T]{RESET} {C_CYAN}⚙ Set Country / City / Niche{RESET} {C_DIM}— Choose target location & industry manually{RESET}
  {C_WHITE}[H]{RESET} {C_GREEN}● Live Hunter{RESET}            {C_DIM}— Scrape Google Maps on laptop (Visible or headless){RESET}
  {C_WHITE}[S]{RESET} {C_CYAN}● Silent Ghost Hunter{RESET}    {C_DIM}— Scrape Google Maps in background (Headless){RESET}
  {C_WHITE}[D]{RESET} {C_YELLOW}● Safe Dry-Run{RESET}           {C_DIM}— Scrape & audit leads without sending emails{RESET}
  {C_WHITE}[A]{RESET} {C_BLUE}● Run Website Auditor{RESET}    {C_DIM}— Inspect website speeds, SSL & extract emails{RESET}
  {C_WHITE}[E]{RESET} {C_MAGENTA}● Dispatch Email Queue{RESET}   {C_DIM}— Send tailored Day 0 cold pitches for active business{RESET}
  {C_WHITE}[F]{RESET} {C_YELLOW}● Dispatch Follow-ups{RESET}    {C_DIM}— Send scheduled 2-Day & 4-Day follow-up sequence{RESET}
  {C_WHITE}[R]{RESET} {C_GREEN}● Full Autopilot Wave{RESET}    {C_DIM}— 1-Click Hunt ➔ Audit ➔ Pitch ➔ Follow-up cycle (Active){RESET}
  {C_WHITE}[B]{RESET} {C_GREEN}⚡ Dual Parallel Wave{RESET}    {C_DIM}— Run Aloria Labs AND GetHotelStays in parallel!{RESET}
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

            # Configure Target
            if choice == "t":
                configure_target_remote(active_id, send, recv_line)
                continue

            if choice == "h":
                c, ci, ni = get_or_prompt_target_remote(active_id, send, recv_line)
                send(f"\n{C_CYAN}[► LAUNCHING MAPS HUNTER ON LAPTOP]{RESET}\n")
                send(f"Target: {ni} in {ci}, {c} for {b_name}\n")
                try:
                    maps_crawler.crawl_google_maps(city=ci, country=c, niche=ni, max_places=5, headless=False, business_id=active_id)
                    send(f"\n{C_GREEN}[✓] Hunt wave completed on laptop!{RESET}\n")
                except Exception as e:
                    send(f"\n{C_RED}[!] Crawl error: {e}{RESET}\n")
                send("Press Enter to return to menu...")
                recv_line()

            elif choice == "s":
                c, ci, ni = get_or_prompt_target_remote(active_id, send, recv_line)
                send(f"\n{C_CYAN}[► LAUNCHING SILENT MAPS HUNTER]{RESET}\n")
                send(f"Target: {ni} in {ci}, {c} for {b_name}\n")
                try:
                    maps_crawler.crawl_google_maps(city=ci, country=c, niche=ni, max_places=5, headless=True, business_id=active_id)
                    send(f"\n{C_GREEN}[✓] Silent hunt completed!{RESET}\n")
                except Exception as e:
                    send(f"\n{C_RED}[!] Crawl error: {e}{RESET}\n")
                send("Press Enter to return to menu...")
                recv_line()

            elif choice == "d":
                c, ci, ni = get_or_prompt_target_remote(active_id, send, recv_line)
                send(f"\n{C_YELLOW}[► RUNNING SAFE DRY-RUN (NO EMAILS)]{RESET}\n")
                send(f"Target: {ni} in {ci}, {c}\n")
                try:
                    maps_crawler.crawl_google_maps(city=ci, country=c, niche=ni, max_places=3, headless=True, business_id=active_id)
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
                c, ci, ni = get_or_prompt_target_remote(active_id, send, recv_line)
                send(f"\n{C_MAGENTA}[► RUNNING FULL AUTONOMOUS WAVE ON LAPTOP]{RESET}\n")
                send(f"Target: {ni} in {ci}, {c} for {b_name}\n")
                try:
                    maps_crawler.crawl_google_maps(city=ci, country=c, niche=ni, max_places=5, headless=True, business_id=active_id)
                    website_auditor.audit_pending_leads(limit=5, business_id=active_id)
                    email_engine.dispatch_initial_emails(limit=5, profile_name=active_b.get("sender_profile", "gmail"), business_id=active_id)
                    email_engine.dispatch_followups(profile_name=active_b.get("sender_profile", "gmail"), business_id=active_id)
                    send(f"\n{C_GREEN}[✓] Full autonomous wave complete!{RESET}\n")
                except Exception as e:
                    send(f"\n{C_RED}[!] Error: {e}{RESET}\n")
                send("Press Enter to return to menu...")
                recv_line()

            elif choice == "b":
                send(f"\n{C_MAGENTA}╔═══════════════════════════════════════════════════════════════════════╗{RESET}\n")
                send(f"  {C_MAGENTA}║       ⚡ LAUNCHING DUAL PARALLEL AGENTS (MULTI-THREADED)             ║{RESET}\n")
                send(f"  {C_MAGENTA}╚═══════════════════════════════════════════════════════════════════════╝{RESET}\n")

                c1, ci1, ni1 = get_or_prompt_target_remote("aloria_labs", send, recv_line)
                c2, ci2, ni2 = get_or_prompt_target_remote("gethotelstays", send, recv_line)

                send(f"  {C_GREEN}[THREAD 1]{RESET} {C_WHITE}Agent Aloria Labs:{RESET} {ni1} in {ci1}, {c1}\n")
                send(f"  {C_GREEN}[THREAD 2]{RESET} {C_WHITE}Agent GetHotelStays:{RESET} {ni2} in {ci2}, {c2}\n")
                send(f"  {C_DIM}Running both parallel background threads concurrently on laptop...{RESET}\n\n")

                import threading

                def run_aloria_sub():
                    try:
                        b = business_manager.get_business("aloria_labs")
                        sp = b.get("sender_profile", "gmail") if b else "gmail"
                        maps_crawler.crawl_google_maps(city=ci1, country=c1, niche=ni1, max_places=5, headless=True, business_id="aloria_labs")
                        website_auditor.audit_pending_leads(limit=5, business_id="aloria_labs")
                        email_engine.dispatch_initial_emails(limit=5, profile_name=sp, business_id="aloria_labs")
                        email_engine.dispatch_followups(profile_name=sp, business_id="aloria_labs")
                        send(f"\n  {C_GREEN}[✓ AGENT ALORIA]{RESET} Wave finished!\n")
                    except Exception as err:
                        send(f"\n  {C_RED}[!] Aloria err: {err}{RESET}\n")

                def run_hotels_sub():
                    try:
                        b = business_manager.get_business("gethotelstays")
                        sp = b.get("sender_profile", "gmail") if b else "gmail"
                        maps_crawler.crawl_google_maps(city=ci2, country=c2, niche=ni2, max_places=5, headless=True, business_id="gethotelstays")
                        website_auditor.audit_pending_leads(limit=5, business_id="gethotelstays")
                        email_engine.dispatch_initial_emails(limit=5, profile_name=sp, business_id="gethotelstays")
                        email_engine.dispatch_followups(profile_name=sp, business_id="gethotelstays")
                        send(f"\n  {C_GREEN}[✓ AGENT HOTELSTAYS]{RESET} Wave finished!\n")
                    except Exception as err:
                        send(f"\n  {C_RED}[!] HotelStays err: {err}{RESET}\n")

                th1 = threading.Thread(target=run_aloria_sub)
                th2 = threading.Thread(target=run_hotels_sub)
                th1.start()
                th2.start()
                th1.join()
                th2.join()

                send(f"\n{C_CYAN}[✓ DUAL PARALLEL WAVE COMPLETED FOR BOTH BUSINESSES!]{RESET}\n")
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
