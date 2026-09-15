import os
import sys
from pathlib import Path

# Ensure D:\playwright-browsers path is set
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "D:\\playwright-browsers"

# Add aloria-hunter to Python path
ROOT_DIR = Path(__file__).resolve().parent
HUNTER_DIR = ROOT_DIR / "aloria-hunter"
if str(HUNTER_DIR) not in sys.path:
    sys.path.insert(0, str(HUNTER_DIR))

import ui  # type: ignore
import runner  # type: ignore
import db  # type: ignore
import config  # type: ignore
import terminal_cockpit  # type: ignore

def select_sender_account_menu():
    profiles, active_key = config.list_smtp_profiles()
    print(f"\n{ui.C_CYAN}┌───[ SENDER ACCOUNT MANAGER ]─────────────────────────────────────────────────────┐{ui.RESET}")
    profile_keys = list(profiles.keys())
    for idx, key in enumerate(profile_keys, 1):
        prof = profiles[key]
        active_badge = f"{ui.C_GREEN}[ACTIVE]{ui.RESET}" if key == active_key else f"{ui.C_DIM}[INACTIVE]{ui.RESET}"
        pwd_status = f"{ui.C_GREEN}Configured{ui.RESET}" if prof.get("password") else f"{ui.C_YELLOW}No Password{ui.RESET}"
        print(f"{ui.C_CYAN}│{ui.RESET}  [{idx}] {ui.C_WHITE}{prof.get('name', key)}{ui.RESET} ({prof.get('email')}) - {active_badge} (Auth: {pwd_status})")
    print(f"{ui.C_CYAN}└──────────────────────────────────────────────────────────────────────────────────┘{ui.RESET}")

    sel = input(f"\n  Select profile number to activate [1-{len(profile_keys)}] or Enter to cancel: ").strip()
    if sel.isdigit() and 1 <= int(sel) <= len(profile_keys):
        chosen_key = profile_keys[int(sel) - 1]
        chosen_prof = profiles[chosen_key]

        if not chosen_prof.get("password"):
            print(f"\n  {ui.C_YELLOW}[!] Profile '{chosen_key}' has no password configured.{ui.RESET}")
            new_pwd = input(f"  Enter SMTP password / App password for {chosen_prof.get('email')} (or Enter to skip): ").strip()
            if new_pwd:
                data = config.get_raw_smtp_data()
                if "profiles" in data and chosen_key in data["profiles"]:
                    data["profiles"][chosen_key]["password"] = new_pwd
                    import json
                    with open(config.SMTP_CONFIG_PATH, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                print(f"  {ui.C_GREEN}[✓] Password saved.{ui.RESET}")

        config.set_active_smtp_profile(chosen_key)
        print(f"  {ui.C_GREEN}[✓] Active sender set to: {chosen_prof.get('email')}{ui.RESET}\n")
    else:
        print("  Cancelled.\n")
    input("  Press Enter to return to Command Center...")

def interactive_mode():
    while True:
        profiles, active_key = config.list_smtp_profiles()
        active_email = profiles.get(active_key, {}).get("email", "alorialabs@gmail.com")

        ui.print_banner()
        ui.print_menu_box(active_sender=active_email)

        choice = input(f"  {ui.C_GREEN}Select an option [0-7]: {ui.RESET}").strip()

        if choice == "0":
            print(f"\n  {ui.C_CYAN}[*] Closing Hunter Command Center. Farewell, Architect.{ui.RESET}\n")
            break

        if choice == "5":
            stats = db.get_stats()
            ui.log_stats_dashboard(stats)
            input("  Press Enter to return to Command Center...")
            continue

        if choice == "6":
            history = db.get_outreach_history(limit=50)
            ui.log_outreach_history_table(history)
            input("  Press Enter to return to Command Center...")
            continue

        if choice == "7":
            select_sender_account_menu()
            continue

        print()
        country_in = input(f"  {ui.C_WHITE}Target Country {ui.C_DIM}[Default: Algeria]{ui.RESET}: ").strip()
        country = country_in or "Algeria"

        city_in = input(f"  {ui.C_WHITE}Target City    {ui.C_DIM}[Default: Algiers]{ui.RESET}: ").strip()
        city = city_in or "Algiers"

        niche_in = input(f"  {ui.C_WHITE}Target Niche   {ui.C_DIM}[Default: Restaurants]{ui.RESET}: ").strip()
        niche = niche_in or "Restaurants"

        limit_in = input(f"  {ui.C_WHITE}Max Places     {ui.C_DIM}[Default: 10]{ui.RESET}: ").strip()
        limit = int(limit_in) if limit_in.isdigit() else 10

        if choice == "3":
            print(f"\n{ui.C_MAGENTA}[*] Launching 24/7 Perpetual Autopilot Daemon for {country}...{ui.RESET}")
            print(f"{ui.C_DIM}    Press Ctrl+C anytime to return to Command Center.{ui.RESET}\n")
            try:
                while True:
                    runner.run_hunter_cycle(
                        country=country,
                        cities=[city],
                        niches=[niche],
                        max_per_niche=limit,
                        headless=True,
                        dry_run=False
                    )
                    print(f"\n{ui.C_CYAN}[*] Wave complete. Sleeping 2 hours before next scan wave...{ui.RESET}")
                    import time
                    time.sleep(7200)
            except KeyboardInterrupt:
                print(f"\n{ui.C_YELLOW}[*] Daemon stopped by user.{ui.RESET}")
        elif choice == "2":
            runner.run_hunter_cycle(
                country=country,
                cities=[city],
                niches=[niche],
                max_per_niche=limit,
                headless=True,
                dry_run=False
            )
        elif choice == "4":
            runner.run_hunter_cycle(
                country=country,
                cities=[city],
                niches=[niche],
                max_per_niche=limit,
                headless=False,
                dry_run=True
            )
        else:  # Option 1 or default (Enter)
            runner.run_hunter_cycle(
                country=country,
                cities=[city],
                niches=[niche],
                max_per_niche=limit,
                headless=False,
                dry_run=False
            )

        print()
        input(f"  {ui.C_GREEN}Wave finished! Press Enter to return to Command Center...{ui.RESET}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--legacy":
        interactive_mode()
    elif len(sys.argv) > 1:
        # User passed CLI flags like: python hunt.py --country UAE --headless
        runner.main()
    else:
        # Zero-arg 1-click execution launches WTF/Sampler Terminal Cockpit
        terminal_cockpit.run_cockpit_loop()
