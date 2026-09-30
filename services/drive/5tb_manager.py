import os
import sys
import argparse
import threading
import hashlib
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

DAILY_LIMIT_BYTES = 700 * (1000**3) # 700 GB

def authenticate():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"ERROR: {CREDENTIALS_FILE} not found. Please download from Google Cloud Console.")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("drive", "v3", credentials=creds)

def get_local_stats(folder: Path):
    total_size = 0
    file_count = 0
    for root, dirs, files in os.walk(folder):
        for f in files:
            fp = os.path.join(root, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
                file_count += 1
    return total_size, file_count

def format_tb(bytes_val):
    return f"{bytes_val / (1000**4):.1f} TB"

def format_gb(bytes_val):
    return f"{bytes_val / (1000**3):.0f} GB"

def md5_of_file(path: Path):
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

def ensure_drive_folder(service, drive_path, root_id="root"):
    if not drive_path or drive_path in (".", "/", "\\"): return root_id
    parts = [p for p in Path(drive_path.replace("\\", "/")).parts if p and p not in ("/", "\\")]
    current_id = root_id
    for part in parts:
        q = f"name='{part}' and '{current_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        resp = service.files().list(q=q, fields="files(id)").execute()
        if resp.get("files"):
            current_id = resp["files"][0]["id"]
        else:
            meta = {"name": part, "mimeType": "application/vnd.google-apps.folder", "parents": [current_id]}
            current_id = service.files().create(body=meta, fields="id").execute()["id"]
    return current_id

class ArchiveManager:
    def __init__(self, service, watch_folder, dry_run=False):
        self.service = service
        self.watch_folder = watch_folder
        self.dry_run = dry_run
        
        self.lock = threading.Lock()
        self.uploaded_bytes_today = 0
        self.limit_reached = False
        
        self.already_uploaded_count = 0
        
        # Cache for folder IDs to reduce API calls
        self.folder_cache = {}
        self.folder_lock = threading.Lock()

    def get_drive_folder_id(self, target_dir_str):
        with self.folder_lock:
            if target_dir_str in self.folder_cache:
                return self.folder_cache[target_dir_str]
        
        # If not in cache, create/ensure it
        folder_id = ensure_drive_folder(self.service, target_dir_str)
        
        with self.folder_lock:
            self.folder_cache[target_dir_str] = folder_id
        return folder_id

    def process_file(self, local_path: Path):
        if self.limit_reached:
            return "LIMIT_REACHED"
            
        file_size = os.path.getsize(local_path)
        
        with self.lock:
            if self.uploaded_bytes_today + file_size > DAILY_LIMIT_BYTES:
                self.limit_reached = True
                return "LIMIT_REACHED"

        rel_path = local_path.relative_to(self.watch_folder)
        target_dir = self.watch_folder.name
        if rel_path.parent != Path("."):
            target_dir = str(Path(target_dir) / rel_path.parent).replace("\\", "/")

        parent_id = self.get_drive_folder_id(target_dir)
        
        # Check if file exists
        q = f"name='{local_path.name}' and '{parent_id}' in parents and trashed=false"
        resp = self.service.files().list(q=q, fields="files(id, md5Checksum, size)").execute()
        existing = resp.get("files", [])
        
        needs_upload = True
        local_md5 = None
        
        if existing:
            drive_file = existing[0]
            drive_size = int(drive_file.get("size", 0))
            if drive_size == file_size:
                # Optional: Strict MD5 check
                # local_md5 = md5_of_file(local_path)
                # if drive_file.get("md5Checksum") == local_md5:
                needs_upload = False
        
        if not needs_upload:
            with self.lock:
                self.already_uploaded_count += 1
            return "SKIPPED"
            
        if self.dry_run:
            print(f"  [DRY RUN] Would upload {local_path.name}")
            return "DRY_RUN"
            
        # Perform upload
        try:
            media = MediaFileUpload(str(local_path), resumable=True)
            if existing:
                self.service.files().update(fileId=existing[0]["id"], media_body=media).execute()
            else:
                meta = {"name": local_path.name, "parents": [parent_id]}
                self.service.files().create(body=meta, media_body=media).execute()
                
            with self.lock:
                self.uploaded_bytes_today += file_size
            return "UPLOADED"
        except Exception as e:
            return f"ERROR: {e}"

def main():
    parser = argparse.ArgumentParser(description="Manage a 5TB Google Drive backup.")
    parser.add_argument("--mode", required=True, choices=["check", "archive"], help="Mode to run the manager in.")
    parser.add_argument("--watch-folder", required=True, help="Local folder to analyze or archive.")
    parser.add_argument("--dry-run", action="store_true", help="Dry run for archive mode.")
    parser.add_argument("--workers", type=int, default=1, help="Number of concurrent upload workers.")
    args = parser.parse_args()

    watch_folder = Path(args.watch_folder).resolve()
    if not watch_folder.exists() or not watch_folder.is_dir():
        print(f"Error: {watch_folder} is not a valid directory.")
        sys.exit(1)

    service = authenticate()
    
    if args.mode == "check":
        print(f"Gathering local stats for {watch_folder}...")
        local_size, local_count = get_local_stats(watch_folder)
        
        print("Querying Google Drive for quota...")
        about = service.about().get(fields="storageQuota").execute()
        quota = about.get("storageQuota", {})
        
        limit = int(quota.get("limit", 0))
        usage = int(quota.get("usage", 0))
        trash = int(quota.get("usageInDriveTrash", 0))
        
        pct_full = (usage / limit) * 100 if limit > 0 else 0
        
        print(f"\n# Output:")
        print(f"# Local: {format_tb(local_size)} / {local_count:,} files")
        
        if trash > 0:
            trash_str = f"{format_gb(trash)} <- free this!"
        else:
            trash_str = "0 GB"
            
        print(f"# Drive: {format_tb(limit)} limit, {format_tb(usage)} used ({pct_full:.0f}% full), Trash: {trash_str}")
        
        gb_per_day = 700
        days = (local_size / (1000**3)) / gb_per_day
        print(f"# Days needed: {days:.1f} days at {gb_per_day}GB/day")

    elif args.mode == "archive":
        print(f"Starting archive process for {watch_folder}")
        if args.dry_run:
            print("!!! RUNNING IN DRY-RUN MODE !!!")
            
        # 1. Gather all files
        all_files = []
        for root, dirs, files in os.walk(watch_folder):
            for f in files:
                fp = Path(root) / f
                if fp.is_file() and not fp.is_symlink():
                    all_files.append(fp)
                    
        total_files = len(all_files)
        print(f"Found {total_files} files locally.")
        
        manager = ArchiveManager(service, watch_folder, args.dry_run)
        
        # 2. Process with workers
        skipped = 0
        uploaded = 0
        
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(manager.process_file, fp): fp for fp in all_files}
            
            for future in tqdm(as_completed(futures), total=total_files, desc="Archiving"):
                fp = futures[future]
                try:
                    res = future.result()
                    if res == "SKIPPED":
                        skipped += 1
                    elif res == "UPLOADED":
                        uploaded += 1
                    elif res == "LIMIT_REACHED":
                        # We hit the limit, pending futures will quickly return LIMIT_REACHED
                        pass
                except Exception as e:
                    print(f"Unhandled error processing {fp.name}: {e}")
                    
        print("\n--- Archive Session Complete ---")
        if skipped > 0:
            print(f"Already uploaded: {skipped} files")
        
        if manager.limit_reached:
            print("Daily upload limit (700GB) reached! Pausing until tomorrow.")
            
        print(f"Files uploaded in this session: {uploaded}")
        print(f"Total bytes transferred today: {format_gb(manager.uploaded_bytes_today)}")

if __name__ == "__main__":
    main()
