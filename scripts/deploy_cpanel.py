import os
import sys
import time
import zipfile
import urllib.request
import urllib.parse
from pathlib import Path
from ftplib import FTP, FTP_TLS, error_perm, error_temp

DEPLOY_SECRET = "shriyansh0402_aloria_secure_deploy_2026"
LIVE_DEPLOY_URL = "https://alorialabs.in/api_deploy.php"

def build_zip_package(dist_dir, output_zip_path):
    print(f"Packaging {dist_dir} into {output_zip_path} ...")
    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(dist_dir)
                zipf.write(full_path, arcname=str(rel_path).replace("\\", "/"))
    size_kb = output_zip_path.stat().st_size / 1024
    print(f"Package created: {size_kb:.1f} KB")

def try_https_deploy(zip_path):
    print(f"\nChecking HTTPS deployment endpoint: {LIVE_DEPLOY_URL} ...")
    try:
        # Test if endpoint is active
        req = urllib.request.Request(
            f"{LIVE_DEPLOY_URL}?token={DEPLOY_SECRET}",
            headers={"User-Agent": "Aloria-GitHub-Deployer/1.0", "X-Aloria-Deploy-Key": DEPLOY_SECRET}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                print("HTTPS Deploy Endpoint is ONLINE! Uploading production bundle over HTTPS (Port 443)...")
                
                # Multi-part form upload
                boundary = "----AloriaBoundary" + str(int(time.time()))
                body_parts = []
                
                # Token field
                body_parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"token\"\r\n\r\n{DEPLOY_SECRET}\r\n".encode("utf-8"))
                
                # File field
                body_parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"deploy_zip\"; filename=\"deploy.zip\"\r\nContent-Type: application/zip\r\n\r\n".encode("utf-8"))
                with open(zip_path, "rb") as f:
                    file_content = f.read()
                body_parts.append(file_content)
                body_parts.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
                
                full_body = b"".join(body_parts)
                
                post_req = urllib.request.Request(
                    LIVE_DEPLOY_URL,
                    data=full_body,
                    headers={
                        "Content-Type": f"multipart/form-data; boundary={boundary}",
                        "Content-Length": str(len(full_body)),
                        "X-Aloria-Deploy-Key": DEPLOY_SECRET,
                        "User-Agent": "Aloria-GitHub-Deployer/1.0"
                    }
                )
                with urllib.request.urlopen(post_req, timeout=30) as post_resp:
                    res_body = post_resp.read().decode("utf-8")
                    print(f"Server response: {res_body}")
                    if post_resp.status == 200 and "success" in res_body:
                        print("\n=======================================================")
                        print("🎉 HTTPS CPANEL DEPLOYMENT SUCCESSFUL IN SECONDS!")
                        print("=======================================================\n")
                        return True
    except Exception as e:
        print(f"HTTPS endpoint not ready yet or returned error: {e}")
    return False

def get_ftp_connection(host, user, password):
    print(f"Connecting to FTP server: {host} (port 21)...")
    try:
        ftp = FTP(timeout=30)
        ftp.connect(host, 21)
        ftp.login(user, password)
        ftp.set_pasv(True)
        print("Connected to standard FTP.")
        return ftp
    except Exception as e:
        print(f"Standard FTP connection failed: {e}. Trying FTPS...")
        ftp = FTP_TLS(timeout=30)
        ftp.connect(host, 21)
        ftp.login(user, password)
        ftp.set_pasv(True)
        return ftp

def navigate_to_target_dir(ftp, ftp_dir):
    target = (ftp_dir or "").strip()
    if target and target != "./" and target != "/":
        ftp.cwd(target)
        return
    try:
        items = ftp.nlst()
        if "public_html" in items:
            ftp.cwd("public_html")
            print("Navigated into public_html")
    except Exception:
        pass

def upload_small_file_ftp(ftp, local_file, remote_file):
    with open(local_file, "rb") as f:
        ftp.storbinary(f"STOR {remote_file}", f, blocksize=4096)
    print(f"Uploaded {remote_file} via FTP successfully.")

def main():
    host = os.environ.get("FTP_SERVER") or os.environ.get("FTP_HOST")
    user = os.environ.get("FTP_USERNAME") or os.environ.get("FTP_USER")
    password = os.environ.get("FTP_PASSWORD") or os.environ.get("FTP_PASS")
    ftp_dir = os.environ.get("FTP_DIR")

    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("ERROR: dist directory missing. Run 'npm run build' first.")
        sys.exit(1)

    zip_file = Path("dist_deploy_package.zip")
    build_zip_package(dist_dir, zip_file)

    # Strategy 1: Check if HTTPS deploy receiver is online
    if try_https_deploy(zip_file):
        if zip_file.exists():
            zip_file.unlink()
        sys.exit(0)

    # Strategy 2: If receiver not yet online, bootstrap it via FTP
    print("\nBootstrapping api_deploy.php to cPanel via lightweight FTP (size: ~1.5 KB)...")
    if not host or not user or not password:
        print("ERROR: Missing FTP credentials for bootstrap.")
        sys.exit(1)

    try:
        ftp = get_ftp_connection(host, user, password)
        navigate_to_target_dir(ftp, ftp_dir)
        
        # Upload api_deploy.php (1.5 KB - never hangs on passive ports!)
        api_deploy_file = Path("public/api_deploy.php")
        if api_deploy_file.exists():
            upload_small_file_ftp(ftp, api_deploy_file, "api_deploy.php")
        
        try:
            ftp.quit()
        except Exception:
            pass

        print("Receiver bootstrapped! Retrying HTTPS deployment...")
        time.sleep(2)
        if try_https_deploy(zip_file):
            if zip_file.exists():
                zip_file.unlink()
            sys.exit(0)
    except Exception as e:
        print(f"FTP bootstrap failed: {e}")

    # Strategy 3: Direct FTP upload of the zip package
    try:
        print("\nAttempting direct FTP upload of deploy.zip ...")
        ftp = get_ftp_connection(host, user, password)
        navigate_to_target_dir(ftp, ftp_dir)
        with open(zip_file, "rb") as f:
            ftp.storbinary("STOR deploy.zip", f, blocksize=4096)
        print("Uploaded deploy.zip via FTP. Triggering server-side extraction...")
        ftp.quit()
        
        # Trigger extraction
        req = urllib.request.Request(
            f"{LIVE_DEPLOY_URL}?token={DEPLOY_SECRET}&action=extract_local",
            headers={"User-Agent": "Aloria-GitHub-Deployer/1.0", "X-Aloria-Deploy-Key": DEPLOY_SECRET}
        )
        try:
            urllib.request.urlopen(req, timeout=10)
        except Exception:
            pass
        print("Done!")
    except Exception as e:
        print(f"Fallback direct FTP upload failed: {e}")
        if zip_file.exists():
            zip_file.unlink()
        sys.exit(1)

    if zip_file.exists():
        zip_file.unlink()

if __name__ == "__main__":
    main()
