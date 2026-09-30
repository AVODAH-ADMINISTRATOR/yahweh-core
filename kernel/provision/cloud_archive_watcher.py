import os
import sys
import time
import argparse
import hashlib
from pathlib import Path
from send2trash import send2trash

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("Please install watchdog: pip install watchdog")
    sys.exit(1)

# --- CLOUD CONFIGURATION ---
CLOUDS = {
    "gdrive": {
        "enabled": True,   # already on
        "folder_path": "AutoArchive",
    },
    "s3": {
        "enabled": True,  # set to True
        "bucket": "my-bucket",
        "prefix": "archive/",
        # it uses your AWS keys from env or ~/.aws/credentials
    },
    "dropbox": {
        "enabled": True,
        "access_token": "sl.XXXX...",
        "folder_path": "/AutoArchive",
    }
}

DELETE_POLICY = "ALL"  # or "ANY" = delete if at least 1 cloud succeeds
# ---------------------------

# Cloud Imports
if CLOUDS["gdrive"]["enabled"]:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    
    SCOPES = ["https://www.googleapis.com/auth/drive"]
    CREDENTIALS_FILE = "credentials.json"
    TOKEN_FILE = "token.json"

if CLOUDS["s3"]["enabled"]:
    import boto3

if CLOUDS["dropbox"]["enabled"]:
    import dropbox

def get_gdrive_service():
    if not CLOUDS["gdrive"]["enabled"]: return None
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"ERROR: {CREDENTIALS_FILE} not found for Google Drive auth.")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("drive", "v3", credentials=creds)

def ensure_gdrive_folder(service, drive_path, root_id="root"):
    if not drive_path or drive_path in (".", "/", "\\"): return root_id
    parts = [p for p in Path(drive_path.replace("\\", "/")).parts if p and p not in ("/", "\\")]
    current_id = root_id
    for part in parts:
        q = f"name='{part}' and '{current_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        resp = service.files().list(q=q, fields="files(id)").execute()
        if resp["files"]:
            current_id = resp["files"][0]["id"]
        else:
            meta = {"name": part, "mimeType": "application/vnd.google-apps.folder", "parents": [current_id]}
            current_id = service.files().create(body=meta, fields="id").execute()["id"]
    return current_id

def upload_gdrive(service, local_path: Path, target_dir: str):
    print(f"  [GDrive] Uploading {local_path.name}...")
    parent_id = ensure_gdrive_folder(service, target_dir)
    
    q = f"name='{local_path.name}' and '{parent_id}' in parents and trashed=false"
    resp = service.files().list(q=q, fields="files(id)").execute()
    existing = resp.get("files", [])
    
    media = MediaFileUpload(str(local_path), resumable=True)
    if existing:
        service.files().update(fileId=existing[0]["id"], media_body=media).execute()
        print(f"  [GDrive] Updated existing file.")
    else:
        meta = {"name": local_path.name, "parents": [parent_id]}
        service.files().create(body=meta, media_body=media).execute()
        print(f"  [GDrive] Uploaded new file.")
    return True

def upload_s3(local_path: Path, relative_path_str: str):
    bucket = CLOUDS["s3"]["bucket"]
    print(f"  [S3] Uploading {local_path.name} to {bucket}...")
    s3 = boto3.client('s3')
    s3_key = CLOUDS["s3"]["prefix"] + relative_path_str
    s3.upload_file(str(local_path), bucket, s3_key)
    print(f"  [S3] Upload complete.")
    return True

def upload_dropbox(local_path: Path, relative_path_str: str):
    print(f"  [Dropbox] Uploading {local_path.name}...")
    dbx = dropbox.Dropbox(CLOUDS["dropbox"]["access_token"])
    dbx_path = CLOUDS["dropbox"]["folder_path"] + "/" + relative_path_str
    dbx_path = dbx_path.replace("//", "/")
    if not dbx_path.startswith("/"): dbx_path = "/" + dbx_path
    
    with open(local_path, "rb") as f:
        dbx.files_upload(f.read(), dbx_path, mute=True, mode=dropbox.files.WriteMode.overwrite)
    print(f"  [Dropbox] Upload complete.")
    return True

