import urllib.request
import time
import zipfile
import os
from pathlib import Path

# Package dist
dist_dir = Path("dist")
zip_path = Path("dist_deploy_package.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(dist_dir):
        for file in files:
            fp = Path(root) / file
            rel = fp.relative_to(dist_dir)
            zipf.write(fp, arcname=str(rel).replace("\\", "/"))

print(f"Packaged dist: {zip_path.stat().st_size} bytes")

DEPLOY_SECRET = "shriyansh0402_aloria_secure_deploy_2026"
LIVE_DEPLOY_URL = "https://alorialabs.in/api_deploy.php"
ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

boundary = f"----AloriaBoundary{int(time.time())}"
crlf = b"\r\n"
parts = []

parts.append(b"--" + boundary.encode() + crlf)
parts.append(b'Content-Disposition: form-data; name="token"' + crlf + crlf)
parts.append(DEPLOY_SECRET.encode() + crlf)

parts.append(b"--" + boundary.encode() + crlf)
parts.append(b'Content-Disposition: form-data; name="deploy_zip"; filename="deploy.zip"' + crlf)
parts.append(b"Content-Type: application/zip" + crlf + crlf)
with open(zip_path, "rb") as f:
    parts.append(f.read())
parts.append(crlf + b"--" + boundary.encode() + b"--" + crlf)

body = b"".join(parts)

req = urllib.request.Request(
    LIVE_DEPLOY_URL,
    data=body,
    headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Content-Length": str(len(body)),
        "X-Aloria-Deploy-Key": DEPLOY_SECRET,
        "User-Agent": ua
    },
    method="POST"
)

with urllib.request.urlopen(req, timeout=30) as r:
    print("STATUS:", r.status)
    print("RESPONSE:", r.read().decode("utf-8"))
