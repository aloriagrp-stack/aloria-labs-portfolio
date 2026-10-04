import os
import sys
import time
from pathlib import Path
from ftplib import FTP, FTP_TLS, error_perm, error_temp

def get_ftp_connection(host, user, password):
    print(f"Connecting to FTP server: {host} ...")
    # Try FTPS first, fallback to FTP
    try:
        print("Attempting secure FTPS connection...")
        ftp = FTP_TLS(timeout=60)
        ftp.connect(host, 21)
        ftp.login(user, password)
        ftp.prot_p()  # Switch data connection to secure TLS
        ftp.set_pasv(True)
        print("FTPS connected and authenticated successfully!")
        return ftp
    except Exception as e:
        print(f"FTPS failed or not supported ({e}). Falling back to standard FTP...")
        try:
            ftp = FTP(timeout=60)
            ftp.connect(host, 21)
            ftp.login(user, password)
            ftp.set_pasv(True)
            print("Standard FTP connected and authenticated successfully!")
            return ftp
        except Exception as e2:
            print(f"Standard FTP connection failed: {e2}")
            raise

def navigate_to_target_dir(ftp, ftp_dir):
    current_pwd = ftp.pwd()
    print(f"Current FTP directory: {current_pwd}")
    
    target = (ftp_dir or "").strip()
    if target and target != "./" and target != "/":
        print(f"Navigating to specified FTP_DIR: {target}")
        ftp.cwd(target)
        print(f"Working directory is now: {ftp.pwd()}")
        return

    # Auto-detect public_html
    try:
        items = ftp.nlst()
        if "public_html" in items:
            print("Detected 'public_html' directory. Navigating into public_html ...")
            ftp.cwd("public_html")
            print(f"Working directory is now: {ftp.pwd()}")
        else:
            print("Already inside target web root (no public_html subfolder detected).")
    except Exception as e:
        print(f"Notice during directory listing ({e}), staying in current directory.")

def ensure_remote_dir(ftp, remote_path):
    parts = remote_path.replace("\\", "/").strip("/").split("/")
    current = ""
    for part in parts:
        if not part:
            continue
        current = f"{current}/{part}" if current else part
        try:
            ftp.mkd(current)
            print(f"  Created remote directory: {current}")
        except (error_perm, error_temp):
            pass  # Directory already exists

def upload_file_with_retry(get_conn_fn, current_ftp_ref, local_file, remote_file, max_retries=3):
    ftp = current_ftp_ref[0]
    for attempt in range(1, max_retries + 1):
        try:
            with open(local_file, "rb") as f:
                ftp.storbinary(f"STOR {remote_file}", f, blocksize=32768)
            return True
        except Exception as e:
            print(f"  [Attempt {attempt}/{max_retries} failed for {remote_file}: {e}]")
            if attempt == max_retries:
                raise
            time.sleep(2)
            try:
                ftp = get_conn_fn()
                current_ftp_ref[0] = ftp
            except Exception as reconn_err:
                print(f"  Reconnect failed: {reconn_err}")
                time.sleep(3)

def main():
    host = os.environ.get("FTP_SERVER") or os.environ.get("FTP_HOST")
    user = os.environ.get("FTP_USERNAME") or os.environ.get("FTP_USER")
    password = os.environ.get("FTP_PASSWORD") or os.environ.get("FTP_PASS")
    ftp_dir = os.environ.get("FTP_DIR")

    if not host or not user or not password:
        print("ERROR: Missing FTP credentials in environment variables (FTP_SERVER, FTP_USERNAME, FTP_PASSWORD).")
        sys.exit(1)

    dist_dir = Path("dist")
    if not dist_dir.exists():
        print("ERROR: dist directory does not exist. Run 'npm run build' first.")
        sys.exit(1)

    def create_conn():
        conn = get_ftp_connection(host, user, password)
        navigate_to_target_dir(conn, ftp_dir)
        return conn

    ftp = create_conn()
    ftp_ref = [ftp]

    print("\nStarting file upload to cPanel ...")
    upload_count = 0
    start_time = time.time()

    # Collect all directories and files to deploy
    all_files = []
    all_dirs = set()

    for root, dirs, files in os.walk(dist_dir):
        rel_root = Path(root).relative_to(dist_dir)
        if str(rel_root) != ".":
            all_dirs.add(str(rel_root).replace("\\", "/"))
        for file in files:
            full_path = Path(root) / file
            rel_file = full_path.relative_to(dist_dir)
            all_files.append((full_path, str(rel_file).replace("\\", "/")))

    # Create directories first
    for d in sorted(all_dirs):
        ensure_remote_dir(ftp_ref[0], d)

    # Upload all files
    total_files = len(all_files)
    for idx, (local_path, remote_path) in enumerate(all_files, 1):
        size_kb = local_path.stat().st_size / 1024
        print(f"[{idx}/{total_files}] Uploading {remote_path} ({size_kb:.1f} KB) ...")
        upload_file_with_retry(create_conn, ftp_ref, local_path, remote_path)
        upload_count += 1

    try:
        ftp_ref[0].quit()
    except Exception:
        pass

    elapsed = time.time() - start_time
    print(f"\n=======================================================")
    print(f"🎉 CPANEL DEPLOYMENT SUCCESSFUL: {upload_count} files uploaded in {elapsed:.1f}s")
    print(f"=======================================================\n")

if __name__ == "__main__":
    main()
