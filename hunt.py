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

import ui
import runner
import db

def interactive_mode():
    ui.print_banner()
    ui.print_menu_box()

    choice = input(f"  {ui.C_GREEN}Select an option [1-5]: {ui.RESET}").strip()

    if choice == "5":
        stats = db.get_stats()
        ui.log_stats_dashboard(stats)
        return

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
    else:  # Option 1 or default
        runner.run_hunter_cycle(
            country=country,
            cities=[city],
            niches=[niche],
            max_per_niche=limit,
            headless=False,
            dry_run=False
        )

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # User passed CLI flags like: python hunt.py --country UAE --headless
        runner.main()
    else:
        # Zero-arg 1-click execution
        interactive_mode()
