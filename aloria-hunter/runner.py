import time
import sys
import argparse
from datetime import datetime
import config
import db
import maps_crawler
import website_auditor
import email_engine
import ui
import threading

_PARALLEL_FOLLOWUP_STARTED = False

def start_parallel_followup_daemon(interval_seconds=60):
    global _PARALLEL_FOLLOWUP_STARTED
    if _PARALLEL_FOLLOWUP_STARTED:
        return
    _PARALLEL_FOLLOWUP_STARTED = True

    def _daemon_loop():
        while True:
            try:
                overdue = db.get_leads_ready_for_followup(interval_days=getattr(config, "FOLLOW_UP_INTERVAL_DAYS", 3))
                if overdue:
                    print(f"\n  {ui.C_MAGENTA}[⚡ PARALLEL FOLLOW-UP DAEMON]{ui.RESET} Found {len(overdue)} leads ready. Dispatching concurrently...")
                    email_engine.dispatch_followups()
            except Exception as e:
                pass
            time.sleep(interval_seconds)

    t = threading.Thread(target=_daemon_loop, daemon=True, name="RunnerFollowupDaemon")
    t.start()

def run_hunter_cycle(country=None, cities=None, niches=None, max_per_niche=15, headless=False, dry_run=False):
    country = country or config.DEFAULT_COUNTRY
    cities = cities or config.DEFAULT_CITIES
    niches = niches or config.DEFAULT_NICHES

    ui.print_banner()
    ui.log_target(country, cities, niches, headless, dry_run)

    if not dry_run:
        start_parallel_followup_daemon(interval_seconds=60)

    for city in cities:
        for niche in niches:
            ui.log_batch_header(city, niche)
            
            # Step 0: Priority Overdue Follow-ups (Offline Catch-up)
            if not dry_run:
                overdue = db.get_overdue_followups(interval_days=config.FOLLOW_UP_INTERVAL_DAYS)
                if overdue:
                    print(f"  {ui.C_YELLOW}[⚡ PRIORITY PROTOCOL]{ui.RESET} Found {len(overdue)} leads overdue for follow-up. Dispatching now...")
                    try:
                        email_engine.dispatch_followups()
                    except Exception as e:
                        print(f"  {ui.C_RED}[!] Error in priority follow-ups: {e}{ui.RESET}")


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
                print(f"  {ui.C_RED}[!] Error in crawler for {city} - {niche}: {e}{ui.RESET}")
                discovered = []

            # Step 2: Autonomous Technical Audits
            try:
                audited = website_auditor.audit_pending_leads(limit=max_per_niche)
            except Exception as e:
                print(f"  {ui.C_RED}[!] Error in website auditor: {e}{ui.RESET}")

            # Step 3: Dispatch Outreach Emails (if not in dry run)
            if not dry_run:
                try:
                    sent = email_engine.dispatch_initial_emails(limit=10)
                except Exception as e:
                    print(f"  {ui.C_RED}[!] Error in email engine: {e}{ui.RESET}")

                # Step 4: Dispatch Scheduled 2-Day Follow-ups
                try:
                    followups = email_engine.dispatch_followups()
                except Exception as e:
                    print(f"  {ui.C_RED}[!] Error in follow-up engine: {e}{ui.RESET}")

            # Step 5: Real-time Stats
            stats = db.get_stats()
            ui.log_stats_dashboard(stats)

            # Pause between niches
            ui.log_cooldown(30)
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
    parser.add_argument("--stats", action="store_true", help="Display current hunter database stats")
    args = parser.parse_args()

    if args.stats:
        ui.print_banner()
        ui.log_stats_dashboard(db.get_stats())
        return

    cities = [args.city] if args.city else config.DEFAULT_CITIES
    niches = [args.niche] if args.niche else config.DEFAULT_NICHES

    if args.daemon:
        print(f"{ui.C_MAGENTA}[!] Running in 24/7 Autonomous Daemon Mode. Press Ctrl+C to terminate.{ui.RESET}")
        while True:
            run_hunter_cycle(
                country=args.country,
                cities=cities,
                niches=niches,
                max_per_niche=args.limit,
                headless=args.headless,
                dry_run=args.dry_run
            )
            print(f"\n{ui.C_CYAN}[*] Cycle complete. Resting 2 hours before scanning next wave...{ui.RESET}")
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
