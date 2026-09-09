# 🏹 Aloria Hunter — Autonomous B2B Lead Discovery & Cold Outreach Agent

A production-grade Python autonomous agent that hunts local businesses on **Google Maps**, audits their digital infrastructure (or identifies businesses with **zero website presence**), and executes personalized cold email outreach with automated 2-day follow-ups.

---

## ⚡ Key Features

1. **Autonomous Google Maps Screen Controller**:
   - Uses Playwright Chromium to search `"Restaurants in Algiers, Algeria"` (or any country/city/niche).
   - Scrolls the feed, clicks each listing, and extracts name, phone, address, rating, and website status.
2. **Deterministic Empirical Audit Engine**:
   - Tests server response speed / latency.
   - Tests mobile viewport responsiveness (`<meta name="viewport">`).
   - Checks SSL certificate validity (`https`).
   - Scrapes homepage and `/contact` pages for email addresses and contact points.
3. **Branching Value Proposition Pitcher**:
   - **Case A (No Website — Golden Lead)**: Pitches an autonomous website & online ordering platform to capture digital customers.
   - **Case B (Has Website)**: Quotes the exact empirical flaws (slow speed, mobile rendering failure, no online booking).
4. **Automated Follow-up Engine**:
   - Day 0: Initial personalized pitch.
   - Day 2: Polite follow-up bump.
   - Day 4: Final courteous check-in / breakup email.
5. **SQLite State Machine (`hunter.db`)**:
   - Guarantees zero duplicate crawls and zero duplicate emails.
6. **Zero External LLM APIs**:
   - 100% self-contained deterministic Python engineering. No OpenAI/Claude API costs.

---

## 🚀 How to Run

Navigate into the folder:
```bash
cd aloria-hunter
```

### 1. Test Run (Live Visible Screen Control — Watch It Click & Type)
```bash
python runner.py --country "Algeria" --city "Algiers" --niche "Restaurants" --limit 5 --dry-run
```
*(This will launch Chromium on your screen, navigate to Google Maps, type the query, scroll, click the cards, and show you the extracted data in real time without sending emails!)*

### 2. Live Run (Visible Window + Real Email Dispatch)
```bash
python runner.py --country "Algeria" --city "Algiers" --niche "Restaurants" --limit 10
```

### 3. Silent Background Mode (Headless)
```bash
python runner.py --country "Algeria" --city "Algiers" --niche "Restaurants" --limit 20 --headless
```

### 4. 24/7 Daemon Mode (Continuous Autonomous Loop)
```bash
python runner.py --daemon --headless
```

---

## ⚙️ Configuration (`config.py`)

- `DEFAULT_COUNTRY`: Country to target (default: `"Algeria"`).
- `DEFAULT_NICHES`: List of business niches (`["Restaurants", "Hotels", "Cafes", "Dental Clinics", "Real Estate"]`).
- `DEFAULT_CITIES`: Cities to scan (`["Algiers", "Oran", "Constantine", "Annaba"]`).
- `HEADLESS`: `False` (visible screen) or `True` (background).
- `SMTP_CONFIG_PATH`: Automatically loads `alorialabs@gmail.com` credentials from `../smtp_config.json`.
