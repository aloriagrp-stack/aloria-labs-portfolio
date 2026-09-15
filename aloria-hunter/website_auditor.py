import re
import time
import requests
import urllib3
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import db
import ui
import email_verifier

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,10}')
IGNORED_EMAIL_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.css', '.js')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def clean_email(email_str):
    """
    Backwards-compatible Tier-1 clean email function.
    Cleans strings, filters framework tags, asset extensions, and blacklisted entries.
    """
    if not email_str:
        return None
    email = email_str.strip().lower()
    # Strip any trailing punctuation like hyphens, dots, dashes, commas
    email = re.sub(r'^[<"\'\s]+|[>"\'\s,;.-]+$', '', email)

    # Reject CDN / framework / library package patterns with versions (e.g. bootstrap@5.3.3, psk-gallery@1.1.0-5, fancybox@3.5.7, aos@2.3.1)
    if re.search(r'@[0-9]+', email) or re.search(r'@[a-z0-9_-]*\d+\.\d+', email):
        return None
    if any(bad in email for bad in [
        "bootstrap", "jquery", "react", "webpack", "sentry", "example.com", "domain.com", 
        "wixpress", "cloudflare", "schema.org", "fancybox", "psk-gallery", "wix-fonts",
        "youremail.com", "mywebsite.com", "email.com", "test.com"
    ]):
        return None
    # Reject asset extensions
    if any(email.endswith(ext) for ext in IGNORED_EMAIL_EXTENSIONS):
        return None
    # Must have a valid TLD with only letters
    if not re.search(r'\.[a-z]{2,10}$', email):
        return None

    # Check blacklist table - never accept blacklisted email
    if db.is_email_blacklisted(email):
        return None

    return email

def clean_and_verify_email(email_str, check_mx=True):
    """
    Tier-2 & Tier-3 deep validation:
    Verifies live DNS/MX records, rejects dummy placeholders (xyz@, test@, info@hotel.com),
    and filters disposable domains.
    """
    cleaned = clean_email(email_str)
    if not cleaned:
        return None
    
    is_valid, verified_email, reason = email_verifier.verify_email_deliverability(cleaned, check_mx=check_mx)
    if is_valid and verified_email:
        if db.is_email_blacklisted(verified_email):
            return None
        return verified_email
    return None

