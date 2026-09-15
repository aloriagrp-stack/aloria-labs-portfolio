import os
import sys

# Ensure UTF-8 console on Windows
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
    except Exception:
        pass

import colorama
from colorama import Fore, Back, Style

# Initialize colorama with Windows virtual terminal processing enabled
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

def print_banner():
    banner_text = f"""
{C_CYAN}  █████╗ ██╗      ██████╗ ██████╗ ██╗ █████╗     ██╗  ██╗██╗   ██╗███╗   ██╗████████╗███████╗██████╗ 
{C_CYAN} ██╔══██╗██║     ██╔═══██╗██╔══██╗██║██╔══██╗    ██║  ██║██║   ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗
{C_BLUE} ███████║██║     ██║   ██║██████╔╝██║███████║    ███████║██║   ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝
{C_BLUE} ██╔══██║██║     ██║   ██║██╔══██╗██║██╔══██║    ██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗
{C_MAGENTA} ██║  ██║███████╗╚██████╔╝██║  ██║██║██║  ██║    ██║  ██║╚██████╔╝██║ ╚████║   ██║   ███████╗██║  ██║
{C_MAGENTA} ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝
{C_WHITE}                       [ AUTONOMOUS B2B INTELLIGENCE & COLD OUTREACH ENGINE ]
{C_DIM}                         Version 2.5 | Zero-API Engineering | Aloria Labs
    """
    print(banner_text)

def print_menu_box(active_sender="alorialabs@gmail.com"):
    print(f"""
{C_CYAN}  ╔═════════════════════════════════════════════════════════════════════════════════════════════════╗
  ║                                   COMMAND & CONTROL CENTER                                      ║
  ╠═════════════════════════════════════════════════════════════════════════════════════════════════╣{RESET}
  {C_WHITE}  [1]{RESET} {C_GREEN}● Live Hunter{RESET}           - {C_WHITE}Watch visible Chrome screen crawl Google Maps live{RESET}
  {C_WHITE}  [2]{RESET} {C_CYAN}● Silent Ghost Mode{RESET}     - {C_DIM}Runs 100% hidden in background (headless){RESET}
  {C_WHITE}  [3]{RESET} {C_MAGENTA}● 24/7 Autopilot Loop{RESET}   - {C_WHITE}Continuous perpetual wave scanner (runs day & night){RESET}
  {C_WHITE}  [4]{RESET} {C_YELLOW}● Safe Dry-Run{RESET}          - {C_WHITE}Extract leads & audit flaws without sending emails{RESET}
  {C_WHITE}  [5]{RESET} {C_BLUE}● Hunter Intel Stats{RESET}    - {C_WHITE}View real-time pipeline totals & database counts{RESET}
  {C_WHITE}  [6]{RESET} {C_GREEN}● Outreach History Log{RESET}  - {C_WHITE}View all contacted leads, dates, times & chat subjects{RESET}
  {C_WHITE}  [7]{RESET} {C_MAGENTA}● Sender Account{RESET}        - {C_DIM}Switch sender profile (Active: {C_YELLOW}{active_sender}{C_DIM}){RESET}
  {C_WHITE}  [0]{RESET} {C_RED}● Exit Console{RESET}          - {C_DIM}Close Hunter Command Center{RESET}
  {C_WHITE}  [ENTER]{RESET}                      - {C_GREEN}Default Quick Launch (Option 1 Live Hunter){RESET}
{C_CYAN}  ╚═════════════════════════════════════════════════════════════════════════════════════════════════╝{RESET}
    """)

def log_target(country, cities, niches, headless, dry_run):
    mode_tag = f"{C_YELLOW}[DRY-RUN - NO EMAILS]{RESET}" if dry_run else f"{C_GREEN}[LIVE SMTP OUTREACH]{RESET}"
    browser_tag = f"{C_DIM}[HEADLESS BACKGROUND]{RESET}" if headless else f"{C_CYAN}[VISIBLE SCREEN WINDOW]{RESET}"
    print(f"\n{C_CYAN}┌───[ TARGET PROFILE ]─────────────────────────────────────────────────────────────┐{RESET}")
    print(f"{C_CYAN}│{RESET}  {C_WHITE}Target Country:{RESET}   {C_GREEN}{country}{RESET}")
    print(f"{C_CYAN}│{RESET}  {C_WHITE}Target Cities:{RESET}    {C_CYAN}{', '.join(cities)}{RESET}")
    print(f"{C_CYAN}│{RESET}  {C_WHITE}Target Niches:{RESET}    {C_MAGENTA}{', '.join(niches)}{RESET}")
    print(f"{C_CYAN}│{RESET}  {C_WHITE}Execution Mode:{RESET}   {browser_tag} {mode_tag}")
    print(f"{C_CYAN}└──────────────────────────────────────────────────────────────────────────────────┘{RESET}\n")

def log_batch_header(city, niche):
    print(f"\n{Back.CYAN}{Fore.BLACK} ► NEW SECTOR SCAN ◄ {RESET} {C_WHITE}Target City:{RESET} {C_GREEN}{city.upper()}{RESET} │ {C_WHITE}Niche:{RESET} {C_YELLOW}{niche.upper()}{RESET}")
    print(f"{C_CYAN}{'─' * 80}{RESET}")

def log_crawler_step(step, total, msg):
    print(f"  {C_CYAN}[⚡ MAPS {step}/{total}]{RESET} {msg}")

