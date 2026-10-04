import os
import sys
import time
import zipfile
import urllib.request
from pathlib import Path
from ftplib import FTP, FTP_TLS

DEPLOY_SECRET = "shriyansh0402_aloria_secure_deploy_2026"
LIVE_DEPLOY_URL = f"https://alorialabs.in/api_deploy.php?token={DEPLOY_SECRET}"
CHROME_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

def build_zip(source_dir, output_zip):
    source_dir = Path(source_dir)
    output_zip = Path(output_zip)
    if output_zip.exists():
        output_zip.unlink()
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                fp = Path(root) / file
                rel = fp.relative_to(source_dir)
                z.write(fp, arcname=str(rel).replace("\\", "/"))
    print(f"Built {output_zip.name}: {output_zip.stat().st_size} bytes")

def get_ftp(host, user, password):
    print(f"Connecting to FTP ({host}:21)...")
    try:
        ftp = FTP(timeout=45)
        ftp.connect(host, 21)
        ftp.login(user, password)
        ftp.set_pasv(True)
        print("Connected via standard FTP.")
        return ftp
    except Exception as e:
        print(f"Standard FTP failed: {e}. Trying FTPS...")
        ftp = FTP_TLS(timeout=45)
        ftp.connect(host, 21)
        ftp.login(user, password)
        ftp.set_pasv(True)
        return ftp

def main():
    host = os.environ.get("FTP_SERVER") or os.environ.get("FTP_HOST")
    user = os.environ.get("FTP_USERNAME") or os.environ.get("FTP_USER")
    password = os.environ.get("FTP_PASSWORD") or os.environ.get("FTP_PASS")
    ftp_dir = os.environ.get("FTP_DIR") or "public_html"

    if not host or not user or not password:
        print("ERROR: Missing FTP credentials.")
        sys.exit(1)

    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("ERROR: dist directory missing.")
        sys.exit(1)

    # 1. Build deploy.zip
    deploy_zip = Path("deploy.zip")
    build_zip(dist_dir, deploy_zip)

    # 2. Build aloria_python_backend.zip
    pkg_dir = Path("backend_cpanel_pkg")
    backend_zip = Path("aloria_python_backend.zip")
    if pkg_dir.exists():
        build_zip(pkg_dir, backend_zip)

    # 3. Connect to FTP & upload to public_html
    ftp = get_ftp(host, user, password)
    try:
        ftp.cwd(ftp_dir)
    except Exception:
        ftp.cwd("public_html")

    # Upload api_deploy.php
    api_deploy_file = Path("public/api_deploy.php")
    if api_deploy_file.exists():
        print("Uploading api_deploy.php ...")
        with open(api_deploy_file, "rb") as f:
            ftp.storbinary("STOR api_deploy.php", f, blocksize=4096)

    # Upload deploy.zip
    print(f"Uploading {deploy_zip.name} ...")
    with open(deploy_zip, "rb") as f:
        ftp.storbinary(f"STOR {deploy_zip.name}", f, blocksize=8192)

    # Upload aloria_python_backend.zip
    if backend_zip.exists():
        print(f"Uploading {backend_zip.name} ...")
        with open(backend_zip, "rb") as f:
            ftp.storbinary(f"STOR {backend_zip.name}", f, blocksize=8192)

    try:
        ftp.quit()
    except Exception:
        pass

    # 4. Trigger server-side extraction
    print("\nTriggering server-side extraction via HTTPS...")
    req = urllib.request.Request(
        LIVE_DEPLOY_URL,
        headers={"User-Agent": CHROME_UA, "X-Aloria-Deploy-Key": DEPLOY_SECRET}
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read().decode("utf-8")
                print("Extraction response:", body)
                if r.status == 200:
                    print("✅ Extraction complete!")
                    break
        except Exception as e:
            print(f"Attempt {attempt+1} notice: {e}")
            time.sleep(2)

    # Cleanup local zips
    deploy_zip.unlink(missing_ok=True)
    print("Deployment finished successfully!")

if __name__ == "__main__":
    main()
