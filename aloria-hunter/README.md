# 🏹 Aloria Hunter — Autonomous B2B Lead Discovery & Cold Outreach Agent

A production-grade Python autonomous agent that hunts local businesses on **Google Maps**, audits their digital infrastructure (or identifies businesses with **zero website presence**), and executes personalized cold email outreach with automated 2-day follow-ups.

---

## ⚡ Key Features

1. **Dual Independent Parallel Autonomous Agents**:
   - **Agent 1: Agent Aloria (Aloria Labs)**: Hunts and audits restaurants, cafes, clinics for web and software modernization pitches.
   - **Agent 2: Agent HotelStays (GetHotelStays)**: Hunts independent hotels, boutique stays, and resorts, pitching partner onboarding for direct guest bookings.
   - **Parallel Multithreaded Execution**: Both agents can run concurrently on background threads with zero cross-blocking and isolated queues.
2. **Local Mobile Command & Chat App (Installable PWA)**:
   - Self-hosted on your machine (FastAPI on port 8000). Zero 3rd party or Telegram dependence.
   - Installable on mobile phones via "Add to Home Screen" as an app.
   - Chat with both agents in real-time, trigger quick action chips (`Hunt`, `Audit`, `Send`, `Follow-up`), view live lead ledger, and stream the terminal console live to your phone.
3. **24/7 Continuous Dual Autopilot**:
   - Automated perpetual wave scheduler that alternates between Aloria Labs and GetHotelStays with safe IP cooldown intervals.
4. **Clean, Uncluttered CLI Terminal Cockpit**:
   - High-contrast, linear console with 1-key business switching (`[1-2]`), real-time pipeline KPIs, and direct wave execution.
5. **Deterministic Audit & Branching Outreach**:
   - Speed/SSL/viewport auditor, no-website golden lead detector, and automated 2-Day/4-Day follow-up engine.

---

## 🚀 How to Run

### 1. Launch Terminal Command Center (PC/Laptop)
```cmd
.\hunt.bat
```
*(Clean terminal menu: Press `1` for Aloria Labs, `2` for GetHotelStays, or `H` to hunt!)*

### 2. Launch Mobile Command App (Control from Phone)
```cmd
.\mobile.bat
```
*(Opens the local server on `http://192.168.43.83:8000`. Open this URL in your phone's browser, tap "Add to Home Screen" to install it as an app, and command both agents from anywhere on your WiFi!)*



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
