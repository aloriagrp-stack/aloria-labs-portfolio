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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
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
            max_retries=0,
            pool_block=False
        )
        _SHARED_SESSION.mount("http://", adapter)
        _SHARED_SESSION.mount("https://", adapter)
    return _SHARED_SESSION

def reset_shared_session():
    """Recycles HTTP sessions and socket pools to eliminate socket buildup and TIME_WAIT stalls on Windows."""
    global _SHARED_SESSION
    if _SHARED_SESSION is not None:
        try:
            _SHARED_SESSION.close()
        except Exception:
            pass
        _SHARED_SESSION = None

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
    Super Intelligence clean email function.
    Routes through email_verifier to eliminate code artifacts, framework assets,
    while permitting all genuine business emails (Gmail, Yahoo, Outlook, custom domains).
    """
    if not email_str:
        return None
    cleaned = email_verifier.clean_syntax(str(email_str))
    if not cleaned:
        return None
    # Check blacklist table - never accept blacklisted email
    if db.is_email_blacklisted(cleaned):
        return None
    return cleaned

def hunt_email_via_search_footprint(business_name: str, city: str = "", website_url: str = "") -> list:
    """
    Super Intelligence Search Footprint Fallback Engine:
    When a website has obfuscated emails, dynamic JS forms, or no direct mailto links,
    this engine queries search footprints to discover verified reservations/official inboxes.
    """
    found = []
    if not business_name or len(business_name.strip()) < 3:
        return found

    domain = ""
    if website_url:
        try:
            from urllib.parse import urlparse
            p = urlparse(website_url if website_url.startswith("http") else "https://" + website_url)
            domain = p.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            domain = domain.split(":")[0]
        except Exception:
            domain = ""

    queries = []
    if domain and not any(bad in domain for bad in ["google.", "facebook.", "instagram.", "tripadvisor."]):
        queries.append(f'"{domain}" (email OR "reservations@" OR "info@" OR "booking@")')
    clean_b = re.sub(r'[^\w\s]', ' ', business_name).strip()
    loc = f'"{city}"' if city else ""
    queries.append(f'"{clean_b}" {loc} ("reservations@" OR "info@" OR "@gmail.com" OR "contact@")')

    session = get_shared_session()
    for q in queries[:2]:
        try:
            import urllib.parse
            encoded = urllib.parse.quote_plus(q)
            # Try Bing search first
            search_url = f"https://www.bing.com/search?q={encoded}&count=15"
            r = session.get(search_url, headers=HEADERS, timeout=(3.5, 6.0))
            if r.status_code == 200:
                bs = BeautifulSoup(r.text, "html.parser")
                for s in bs(["script", "style", "svg", "noscript"]):
                    s.decompose()
                text = deobfuscate_text(bs.get_text())
                for match in EMAIL_REGEX.findall(text):
                    cl = clean_email(match)
                    if cl and not any(bad in cl for bad in ["bing", "microsoft", "google", "example", "domain.com", "w3.org"]):
                        found.append(cl)

            # DuckDuckGo HTML fallback if Bing returned 0 emails
            if not found:
                ddg_url = f"https://html.duckduckgo.com/html/?q={encoded}"
                r_ddg = session.get(ddg_url, headers=HEADERS, timeout=(3.5, 6.0))
                if r_ddg.status_code == 200:
                    bs_d = BeautifulSoup(r_ddg.text, "html.parser")
                    for s in bs_d(["script", "style", "svg", "noscript"]):
                        s.decompose()
                    text_d = deobfuscate_text(bs_d.get_text())
                    for match in EMAIL_REGEX.findall(text_d):
                        cl = clean_email(match)
                        if cl and not any(bad in cl for bad in ["duckduckgo", "google", "example", "domain.com", "w3.org"]):
                            found.append(cl)

            if found:
                break
        except Exception:
            continue
    return found

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

    # STRICT GOVERNMENT & SYSTEM DOMAIN SHIELD: Reject any government domain immediately
    url_lower = (url or "").lower()
    if any(g in url_lower for g in [".gov.in", ".nic.in", "gov.in", "nic.in", ".mil.in"]):
        db.mark_lead_invalid(lead_id, reason="Rejected Government / Public Sector Domain")
        return {"id": lead_id, "email": None, "audit": "Rejected Govt Domain", "lead": lead}

    # Scheme auto-correction: if url is www.example.com, add https://
    if url and not url.startswith("http://") and not url.startswith("https://"):
        if "." in url and not url.startswith("/"):
            url = "https://" + url

    if not url or not url.startswith("http"):
        # Check if lead already has a verified email from Google Maps listing
        existing_email = (lead.get("email") or "").strip()
        if existing_email:
            verified = clean_and_verify_email(existing_email, check_mx=True)
            if verified:
                db.update_audit(
                    lead_id,
                    email=verified,
                    audit_summary="★ Verified direct inbox captured from Google Maps listing ✓",
                    business_id=lead.get("business_id", "gethotelstays")
                )
                return {"id": lead_id, "email": verified, "audit": "Google Maps Verified Inbox", "lead": lead}
        
        # Super Intelligence Footprint hunt for leads without website
        f_emails = hunt_email_via_search_footprint(business_name, lead.get("city", ""), "")
        for f_em in f_emails:
            verified = clean_and_verify_email(f_em, check_mx=True)
            if verified:
                db.update_audit(
                    lead_id,
                    email=verified,
                    audit_summary="★ Verified reservations inbox discovered via search footprint ✓",
                    business_id=lead.get("business_id", "gethotelstays")
                )
                return {"id": lead_id, "email": verified, "audit": "Search Verified Inbox", "lead": lead}

        # Otherwise: Lead has No Website & No Email found
        b_id = lead.get("business_id", "gethotelstays")
        summary = f"★ Actionable Lead (No Website) - Assigned to {b_id}."
        db.update_audit(
            lead_id,
            email="",
            audit_summary=summary,
            business_id=b_id
        )
        return {"id": lead_id, "email": None, "audit": summary, "lead": lead}

    discovered_emails = set()
    if lead.get("email"):
        cl_ex = clean_email(lead.get("email"))
        if cl_ex:
            discovered_emails.add(cl_ex)
    vulnerabilities = []
    response_time = 0.0
    session = get_shared_session()

    try:
        start_t = time.time()
        resp = session.get(url, headers=HEADERS, timeout=(3.5, 7.0), verify=False, allow_redirects=True)
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

        # Truncate to first 250KB to protect RAM and accelerate DOM parsing
        resp_text = resp.text[:250000] if resp.text else ""
        soup = BeautifulSoup(resp_text, "html.parser")

        # 1. Check Mobile Viewport
        viewport = soup.find("meta", attrs={"name": re.compile(r"viewport", re.I)})
        if not viewport:
            vulnerabilities.append("Missing mobile viewport optimization (fails mobile rendering)")

        # 2. Check SSL
        if not url.startswith("https://"):
            vulnerabilities.append("Non-secure HTTP connection (missing SSL certificate)")

        # 3. Check Response Latency
        if response_time > 2.0:
            vulnerabilities.append(f"High server response latency ({response_time:.1f}s TTFB — slows mobile loading)")

        # 4. Check for WhatsApp Speed-to-Lead CTA
        has_whatsapp = any(w in resp_text.lower() for w in ["wa.me", "api.whatsapp.com", "whatsapp.com/send", "whatsapp"])
        if not has_whatsapp:
            vulnerabilities.append("Missing direct WhatsApp speed-to-lead channel (leads bounce before inquiry)")

        # 5. Check for automated self-serve booking or estimate calculator
        text_lower = resp_text.lower()
        has_interactive = any(b in text_lower for b in ["appointment", "consultation", "estimate", "calculator", "booking", "book now", "reservation", "order online"])
        if not has_interactive:
            vulnerabilities.append("Lacks automated self-serve booking or instant appointment qualification")

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
                link_text = a.get_text().strip().lower()
                if any(k in href_lower or k in link_text for k in ["contact", "about", "reach", "support", "touch", "contactez", "reserva", "booking", "location", "help", "enquiry"]):
                    full_url = urljoin(url, href_val)
                    if full_url not in seen_links and full_url != url:
                        seen_links.add(full_url)
                        contact_links.append(full_url)

            # Probe extended contact, about, and reservation endpoints
            for default_path in [
                "/contact", "/contact-us", "/contactus", "/reach-us", 
                "/about", "/about-us", "/location", "/contact.html", 
                "/contact-us.html", "/contact.php", "/enquiry", "/reservations"
            ]:
                full_url = urljoin(url, default_path)
                if full_url not in seen_links and full_url != url:
                    seen_links.add(full_url)
                    contact_links.append(full_url)

            for c_url in contact_links[:4]:
                try:
                    c_resp = session.get(c_url, headers=HEADERS, timeout=(3.0, 5.0), verify=False, allow_redirects=True)
                    if c_resp.status_code == 200:
                        c_text = c_resp.text[:150000] if c_resp.text else ""
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

        # 8. SUPER INTELLIGENCE SEARCH FOOTPRINT FALLBACK
        # If no email was exposed on website DOM or contact pages, search indexed web footprints
        if not discovered_emails:
            try:
                footprint_emails = hunt_email_via_search_footprint(business_name, lead.get("city", ""), url)
                for f_em in footprint_emails:
                    cl = clean_email(f_em)
                    if cl:
                        discovered_emails.add(cl)
            except Exception:
                pass

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

def audit_pending_leads(limit=20, business_id=None, on_step=None, should_stop=None, lead_ids=None):
    """
    Parallelized Ultra-Lightweight Website Auditor:
    Uses ThreadPoolExecutor with up to 100 concurrent lightweight Python workers (~1MB RAM each).
    Scrapes deep website data, de-obfuscates text, and performs live DNS MX checks.
    """
    pending = db.get_pending_audits(business_id=business_id, limit=limit, lead_ids=lead_ids)
    if not pending:
        if on_step:
            on_step("All discovered leads are already audited. 0 pending candidate websites in queue.")
        return []

    max_auditors = getattr(config, "AUDITOR_WORKERS", 25)
    workers = min(max_auditors, len(pending))
    print(f"  {ui.C_BLUE}[⚡ LOW-RAM HIGH-SPEED AUDITOR]{ui.RESET} Inspecting {ui.C_WHITE}{len(pending)}{ui.RESET} websites concurrently ({workers} active workers)...")
    if on_step:
        on_step(f"Identified {len(pending)} pending candidate websites. Initializing {workers} concurrent low-RAM audit workers...")

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
    
    # Recycle session pools and force garbage collection to prevent memory/socket leaks on Windows
    reset_shared_session()
    import gc
    gc.collect()

    return results

if __name__ == "__main__":
    audit_pending_leads(limit=5)