def log_discovered_place(index, total, name, website_url, phone, rating):
    if not website_url:
        status_tag = f"{Back.YELLOW}{Fore.BLACK} ★ GOLDEN LEAD - NO WEBSITE ★ {RESET}"
        name_str = f"{C_YELLOW}{name}{RESET}"
    else:
        status_tag = f"{C_BLUE}[WEBSITE FOUND]{RESET} {C_DIM}{website_url}{RESET}"
        name_str = f"{C_WHITE}{name}{RESET}"

    phone_str = f"{C_CYAN}☎ {phone or 'N/A'}{RESET}"
    rating_str = f"{C_YELLOW}★ {rating or 'N/A'}{RESET}"
    print(f"  {C_CYAN}[{index:02d}/{total:02d}]{RESET} {status_tag} {name_str} │ {phone_str} │ {rating_str}")

def log_audit_start(name, url):
    print(f"\n  {C_BLUE}[AUDIT INITIATED]{RESET} {C_WHITE}{name}{RESET} ➔ {C_DIM}{url}{RESET}")

def log_audit_result(email, vulnerabilities, response_time):
    if email:
        print(f"    {C_GREEN}[✓ EMAIL EXTRACTED]{RESET} {Back.GREEN}{Fore.BLACK} {email} {RESET}")
    else:
        print(f"    {C_RED}[✗ EMAIL MISSING]{RESET}   {C_DIM}No public mailto/contact email discovered{RESET}")

    if vulnerabilities:
        for v in vulnerabilities:
            if "error" in v.lower() or "missing ssl" in v.lower():
                print(f"    {C_RED}[⚠ CRITICAL FLAW]{RESET}  {v}")
            else:
                print(f"    {C_YELLOW}[⚠ ADVISORY]{RESET}       {v}")
    else:
        print(f"    {C_GREEN}[✓ HEALTHY]{RESET}        {C_DIM}No major infrastructure flaws detected{RESET}")

def log_email_dispatch(lead_name, email, subject, success, status_msg=""):
    if success:
        print(f"  {C_GREEN}[✉ OUTREACH SENT]{RESET}   {C_WHITE}To:{RESET} {C_GREEN}{email}{RESET} │ {C_DIM}{lead_name}{RESET}")
        print(f"     {C_DIM}Subject: '{subject}'{RESET}")
    else:
        print(f"  {C_RED}[✗ OUTREACH FAILED]{RESET} {C_WHITE}To:{RESET} {C_RED}{email}{RESET} │ {C_YELLOW}{status_msg}{RESET}")

def log_stats_dashboard(stats):
    total = stats.get('total', 0)
    golden = stats.get('without_website', 0)
    audited = stats.get('with_website', 0)
    total_emails = stats.get('total_emails_sent', 0)
    statuses = stats.get('statuses', {})

    print(f"""
{C_CYAN}  ╔═══════════════════════════════════════════════════════════════════════════════════════╗
  ║                                REAL-TIME HUNTER STATS                                 ║
  ╠═══════════════════════════════════════════════════════════════════════════════════════╣{RESET}
  {C_WHITE}  Total Discovered Leads:{RESET}       {C_CYAN}{total}{RESET}
  {C_WHITE}  Golden Leads (No Website):{RESET}    {C_YELLOW}{golden}  {Back.YELLOW}{Fore.BLACK} [PRIORITY PITCH TARGETS] {RESET}
  {C_WHITE}  Websites Audited:{RESET}             {C_BLUE}{audited}{RESET}
  {C_WHITE}  Outreach Emails Dispatched:{RESET}   {C_GREEN}{total_emails}{RESET}
  {C_WHITE}  Pipeline Status Breakdown:{RESET}    {C_MAGENTA}{statuses}{RESET}
{C_CYAN}  ╚═══════════════════════════════════════════════════════════════════════════════════════╝{RESET}
    """)

def log_outreach_history_table(history_rows):
    print(f"""
{C_GREEN}  ╔═══════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
  ║                                        OUTREACH HISTORY & SENT LOGS                                           ║
  ╠═══════════════════════════════════════════════════════════════════════════════════════════════════════════════╣{RESET}""")
    if not history_rows:
        print(f"    {C_DIM}No outreach emails recorded in database yet.{RESET}\n")
        print(f"{C_GREEN}  ╚═══════════════════════════════════════════════════════════════════════════════════════════════════════════════╝{RESET}\n")
        return

    print(f"  {C_CYAN}{'#':<3} {'DATE & TIME':<20} {'RECIPIENT EMAIL':<30} {'BUSINESS NAME':<32} {'TYPE':<10} {'STATUS'}{RESET}")
    print(f"  {C_DIM}{'─' * 107}{RESET}")

    for idx, row in enumerate(history_rows, 1):
        dt = row.get("sent_at", "N/A")[:19]
        recip = (row.get("recipient_email") or "N/A")[:28]
        biz = (row.get("business_name") or "N/A")[:30]
        p_type = row.get("pitch_type", "INITIAL")
        status = row.get("status", "SENT")
        
        status_badge = f"{C_GREEN}[✓ SENT]{RESET}" if status == "SENT" else f"{C_RED}[✗ FAIL]{RESET}"
        type_badge = f"{C_MAGENTA}{p_type}{RESET}"
        
        print(f"  {C_WHITE}{idx:<3}{RESET} {C_CYAN}{dt:<20}{RESET} {C_WHITE}{recip:<30}{RESET} {C_YELLOW}{biz:<32}{RESET} {type_badge:<19} {status_badge}")

    print(f"{C_GREEN}  ╚═══════════════════════════════════════════════════════════════════════════════════════════════════════════════╝{RESET}\n")

def log_cooldown(seconds):
    print(f"  {C_CYAN}[⏳ COOLDOWN]{RESET} {C_DIM}Sleeping {seconds}s before next sector scan...{RESET}")