def audit_single_website(lead):
    lead_id = lead["id"]
    url = lead["website_url"]
    business_name = lead["business_name"]

    ui.log_audit_start(business_name, url or "N/A")

    if not url or not url.startswith("http"):
        # No website to audit
        db.update_audit(lead_id, email="", audit_summary="No website present on Google Maps presence.")
        return {"id": lead_id, "email": None, "audit": "No website present.", "lead": lead}

    discovered_emails = set()
    vulnerabilities = []
    response_time = 0.0

    try:
        start_t = time.time()
        resp = requests.get(url, headers=HEADERS, timeout=8, verify=False)
        response_time = round(time.time() - start_t, 2)

        if resp.status_code != 200:
            vulnerabilities.append(f"Server returned HTTP {resp.status_code} error status")

        if response_time > 2.5:
            vulnerabilities.append(f"Slow server response latency ({response_time}s)")

        soup = BeautifulSoup(resp.text, "html.parser")

        # 1. Check Mobile Viewport
        viewport = soup.find("meta", attrs={"name": re.compile(r"viewport", re.I)})
        if not viewport:
            vulnerabilities.append("Missing mobile viewport optimization (fails mobile rendering)")

        # 2. Check SSL
        if not url.startswith("https://"):
            vulnerabilities.append("Non-secure HTTP connection (missing SSL certificate)")

        # 3. Check for modern interactive features
        text_lower = resp.text.lower()
        if "order online" not in text_lower and "book table" not in text_lower and "reservation" not in text_lower:
            vulnerabilities.append("Lacks automated online booking or order system")

        # 4. Extract Emails from Homepage
        for mailto in soup.select('a[href^="mailto:"]'):
            raw_href = mailto.get("href")
            href_val = str(raw_href[0] if isinstance(raw_href, list) else (raw_href or ""))
            href = href_val.replace("mailto:", "").split("?")[0]
            cleaned = clean_email(href)
            if cleaned:
                discovered_emails.add(cleaned)

        raw_emails = EMAIL_REGEX.findall(resp.text)
        for e in raw_emails:
            cleaned = clean_email(e)
            if cleaned:
                discovered_emails.add(cleaned)

        # 5. Check Contact Page if no email on homepage
        if not discovered_emails:
            contact_links = []
            for a in soup.find_all("a", href=True):
                raw_href = a.get("href")
                href_val = str(raw_href[0] if isinstance(raw_href, list) else (raw_href or ""))
                href_lower = href_val.lower()
                if any(k in href_lower for k in ["contact", "about", "reach", "support", "touch", "contactez", "reserva"]):
                    contact_links.append(urljoin(url, href_val))

            for c_url in contact_links[:2]:
                try:
                    c_resp = requests.get(c_url, headers=HEADERS, timeout=6, verify=False)
                    if c_resp.status_code == 200:
                        c_soup = BeautifulSoup(c_resp.text, "html.parser")
                        for mailto in c_soup.select('a[href^="mailto:"]'):
                            raw_href = mailto.get("href")
                            href_val = str(raw_href[0] if isinstance(raw_href, list) else (raw_href or ""))
                            href = href_val.replace("mailto:", "").split("?")[0]
                            cleaned = clean_email(href)
                            if cleaned:
                                discovered_emails.add(cleaned)
                        for e in EMAIL_REGEX.findall(c_resp.text):
                            cleaned = clean_email(e)
                            if cleaned:
                                discovered_emails.add(cleaned)
                        if discovered_emails:
                            break
                except Exception:
                    continue

    except requests.exceptions.SSLError:
        vulnerabilities.append("Broken or invalid SSL/HTTPS configuration")
    except requests.exceptions.Timeout:
        vulnerabilities.append("Server connection timed out (>8s latency)")
    except Exception as e:
        vulnerabilities.append(f"Connection failure: {str(e)[:60]}")

    # ZERO-BOUNCE SELECTION: Verify deliverability with live MX check and score candidates
    verified_candidates = []
    for cand in discovered_emails:
        verified = clean_and_verify_email(cand, check_mx=True)
        if verified:
            score = email_verifier.score_email_for_lead(verified, business_name, url)
            verified_candidates.append((score, verified))

    primary_email = ""
    if verified_candidates:
        # Pick the highest scoring verified email (best domain match / business inbox)
        verified_candidates.sort(key=lambda x: x[0], reverse=True)
        primary_email = verified_candidates[0][1]

    audit_text = " | ".join(vulnerabilities) if vulnerabilities else f"Site operational ({response_time}s latency)"

    ui.log_audit_result(primary_email, vulnerabilities, response_time)

    db.update_audit(lead_id, email=primary_email, audit_summary=audit_text)

    return {
        "id": lead_id,
        "email": primary_email,
        "audit": audit_text,
        "latency": response_time,
        "vulnerabilities": vulnerabilities,
        "lead": lead
    }

def audit_pending_leads(limit=20, business_id=None, on_step=None, should_stop=None):
    """
    Parallelized Website Auditor:
    Uses ThreadPoolExecutor(max_workers=8) to audit 20-30 candidate websites concurrently.
    Completes in seconds rather than minutes!
    """
    pending = db.get_pending_audits(business_id=business_id, limit=limit)
    if not pending:
        if on_step:
            on_step("All discovered leads are already audited. 0 pending candidate websites in queue.")
        return []

    print(f"  {ui.C_BLUE}[⚡ PARALLEL AUDITOR ENGINE]{ui.RESET} Inspecting {ui.C_WHITE}{len(pending)}{ui.RESET} candidate websites concurrently (8 workers)...")
    if on_step:
        on_step(f"Identified {len(pending)} pending candidate websites. Initializing concurrent audit workers...")

    results = []
    workers = min(6, len(pending))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_lead = {executor.submit(audit_single_website, lead): lead for lead in pending}
        for future in as_completed(future_to_lead):
            if should_stop and should_stop():
                if on_step:
                    on_step("Halt directive received from operator. Safely stopping website audit sweep.")
                break
            try:
                res = future.result()
                results.append(res)
                if on_step:
                    b_name = res.get("lead", {}).get("business_name", "Lead")
                    em = res.get("email")
                    lat = res.get("latency", 0)
                    if em:
                        on_step(f"Audited '{b_name}': Verified inbox {em} (MX check passed ✓, Latency: {lat}s)")
                    else:
                        on_step(f"Audited '{b_name}': {res.get('audit', 'Domain reachable')} (Latency: {lat}s)")
            except Exception as e:
                lead = future_to_lead[future]
                print(f"  {ui.C_RED}[!] Auditor thread error for '{lead.get('business_name')}': {e}{ui.RESET}")

    verified_emails_found = sum(1 for r in results if r.get("email"))
    print(f"  {ui.C_GREEN}[✓] Concurrent audit complete! Found {verified_emails_found} verified deliverable business emails.{ui.RESET}")
    return results

if __name__ == "__main__":
    audit_pending_leads(limit=5)
