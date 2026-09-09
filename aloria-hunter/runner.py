import time
import sys
import argparse
from datetime import datetime
import config
import db
import maps_crawler
import website_auditor
import email_engine

def print_banner():
    print("""
  +--------------------------------------------------------------+
  |                 ALORIA AUTONOMOUS HUNTER AGENT               |
  |         Production-Grade Cold Outreach & Lead Discovery      |
  +--------------------------------------------------------------+
    """)

def run_hunter_cycle(country=None, cities=None, niches=None, max_per_niche=15, headless=False, dry_run=False):
    country = country or config.DEFAULT_COUNTRY
    cities = cities or config.DEFAULT_CITIES
    niches = niches or config.DEFAULT_NICHES

    print_banner()
    print(f"[*] Target Country: {country}")
    print(f"[*] Target Cities:  {', '.join(cities)}")
    print(f"[*] Target Niches:  {', '.join(niches)}")
    print(f"[*] Browser Mode:   {'Silent Background (Headless)' if headless else 'Visible Screen Window (Live Watching)'}")
    print(f"[*] Dry-Run Mode:   {dry_run} (Emails {'DISABLED' if dry_run else 'ACTIVE via SMTP'})\n")

    for city in cities:
        for niche in niches:
            print(f"\n>>> [NEW HUNTING BATCH] City: {city} | Niche: {niche} <<<")
            
            # Step 1: Autonomous Google Maps Discovery
            try:
                discovered = maps_crawler.crawl_google_maps(
                    city=city,
                    country=country,
                    niche=niche,
                    max_places=max_per_niche,
                    headless=headless
                )
            except Exception as e:
                print(f"[!] Error in crawler for {city} - {niche}: {e}")
                discovered = []

            # Step 2: Autonomous Technical Audits
            try:
                audited = website_auditor.audit_pending_leads(limit=max_per_niche)
            except Exception as e:
                print(f"[!] Error in auditor: {e}")

            # Step 3: Dispatch Outreach Emails (if not in dry run)
            if not dry_run:
                try:
                    sent = email_engine.dispatch_initial_emails(limit=10)
                except Exception as e:
                    print(f"[!] Error in email dispatch: {e}")

                # Step 4: Dispatch Scheduled 2-Day Follow-ups
                try:
                    followups = email_engine.dispatch_followups()
                except Exception as e:
                    print(f"[!] Error in follow-up dispatch: {e}")

            # Step 5: Real-time Stats
            stats = db.get_stats()
            print(f"\n--- [CURRENT AGENT STATS] ---")
            print(f"Total Leads Discovered:    {stats['total']}")
            print(f"Golden Leads (No Website): {stats['without_website']}")
            print(f"Audited Websites:          {stats['with_website']}")
            print(f"Status Breakdown:          {stats['statuses']}")
            print(f"-----------------------------\n")

            # Pause between niches
            print("[*] Sleeping 30s before moving to next target niche...")
            time.sleep(30)

def main():
    parser = argparse.ArgumentParser(description="Aloria Autonomous Lead Hunter")
    parser.add_argument("--country", default="Algeria", help="Target country (e.g. Algeria, UAE, India, UK)")
    parser.add_argument("--city", default="Algiers", help="Target city")
    parser.add_argument("--niche", default="Restaurants", help="Target niche (e.g. Restaurants, Hotels, Cafes)")
    parser.add_argument("--limit", type=int, default=10, help="Max places to scrape per niche")
    parser.add_argument("--headless", action="store_true", help="Run browser silently in background")
    parser.add_argument("--dry-run", action="store_true", help="Crawl and audit without sending emails")
    parser.add_argument("--daemon", action="store_true", help="Run continuously in 24/7 background loop")
    args = parser.parse_args()

    cities = [args.city] if args.city else config.DEFAULT_CITIES
    niches = [args.niche] if args.niche else config.DEFAULT_NICHES

    if args.daemon:
        print("[!] Running in 24/7 Autonomous Daemon Mode. Press Ctrl+C to stop.")
        while True:
            run_hunter_cycle(
                country=args.country,
                cities=cities,
                niches=niches,
                max_per_niche=args.limit,
                headless=args.headless,
                dry_run=args.dry_run
            )
            print("[*] Cycle complete. Resting for 2 hours before scanning next wave...")
            time.sleep(7200)
    else:
        run_hunter_cycle(
            country=args.country,
            cities=cities,
            niches=niches,
            max_per_niche=args.limit,
            headless=args.headless,
            dry_run=args.dry_run
        )

if __name__ == "__main__":
    main()
