import re
import time
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import db
import ui

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
IGNORED_EMAIL_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.css', '.js')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def clean_email(email_str):
    email = email_str.strip().lower()
    if any(email.endswith(ext) for ext in IGNORED_EMAIL_EXTENSIONS):
        return None
    if "example.com" in email or "sentry.io" in email or "domain.com" in email:
        return None
    return email

def audit_single_website(lead):
    lead_id = lead["id"]
    url = lead["website_url"]
    business_name = lead["business_name"]

    ui.log_audit_start(business_name, url or "N/A")

    if not url or not url.startswith("http"):
        # No website to audit
        db.update_audit(lead_id, email="", audit_summary="No website present on Google Maps presence.")
        return {"email": None, "audit": "No website present."}

    discovered_emails = set()
    vulnerabilities = []
    response_time = 0.0

    try:
        start_t = time.time()
        resp = requests.get(url, headers=HEADERS, timeout=12, verify=False)
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
            href = mailto.get("href", "").replace("mailto:", "").split("?")[0]
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
                href = a["href"].lower()
                if any(k in href for k in ["contact", "about", "reach", "support", "touch"]):
                    contact_links.append(urljoin(url, a["href"]))

            for c_url in contact_links[:2]:
                try:
                    c_resp = requests.get(c_url, headers=HEADERS, timeout=8, verify=False)
                    if c_resp.status_code == 200:
                        c_soup = BeautifulSoup(c_resp.text, "html.parser")
                        for mailto in c_soup.select('a[href^="mailto:"]'):
                            href = mailto.get("href", "").replace("mailto:", "").split("?")[0]
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
        vulnerabilities.append("Server connection timed out (>12s latency)")
    except Exception as e:
        vulnerabilities.append(f"Connection failure: {str(e)[:60]}")

    primary_email = list(discovered_emails)[0] if discovered_emails else ""
    audit_text = " | ".join(vulnerabilities) if vulnerabilities else f"Site operational ({response_time}s latency)"

    ui.log_audit_result(primary_email, vulnerabilities, response_time)

    db.update_audit(lead_id, email=primary_email, audit_summary=audit_text)

    return {
        "email": primary_email,
        "audit": audit_text,
        "latency": response_time,
        "vulnerabilities": vulnerabilities
    }

def audit_pending_leads(limit=20, business_id=None):
    pending = db.get_pending_audits(business_id=business_id, limit=limit)
    print(f"  {ui.C_BLUE}[⚡ AUDITOR ENGINE]{ui.RESET} Inspecting {ui.C_WHITE}{len(pending)}{ui.RESET} candidate websites for technical vulnerabilities & email extraction...")
    results = []
    for lead in pending:
        res = audit_single_website(lead)
        results.append(res)
        time.sleep(1.5)  # Polite crawl delay
    return results

if __name__ == "__main__":
    audit_pending_leads(limit=5)
