import sys
import re
import time
import requests

if sys.platform == "win32":
    try:
        reconfig_stdout = getattr(sys.stdout, "reconfigure", None)
        if callable(reconfig_stdout):
            reconfig_stdout(encoding="utf-8", errors="replace")
        reconfig_stderr = getattr(sys.stderr, "reconfigure", None)
        if callable(reconfig_stderr):
            reconfig_stderr(encoding="utf-8", errors="replace")
    except Exception:
        pass
import urllib3
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import db
import ui
import config
import email_verifier

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,10}')
IGNORED_EMAIL_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.css', '.js')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Thread-safe pooled HTTP Session to prevent socket exhaustion with 100 concurrent workers
_SHARED_SESSION = None

def get_shared_session():
    global _SHARED_SESSION
    if _SHARED_SESSION is None:
        _SHARED_SESSION = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=120,
            pool_maxsize=120,
            max_retries=1,
            pool_block=False
        )
        _SHARED_SESSION.mount("http://", adapter)
        _SHARED_SESSION.mount("https://", adapter)
    return _SHARED_SESSION

def deobfuscate_text(text: str) -> str:
    """Decodes obfuscated email patterns like [at], (at), &#64;, [dot], (dot)."""
    if not text:
        return ""
    text = text.replace("&#64;", "@").replace("&commat;", "@").replace("&#46;", ".").replace("&period;", ".")
    # Match [at], (at), {at}, [dot], (dot), {dot} with optional surrounding spaces
    text = re.sub(r'\s*\[\s*at\s*\]\s*|\s*\(\s*at\s*\)\s*|\s*\{\s*at\s*\}\s*', '@', text, flags=re.I)
    text = re.sub(r'\s*\[\s*dot\s*\]\s*|\s*\(\s*dot\s*\)\s*|\s*\{\s*dot\s*\}\s*', '.', text, flags=re.I)
    return text

