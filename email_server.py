import http.server
import json
import smtplib
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

CONFIG_FILE = "smtp_config.json"

def load_config():
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except:
        return {"email": "", "password": "", "smtp_server": "smtp.gmail.com", "smtp_port": 587}

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

def send_email(config, to_email, applicant_name, category, team_member, subject=None, html_body=None):
    msg = MIMEMultipart("alternative")
    msg["From"] = f"Aloria Labs <{config['email']}>"
    msg["To"] = to_email

    if subject:
        msg["Subject"] = subject
    else:
        msg["Subject"] = "Your Application Has Been Approved - Aloria Labs"

    if html_body:
        # Use provided HTML body, replace variables if needed
        html = html_body
        text = f"""Dear {applicant_name},

Congratulations! Your application has been approved by Aloria Labs.

Category: {category}
Referred By: {team_member}

Our team will reach out to you shortly with next steps.

Best,
Aloria Labs Team
"""
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))
    else:
        # Default email
        text = f"""Dear {applicant_name},

Congratulations! Your application has been approved by Aloria Labs.

Category: {category}
Referred By: {team_member}

Our team will reach out to you shortly with next steps.

Best,
Aloria Labs Team
"""

        html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: 'Inter', Arial, sans-serif; background: #000; color: #fff; margin: 0; padding: 0;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#000;padding:40px 20px;">
    <tr><td align="center">
      <table width="480" cellpadding="0" cellspacing="0" style="background:#0a0a0a;border:1px solid rgba(255,255,255,0.1);border-radius:16px;padding:40px;">
        <tr><td align="center" style="font-family:'Outfit',Arial,sans-serif;font-size:14px;font-weight:700;letter-spacing:3px;color:#666;padding-bottom:8px;">ALORIA LABS</td></tr>
        <tr><td align="center" style="font-family:'Outfit',Arial,sans-serif;font-size:32px;font-weight:800;color:#fff;padding-bottom:24px;">Application Approved</td></tr>
        <tr><td style="color:#aaa;font-size:15px;line-height:1.6;padding-bottom:20px;">
          Dear <strong style="color:#fff;">{applicant_name}</strong>,
          <br><br>
          Congratulations! Your application has been <strong style="color:#44ff88;">approved</strong> by Aloria Labs.
        </td></tr>
        <tr><td style="padding:16px 20px;background:rgba(255,255,255,0.03);border-radius:10px;margin-bottom:16px;">
          <table width="100%">
            <tr><td style="color:#666;font-size:12px;padding:4px 0;">Category</td><td style="color:#fff;font-size:14px;text-align:right;">{category}</td></tr>
            <tr><td style="color:#666;font-size:12px;padding:4px 0;">Referred By</td><td style="color:#fff;font-size:14px;text-align:right;">{team_member}</td></tr>
          </table>
        </td></tr>
        <tr><td style="color:#888;font-size:14px;line-height:1.6;padding-top:12px;">
          Our team will reach out to you shortly with next steps.
          <br><br>
          Best,<br>
          <strong style="color:#fff;">Aloria Labs Team</strong>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

    server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
    server.starttls()
    server.login(config["email"], config["password"])
    server.sendmail(config["email"], to_email, msg.as_string())
    server.quit()

class Handler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/health":
            self.send_json({"status": "ok"})
        elif parsed.path == "/config":
            cfg = load_config()
            self.send_json({"configured": bool(cfg.get("email") and cfg.get("password"))})
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        data = json.loads(body) if body else {}
        print(f"[EMAIL SERVER] POST {parsed.path} data: {json.dumps({k: v for k, v in data.items() if k != 'password'})}")

        if parsed.path == "/send":
            config = load_config()
            if not config["email"] or not config["password"]:
                self.send_json({"success": False, "error": "SMTP not configured"})
                return
            try:
                send_email(config,
                    to_email=data.get("to_email", ""),
                    applicant_name=data.get("applicant_name", "Applicant"),
                    category=data.get("category", "Application"),
                    team_member=data.get("team_member", "Aloria Labs"),
                    subject=data.get("subject"),
                    html_body=data.get("html_body"))
                self.send_json({"success": True})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})

        elif parsed.path == "/save-config":
            save_config(data)
            self.send_json({"success": True})

        elif parsed.path == "/test":
            config = load_config()
            if not config["email"] or not config["password"]:
                self.send_json({"success": False, "error": "SMTP not configured"})
                return
            try:
                send_email(config, config["email"], "Test User", "Test", "Admin")
                self.send_json({"success": True, "message": f"Test email sent to {config['email']}"})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
        else:
            self.send_error(404)

    def send_json(self, obj):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())

    def log_message(self, format, *args):
        print(f"[EMAIL SERVER] {args[0]} {args[1]} {args[2]}")

if __name__ == "__main__":
    port = 5000
    print(f"Email server running on http://localhost:{port}")
    print(f"Configure SMTP at: POST http://localhost:{port}/save-config")
    print(f"Send email at:    POST http://localhost:{port}/send")
    server = http.server.HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()