def process_file(local_path: Path, watch_folder: Path, gdrive_service, dry_run: bool):
    try:
        time.sleep(1)
        if not local_path.exists() or not local_path.is_file():
            return
            
        rel_path_str = str(local_path.relative_to(watch_folder)).replace("\\", "/")
        print(f"\nProcessing: {rel_path_str}")
        
        if dry_run:
            print(f"  [DRY RUN] Would upload {local_path.name} to enabled cloud services.")
            print(f"  [DRY RUN] Would evaluate DELETE_POLICY ({DELETE_POLICY}) and send to trash if met.")
            return

        upload_results = {}
        
        if CLOUDS["gdrive"]["enabled"] and gdrive_service:
            try:
                target_dir = CLOUDS["gdrive"]["folder_path"]
                if local_path.parent != watch_folder:
                    target_dir = str(Path(target_dir) / local_path.relative_to(watch_folder).parent).replace("\\", "/")
                upload_results["gdrive"] = upload_gdrive(gdrive_service, local_path, target_dir)
            except Exception as e:
                print(f"  [GDrive Error] {e}")
                upload_results["gdrive"] = False
                
        if CLOUDS["s3"]["enabled"]:
            try:
                upload_results["s3"] = upload_s3(local_path, rel_path_str)
            except Exception as e:
                print(f"  [S3 Error] {e}")
                upload_results["s3"] = False
                
        if CLOUDS["dropbox"]["enabled"]:
            try:
                upload_results["dropbox"] = upload_dropbox(local_path, rel_path_str)
            except Exception as e:
                print(f"  [Dropbox Error] {e}")
                upload_results["dropbox"] = False

        if not upload_results:
            print("  [Warning] No cloud services enabled in configuration. Skipping upload.")
            return

        # Evaluate DELETE_POLICY
        should_delete = False
        if DELETE_POLICY == "ALL":
            should_delete = all(upload_results.values())
        elif DELETE_POLICY == "ANY":
            should_delete = any(upload_results.values())

        if should_delete:
            print(f"  [TRASH] Deletion policy ({DELETE_POLICY}) met. Moving local file to recycle bin: {local_path}")
            send2trash(str(local_path))
        else:
            print(f"  [KEEP] Deletion policy ({DELETE_POLICY}) NOT met. Keeping local file.")
            
    except Exception as e:
        print(f"  [Error] Failed to process {local_path}: {e}")

class ArchiveEventHandler(FileSystemEventHandler):
    def __init__(self, watch_folder: Path, gdrive_service, dry_run: bool):
        self.watch_folder = watch_folder
        self.gdrive_service = gdrive_service
        self.dry_run = dry_run

    def on_created(self, event):
        if not event.is_directory:
            process_file(Path(event.src_path), self.watch_folder, self.gdrive_service, self.dry_run)

def scan_existing_files(watch_folder: Path, gdrive_service, dry_run: bool):
    print(f"\n--- Scanning existing files in {watch_folder} ---")
    for filepath in watch_folder.rglob("*"):
        if filepath.is_file():
            process_file(filepath, watch_folder, gdrive_service, dry_run)
    print("--- Finished scanning existing files ---\n")

def main():
    parser = argparse.ArgumentParser(description="Watch a folder and upload new files to cloud archives.")
    parser.add_argument("--watch-folder", type=str, required=True, help="Folder to watch for incoming files.")
    parser.add_argument("--dry-run", action="store_true", help="Do not upload or delete, just print actions.")
    parser.add_argument("--scan-existing", action="store_true", help="Scan and process existing files in the folder before watching.")
    args = parser.parse_args()

    watch_folder = Path(args.watch_folder).resolve()
    if not watch_folder.exists() or not watch_folder.is_dir():
        print(f"Error: Watch folder {watch_folder} does not exist or is not a directory.")
        sys.exit(1)

    print("Initializing Cloud Archive Watcher...")
    
    gdrive_service = None
    if CLOUDS["gdrive"]["enabled"]:
        print("Authenticating with Google Drive...")
        gdrive_service = get_gdrive_service()
        print("Google Drive Ready.")
    
    if CLOUDS["s3"]["enabled"]: print("AWS S3 Uploading ENABLED.")
    if CLOUDS["dropbox"]["enabled"]: print("Dropbox Uploading ENABLED.")

    if args.scan_existing:
        scan_existing_files(watch_folder, gdrive_service, args.dry_run)

    print(f"\nStarting watcher on: {watch_folder}")
    if args.dry_run:
        print("!!! RUNNING IN DRY-RUN MODE (No files will be uploaded or deleted) !!!")

    event_handler = ArchiveEventHandler(watch_folder, gdrive_service, args.dry_run)
    observer = Observer()
    observer.schedule(event_handler, str(watch_folder), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping watcher...")
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