def extract_attr_str(raw_val: object) -> str:
    if isinstance(raw_val, (list, tuple)):
        return str(raw_val[0]) if raw_val else ""
    return str(raw_val) if raw_val is not None else ""

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
    lead_id = lead.get("id") if isinstance(lead, dict) else lead["id"]
    url = (lead.get("website_url") or "").strip()
    business_name = (lead.get("business_name") or "Lead") if isinstance(lead, dict) else "Lead"

    ui.log_audit_start(business_name, url or "N/A")

    # Scheme auto-correction: if url is www.example.com, add https://
    if url and not url.startswith("http://") and not url.startswith("https://"):
        if "." in url and not url.startswith("/"):
            url = "https://" + url

    if not url or not url.startswith("http"):
        # No website to audit - Golden Lead (Auto-routed to Aloria Labs)
        existing_email = lead.get("email") or ""
        db.update_audit(
            lead_id,
            email=existing_email,
            audit_summary="★ Golden Lead (No Website) - Assigned to Aloria Labs for Web Development & Direct Booking Platform.",
            business_id="aloria_labs"
        )
        return {"id": lead_id, "email": existing_email or None, "audit": "Golden Lead (No Website)", "lead": lead}

    discovered_emails = set()
    vulnerabilities = []
    response_time = 0.0
    session = get_shared_session()

    try:
        start_t = time.time()
        resp = session.get(url, headers=HEADERS, timeout=4.0, verify=False, allow_redirects=True)
        response_time = round(time.time() - start_t, 2)

        if resp.status_code != 200:
            vulnerabilities.append(f"Server returned HTTP {resp.status_code} error status")

        if response_time > 2.5:
            vulnerabilities.append(f"Slow server response latency ({response_time}s)")

        # Content-Type / File size safety guard: Only parse HTML/text, skip binary blobs
        content_type = resp.headers.get("content-type", "").lower()
        if content_type and not any(t in content_type for t in ["text", "html", "json", "xml"]):
            vulnerabilities.append("Non-HTML response content")
            db.update_audit(lead_id, email="", audit_summary="Non-HTML response")
            return {"id": lead_id, "email": None, "audit": "Non-HTML response", "lead": lead}

        # Truncate to first 1MB to protect memory
        resp_text = resp.text[:1000000] if resp.text else ""
        soup = BeautifulSoup(resp_text, "html.parser")

        # 1. Check Mobile Viewport
        viewport = soup.find("meta", attrs={"name": re.compile(r"viewport", re.I)})
        if not viewport:
            vulnerabilities.append("Missing mobile viewport optimization (fails mobile rendering)")

        # 2. Check SSL
        if not url.startswith("https://"):
            vulnerabilities.append("Non-secure HTTP connection (missing SSL certificate)")

        # 3. Check for modern interactive features
        text_lower = resp_text.lower()
        if "order online" not in text_lower and "book table" not in text_lower and "reservation" not in text_lower:
            vulnerabilities.append("Lacks automated online booking or order system")

        # 4. Extract Emails from Schema.org / JSON-LD / Meta tags
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                import json as pyjson
                raw_script = (script.get_text() or script.string or "").strip()
                if not raw_script:
                    continue
                s_data = pyjson.loads(raw_script)
                def _find_emails_in_json(obj):
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            if str(k).lower() in ["email", "telephone"]:
                                if isinstance(v, str) and "@" in v:
                                    cl = clean_email(v)
                                    if cl: discovered_emails.add(cl)
                            _find_emails_in_json(v)
                    elif isinstance(obj, list):
                        for item in obj:
                            _find_emails_in_json(item)
                    elif isinstance(obj, str) and "@" in obj:
                        for em in EMAIL_REGEX.findall(obj):
                            cl = clean_email(em)
                            if cl: discovered_emails.add(cl)
                _find_emails_in_json(s_data)
            except Exception:
                pass

        for meta_tag in soup.find_all("meta"):
            content = extract_attr_str(meta_tag.get("content"))
            if "@" in content:
                for em in EMAIL_REGEX.findall(content):
                    cl = clean_email(em)
                    if cl: discovered_emails.add(cl)

        # 5. Extract Emails from Homepage Mailto Links
        for mailto in soup.select('a[href^="mailto:"]'):
            raw_href = mailto.get("href")
            href_val = extract_attr_str(raw_href)
            href = href_val.replace("mailto:", "").split("?")[0]
            cleaned = clean_email(href)
            if cleaned:
                discovered_emails.add(cleaned)

        # 6. Extract Emails from Raw & De-obfuscated Homepage Text
        deobf_homepage = deobfuscate_text(resp_text)
        for e in EMAIL_REGEX.findall(deobf_homepage):
            cleaned = clean_email(e)
            if cleaned:
                discovered_emails.add(cleaned)

        # 7. Check Contact / About Pages if no email on homepage (Top 2 distinct pages, 3.0s timeout)
        if not discovered_emails:
            contact_links = []
            seen_links = set()
            for a in soup.find_all("a", href=True):
                raw_href = a.get("href")
                href_val = extract_attr_str(raw_href)
                href_lower = href_val.lower()
                if any(k in href_lower for k in ["contact", "about", "reach", "support", "touch", "contactez", "reserva", "booking", "location", "help", "enquiry"]):
                    full_url = urljoin(url, href_val)
                    if full_url not in seen_links and full_url != url:
                        seen_links.add(full_url)
                        contact_links.append(full_url)

            for c_url in contact_links[:2]:
                try:
                    c_resp = session.get(c_url, headers=HEADERS, timeout=3.0, verify=False, allow_redirects=True)
                    if c_resp.status_code == 200:
                        c_text = c_resp.text[:500000] if c_resp.text else ""
                        c_soup = BeautifulSoup(c_text, "html.parser")
                        for mailto in c_soup.select('a[href^="mailto:"]'):
                            raw_href = mailto.get("href")
                            href_val = extract_attr_str(raw_href)
                            href = href_val.replace("mailto:", "").split("?")[0]
                            cleaned = clean_email(href)
                            if cleaned:
                                discovered_emails.add(cleaned)
                        deobf_contact = deobfuscate_text(c_text)
                        for e in EMAIL_REGEX.findall(deobf_contact):
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
    Parallelized Ultra-Lightweight Website Auditor:
    Uses ThreadPoolExecutor with up to 100 concurrent lightweight Python workers (~1MB RAM each).
    Scrapes deep website data, de-obfuscates text, and performs live DNS MX checks.
    """
    pending = db.get_pending_audits(business_id=business_id, limit=limit)
    if not pending:
        if on_step:
            on_step("All discovered leads are already audited. 0 pending candidate websites in queue.")
        return []

    max_auditors = getattr(config, "AUDITOR_WORKERS", 100)
    workers = min(max_auditors, len(pending))
    print(f"  {ui.C_BLUE}[⚡ 100-WORKER LIGHTWEIGHT AUDITOR]{ui.RESET} Inspecting {ui.C_WHITE}{len(pending)}{ui.RESET} websites concurrently ({workers} active workers, ~1MB RAM each)...")
    if on_step:
        on_step(f"Identified {len(pending)} pending candidate websites. Initializing {workers} concurrent lightweight audit workers...")

    results = []
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
                if on_step and isinstance(res, dict):
                    lead_val = res.get("lead")
                    b_name = lead_val.get("business_name", "Lead") if isinstance(lead_val, dict) else "Lead"
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
