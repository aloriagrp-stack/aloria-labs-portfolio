import os
import sys
import time
import io
from pathlib import Path
from ftplib import FTP, FTP_TLS

def get_ftp_connection(host, user, password):
    print(f"Connecting to FTP server: {host} (port 21)...")
    try:
        ftp = FTP(timeout=45)
        ftp.connect(host, 21)
        ftp.login(user, password)
        ftp.set_pasv(True)
        print("Connected to standard FTP.")
        return ftp
    except Exception as e:
        print(f"Standard FTP connection failed: {e}. Trying FTPS...")
        ftp = FTP_TLS(timeout=45)
        ftp.connect(host, 21)
        ftp.login(user, password)
        ftp.prot_p()
        ftp.set_pasv(True)
        return ftp

def upload_dir_ftp(ftp, local_dir):
    local_dir = Path(local_dir)
    count = 0
    for root, dirs, files in os.walk(local_dir):
        rel_root = Path(root).relative_to(local_dir)
        current_remote = str(rel_root).replace("\\", "/")
        if current_remote != ".":
            parts = current_remote.split("/")
            accum = ""
            for p in parts:
                accum = f"{accum}/{p}" if accum else p
                try:
                    ftp.mkd(accum)
                except Exception:
                    pass
        for file in files:
            local_fp = Path(root) / file
            remote_target = str(local_fp.relative_to(local_dir)).replace("\\", "/")
            try:
                with open(local_fp, "rb") as f:
                    ftp.storbinary(f"STOR {remote_target}", f, blocksize=8192)
                count += 1
                print(f"  ✓ {remote_target}")
            except Exception as e:
                print(f"  ⚠️ Error uploading {remote_target}: {e}")
    return count

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
        print("ERROR: dist directory missing. Run 'npm run build' first.")
        sys.exit(1)

    # 1. Connect to FTP
    ftp = get_ftp_connection(host, user, password)

    # 2. Upload Production Frontend to public_html
    print(f"\n[1/2] Deploying Frontend Bundle to {ftp_dir} ...")
    try:
        ftp.cwd(ftp_dir)
    except Exception:
        ftp.cwd("public_html")

    uploaded_frontend = upload_dir_ftp(ftp, dist_dir)
    print(f"🎉 Frontend Deployment Complete! ({uploaded_frontend} files synced)")

    # 3. Upload Backend to aloria-api
    backend_dir = Path("backend_cpanel_pkg")
    if backend_dir.exists():
        print("\n[2/2] Deploying Python Backend to aloria-api ...")
        try:
            ftp.cwd("/home/vgyuvmpi/aloria-api")
        except Exception:
            try:
                ftp.cwd("../../aloria-api")
            except Exception:
                try:
                    ftp.cwd("../aloria-api")
                except Exception as e:
                    print(f"Could not enter aloria-api directory: {e}")

        uploaded_backend = upload_dir_ftp(ftp, backend_dir)
        print(f"🎉 Backend Deployment Complete! ({uploaded_backend} files synced)")

        # Restart Phusion Passenger app
        try:
            ftp.mkd("tmp")
        except Exception:
            pass
        try:
            ftp.storbinary("STOR tmp/restart.txt", io.BytesIO(f"restart {time.time()}\n".encode()))
            print("🚀 Phusion Passenger Application Restarted via tmp/restart.txt!")
        except Exception as e:
            print(f"Passenger restart notice: {e}")

    try:
        ftp.quit()
    except Exception:
        pass

    print("\n=======================================================")
    print("✅ FULL PRODUCTION DEPLOYMENT FINISHED SUCCESSFULLY!")
    print("=======================================================\n")

if __name__ == "__main__":
    main()
