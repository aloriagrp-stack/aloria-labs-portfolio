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
    old_c = tgt.get("country", "India")
    old_ci = tgt.get("city", "Goa" if b_id == "gethotelstays" else "Mumbai")
    old_ni = tgt.get("niche", "Hotels" if b_id == "gethotelstays" else "Restaurants")

    send(f"\n{C_CYAN}─── [CONFIGURE TARGET FOR {b_name.upper()}] ───{RESET}\n")
    send(f"{C_WHITE}Target Country [{old_c}]: {RESET}")
    c_in = recv_line()
    c = c_in.strip() if c_in and c_in.strip() else old_c

    send(f"{C_WHITE}Target City (e.g. Goa, Jaipur, Manali) [{old_ci}]: {RESET}")
    ci_in = recv_line()
    ci = ci_in.strip() if ci_in and ci_in.strip() else old_ci

    send(f"{C_WHITE}Target Niche [{old_ni}]: {RESET}")
    ni_in = recv_line()
    ni = ni_in.strip() if ni_in and ni_in.strip() else old_ni

    business_manager.set_target_settings(b_id, country=c, city=ci, niche=ni)
    send(f"\n{C_GREEN}[✓] Target saved: {ni} in {ci}, {c}!{RESET}\n")
    time.sleep(1)
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
            stats = db.get_funnel_stats(business_id=active_id)

            total = stats.get("total", 0)
            audited = stats.get("audited", 0)
            pitched = stats.get("pitch_sent", 0)
            sent_total = stats.get("emails_sent", 0)

            tgt = business_manager.get_target_settings(active_id)
            tgt_country = tgt.get("country") or "India"
            tgt_city = tgt.get("city") or ("Goa" if active_id == "gethotelstays" else "Mumbai")
            tgt_niche = tgt.get("niche") or ("Hotels" if active_id == "gethotelstays" else "Restaurants")
            loc_str = f"{tgt_city}, {tgt_country}"

            screen = BANNER + f"""
{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}
  {C_WHITE}ACTIVE AGENT:{RESET}       {C_MAGENTA}[ {active_id.upper()} ]{RESET}  {C_DIM}(Press B to toggle){RESET}
  {C_WHITE}TARGET DESTINATION:{RESET} {C_GREEN}{loc_str}{RESET} │ {C_CYAN}{tgt_niche}{RESET}
  {C_WHITE}SENDER ACCOUNT:{RESET}     {C_GREEN}{'onboard@gethotelstays.com' if active_id == 'gethotelstays' else 'alorialabs@gmail.com'}{RESET}
  {C_WHITE}PIPELINE STATS:{RESET}     {C_GREEN}{total}{RESET} Leads │ {C_BLUE}{audited}{RESET} Audited │ {C_YELLOW}{pitched}{RESET} Pitched │ {C_CYAN}{sent_total}{RESET} Sent
{C_CYAN}═══════════════════════════════════════════════════════════════════════════════════════════════{RESET}
"""
            if active_id == "gethotelstays":
                screen += f"""
  {C_GREEN}─── [AUTONOMOUS 24/7 HOTEL ONBOARDING ENGINE] ─────────────────────────────────────────────{RESET}
  {C_WHITE}[1]{RESET} {C_GREEN}🔥 START 24/7 HOTEL ONBOARDING{RESET}   {C_DIM}— Runs continuously: Discover ➔ Pitch ➔ Follow-up{RESET}
  {C_WHITE}[T]{RESET} {C_CYAN}⚙ Set Target City / State{RESET}        {C_DIM}— Destination (Currently: {loc_str}){RESET}
  {C_WHITE}[L]{RESET} {C_YELLOW}📋 Hotel Pipeline & Ledger{RESET}        {C_DIM}— View discovered hotels & outreach statuses{RESET}
  {C_WHITE}[B]{RESET} {C_BLUE}🔄 Switch to Aloria Labs{RESET}          {C_DIM}— Web Agency Agent{RESET}
  {C_WHITE}[0]{RESET} {C_RED}● Disconnect{RESET}                      {C_DIM}— Close connection to laptop{RESET}

  {C_GREEN}Enter command in Termux: {RESET}"""
            else:
                screen += f"""
  {C_CYAN}─── [ALORIA LABS • 24/7 CLIENT ACQUISITION] ───────────────────────────────────────────────{RESET}
  {C_WHITE}[1]{RESET} {C_GREEN}🚀 START 24/7 CLIENT ACQUISITION{RESET} {C_DIM}— Non-stop Maps discovery & tailored web pitches{RESET}
  {C_WHITE}[T]{RESET} {C_CYAN}⚙ Set Target Location / Niche{RESET}   {C_DIM}— Industry & location targeting{RESET}
  {C_WHITE}[L]{RESET} {C_YELLOW}📋 Client Pipeline & Ledger{RESET}       {C_DIM}— View all leads & statuses{RESET}
  {C_WHITE}[B]{RESET} {C_BLUE}🔄 Switch to GetHotelStays{RESET}       {C_DIM}— Hotel Onboarding Agent{RESET}
  {C_WHITE}[0]{RESET} {C_RED}● Disconnect{RESET}                      {C_DIM}— Close connection to laptop{RESET}

  {C_GREEN}Enter command in Termux: {RESET}"""

            send(screen)
            choice = recv_line()
            if choice is None or choice in ["0", "q", "exit"]:
                send(f"\n{C_CYAN}Termux session closed. Goodbye!{RESET}\n")
                break

            choice = choice.lower()

            if choice == "b":
                new_id = "aloria_labs" if active_id == "gethotelstays" else "gethotelstays"
                business_manager.set_active_business(new_id)
                send(f"\n{C_GREEN}[✓] Switched profile to: {new_id.upper()}{RESET}\n")
                time.sleep(1)
                continue

            if choice == "t":
                configure_target_remote(active_id, send, recv_line)
                continue

            if choice == "l":
                leads = db.get_lead_ledger(business_id=active_id, limit=30)
                send(f"\n{C_CYAN}═══════════════════════════════════════════════════════════════════════{RESET}\n")
                send(f"  {C_WHITE}LEAD LEDGER FOR {C_YELLOW}{active_id.upper()}{RESET} ({len(leads)} leads)\n")
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
                continue

            if choice in ["1", "r", ""]:
                send(f"\n{C_GREEN}[► STARTING 24/7 AUTONOMOUS OUTREACH WAVE ON LAPTOP]{RESET}\n")
                send(f"Target: {tgt_niche} in {loc_str}\n")
                try:
                    maps_crawler.crawl_google_maps(city=tgt_city, country=tgt_country, niche=tgt_niche, max_places=5, headless=True, business_id=active_id)
                    website_auditor.audit_pending_leads(limit=5, business_id=active_id)
                    p_name = "gethotelstays" if active_id == "gethotelstays" else "gmail"
                    sent = email_engine.dispatch_initial_emails(limit=5, profile_name=p_name, business_id=active_id)
                    fu = email_engine.dispatch_followups(profile_name=p_name, business_id=active_id)
                    send(f"\n{C_GREEN}[✓] Autonomous wave completed! Sent: {sent} pitches, {fu} follow-ups.{RESET}\n")
                except Exception as e:
                    send(f"\n{C_RED}[!] Error: {e}{RESET}\n")
                send("Press Enter to return to menu...")
                recv_line()
                continue

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
