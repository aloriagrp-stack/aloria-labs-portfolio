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

import runner

def interactive_mode():
    print("""
  +--------------------------------------------------------------+
  |              ALORIA AUTONOMOUS HUNTER CONTROLLER             |
  |         One-Click B2B Discovery & Automated Cold Outreach    |
  +--------------------------------------------------------------+
    """)
    print("Choose an operating mode:")
    print("  [1] Live Hunt (Visible Chromium Window - Watch it on screen)")
    print("  [2] Silent Background Mode (Headless)")
    print("  [3] 24/7 Autopilot Daemon Mode (Continuous Background Hunting)")
    print("  [4] Safe Dry-Run (Crawl & Audit without sending emails)")
    print("  [5] View Current Database Stats")
    print("  [Enter] Quick Launch with Smart Defaults (Option 1)")
    print()

    choice = input("Select an option [1-5]: ").strip()

    if choice == "5":
        import db
        stats = db.get_stats()
        print("\n=== [HUNTER DATABASE STATS] ===")
        print(f"Total Leads Discovered:    {stats['total']}")
        print(f"Golden Leads (No Website): {stats['without_website']}")
        print(f"Websites Audited:          {stats['with_website']}")
        print(f"Status Breakdown:          {stats['statuses']}")
        print("===============================\n")
        return

    country = input("Target Country [Default: Algeria]: ").strip() or "Algeria"
    city = input("Target City [Default: Algiers]: ").strip() or "Algiers"
    niche = input("Target Niche [Default: Restaurants]: ").strip() or "Restaurants"
    limit_str = input("Max places to hunt [Default: 10]: ").strip()
    limit = int(limit_str) if limit_str.isdigit() else 10

    if choice == "3":
        print(f"\n[*] Starting 24/7 Autonomous Autopilot Daemon for {country}...")
        while True:
            runner.run_hunter_cycle(
                country=country,
                cities=[city],
                niches=[niche],
                max_per_niche=limit,
                headless=True,
                dry_run=False
            )
            print("[*] Wave finished. Sleeping 2 hours before scanning next leads...")
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
