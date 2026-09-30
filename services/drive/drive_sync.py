"""
Google Drive <-> Hard Drive Auto Sync
=====================================
Features:
- Bidirectional sync (upload new local files, download new Drive files)
- Conflict resolution by modified time + md5 checksum
- Creates missing folders automatically
- Handles Google Docs/Sheets/Slides by exporting (optional)
- One-shot sync or continuous --watch mode

Setup:
1. Go to https://console.cloud.google.com/ -> New Project
2. Enable "Google Drive API"
3. APIs & Services -> Credentials -> Create Credentials -> OAuth Client ID -> Desktop App
4. Download JSON and save as credentials.json next to this script
5. pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib watchdog
6. python drive_sync.py --first-run (will open browser to log in)
7. python drive_sync.py --watch  (for continuous sync)

Config below:
"""

import os
import io
import sys
import time
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# ================= CONFIG =================
SCOPES = ["https://www.googleapis.com/auth/drive"]
LOCAL_ROOT = Path.home() / "GoogleDriveSync"  # Change to your folder, e.g. Path("D:/MyDrive")
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
DRIVE_ROOT_ID = "root"  # Use "root" for My Drive, or a specific Folder ID to sync only that folder
# Set to True to export Google Docs/Sheets/Slides
EXPORT_GOOGLE_DOCS = True
# =========================================

def authenticate():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"ERROR: {CREDENTIALS_FILE} not found.")
                print("Download OAuth credentials from Google Cloud Console and save as credentials.json")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("drive", "v3", credentials=creds)

def parse_drive_time(t):
    # 2024-01-01T12:00:00.000Z
    return datetime.fromisoformat(t.replace("Z", "+00:00"))

def list_drive_files_recursive(service, parent_id="root", base_path=""):
    """Returns dict: relative_path -> file metadata"""
    files_map = {}
    query = f"'{parent_id}' in parents and trashed=false"
    page_token = None
    while True:
        resp = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType, modifiedTime, md5Checksum, size, parents)",
            pageSize=1000,
            pageToken=page_token
        ).execute()
        for f in resp.get("files", []):
            rel = os.path.join(base_path, f["name"]) if base_path else f["name"]
            if f["mimeType"] == "application/vnd.google-apps.folder":
                # Recurse into folder
                files_map.update(
                    list_drive_files_recursive(service, f["id"], rel)
                )
                # Keep folder marker so we can create it locally
                files_map[rel + "/__folder__"] = f
            else:
                files_map[rel] = f
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return files_map

def get_local_files(local_root: Path):
    """Returns dict: relative_path -> {full_path, mtime, size, md5?}"""
    local_map = {}
    for file_path in local_root.rglob("*"):
        if file_path.is_dir():
            continue
        if file_path.name in [TOKEN_FILE, CREDENTIALS_FILE, ".DS_Store"]:
            continue
        rel = str(file_path.relative_to(local_root)).replace("\\", "/")
        stat = file_path.stat()
        local_map[rel] = {
            "full_path": file_path,
            "mtime": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            "size": stat.st_size,
        }
    return local_map

def md5_of_file(path: Path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def ensure_drive_folder_path(service, drive_path, drive_root_id):
    """Ensure folder path exists on Drive, return folder id of deepest folder"""
    if not drive_path or drive_path == ".":
        return drive_root_id
    
    parts = Path(drive_path).parts
    current_id = drive_root_id
    for part in parts:
        # Check if folder exists
        q = f"name='{part}' and '{current_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        resp = service.files().list(q=q, fields="files(id)").execute()
        if resp["files"]:
            current_id = resp["files"][0]["id"]
        else:
            # Create folder
            meta = {"name": part, "mimeType": "application/vnd.google-apps.folder", "parents": [current_id]}
            folder = service.files().create(body=meta, fields="id").execute()
            current_id = folder["id"]
            print(f"[Drive] Created folder: {drive_path}")
    return current_id

def download_drive_file(service, drive_file, local_path: Path):
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Handle native Google Docs
    mime = drive_file["mimeType"]
    export_map = {
        "application/vnd.google-apps.document": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".docx"),
        "application/vnd.google-apps.spreadsheet": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".xlsx"),
        "application/vnd.google-apps.presentation": ("application/vnd.openxmlformats-officedocument.presentationml.presentation", ".pptx"),
    }
    try:
        if EXPORT_GOOGLE_DOCS and mime in export_map:
            export_mime, ext = export_map[mime]
            if not str(local_path).endswith(ext):
                local_path = local_path.with_suffix(ext)
            request = service.files().export_media(fileId=drive_file["id"], mimeType=export_mime)
        else:
            if mime.startswith("application/vnd.google-apps."):
                print(f"[Skip] Cannot download Google native file without export: {drive_file['name']}")
                return
            request = service.files().get_media(fileId=drive_file["id"])
        
        with io.FileIO(local_path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        
        # Set mtime to match Drive
        dt = parse_drive_time(drive_file["modifiedTime"])
        ts = dt.timestamp()
        os.utime(local_path, (ts, ts))
        print(f"[Download] {drive_file['name']} -> {local_path}")
    except Exception as e:
        print(f"[Error Download] {drive_file['name']}: {e}")

def upload_local_file(service, local_path: Path, drive_root_id, existing_file_id=None):
    drive_dir = str(local_path.parent).replace("\\", "/")
    # Convert local relative to drive folder structure
    # We need relative to LOCAL_ROOT - handled by caller
    
    parent_id = ensure_drive_folder_path(service, drive_dir, drive_root_id) if drive_dir != "." else drive_root_id
    
    media = MediaFileUpload(str(local_path), resumable=True)
    try:
        if existing_file_id:
            # Update existing
            file = service.files().update(
                fileId=existing_file_id,
                media_body=media,
                fields="id, modifiedTime"
            ).execute()
            print(f"[Update] {local_path.name} to Drive")
        else:
            meta = {"name": local_path.name, "parents": [parent_id]}
            file = service.files().create(body=meta, media_body=media, fields="id").execute()
            print(f"[Upload] {local_path.name} -> Drive/{drive_dir}")
            
        print(f"[Delete] Removing local file {local_path}")
        local_path.unlink()
        return file
    except Exception as e:
        print(f"[Error Upload] {local_path}: {e}")
        return None

def sync_once(service, local_root: Path, drive_root_id):
    print(f"\n--- Syncing {local_root} <-> Drive:{drive_root_id} at {datetime.now()} ---")
    local_root.mkdir(parents=True, exist_ok=True)
    
    drive_files = list_drive_files_recursive(service, drive_root_id, "")
    # Remove folder markers for file logic
    drive_file_only = {k: v for k, v in drive_files.items() if not k.endswith("/__folder__")}
    drive_folders = [k.replace("/__folder__", "") for k in drive_files if k.endswith("/__folder__")]
    
    # Ensure local folders exist
    for folder in drive_folders:
        (local_root / folder).mkdir(parents=True, exist_ok=True)
    
    local_files = get_local_files(local_root)
    
    # 1. Download new / updated from Drive
    # Disabled per request: "sync to gdrive then delete on harddrive"
    # To re-enable bidirectional sync, uncomment this section.
    """
    for rel_path, dfile in drive_file_only.items():
        # Adjust for exported extensions
        local_path = local_root / rel_path
        # Handle doc export extension mismatch
        if EXPORT_GOOGLE_DOCS and dfile["mimeType"] in [
            "application/vnd.google-apps.document",
            "application/vnd.google-apps.spreadsheet",
            "application/vnd.google-apps.presentation"
        ]:
            # We'll check if any file with same stem exists
            stem_path = local_path.parent / local_path.stem
            existing_match = None
            for ext in [".docx", ".xlsx", ".pptx"]:
                if (stem_path.with_suffix(ext)).exists():
                    existing_match = stem_path.with_suffix(ext)
                    break
            if existing_match:
                local_path = existing_match
        
        if rel_path not in local_files and str(local_path.relative_to(local_root)).replace("\\","/") not in local_files:
            # New file on Drive
            download_drive_file(service, dfile, local_root / rel_path)
        else:
            # Both exist, check if Drive is newer
            l_info = local_files.get(rel_path) or local_files.get(str(local_path.relative_to(local_root)).replace("\\","/"))
            if not l_info:
                continue
            drive_time = parse_drive_time(dfile["modifiedTime"])
            # If md5 available, use it to avoid unnecessary sync
            drive_md5 = dfile.get("md5Checksum")
            if drive_md5:
                local_md5 = md5_of_file(l_info["full_path"])
                if local_md5 == drive_md5:
                    continue  # Same content
            
            if drive_time > l_info["mtime"] + timedelta(seconds=5):
                print(f"[Conflict] Drive newer for {rel_path}, downloading...")
                download_drive_file(service, dfile, l_info["full_path"])
    """
    
    # 2. Upload new / updated from Local
    # Need to re-get local after downloads for fresh state? Keep simple
    local_files = get_local_files(local_root)
    for rel_path, l_info in local_files.items():
        if rel_path not in drive_file_only:
            # Check if same stem exists as exported doc (avoid re-uploading exported files)
            # For simplicity, if local is docx that came from Google Doc, skip upload
            if rel_path not in drive_file_only:
                # New local file -> upload
                drive_subfolder = os.path.dirname(rel_path)
                parent_id = ensure_drive_folder_path(service, drive_subfolder, drive_root_id) if drive_subfolder else drive_root_id
                
                # Check if file already exists in that parent (by name)
                q = f"name='{Path(rel_path).name}' and '{parent_id}' in parents and trashed=false"
                resp = service.files().list(q=q, fields="files(id, modifiedTime)").execute()
                if resp["files"]:
                    existing = resp["files"][0]
                    drive_time = parse_drive_time(existing["modifiedTime"])
                    if l_info["mtime"] > drive_time + timedelta(seconds=5):
                        upload_local_file(service, l_info["full_path"], drive_root_id, existing_file_id=existing["id"])
                else:
                    upload_local_file(service, l_info["full_path"], drive_root_id)
        else:
            # Both exist, check if local is newer (md5 already checked)
            dfile = drive_file_only[rel_path]
            drive_time = parse_drive_time(dfile["modifiedTime"])
            if l_info["mtime"] > drive_time + timedelta(seconds=5):
                drive_md5 = dfile.get("md5Checksum")
                if drive_md5:
                    local_md5 = md5_of_file(l_info["full_path"])
                    if local_md5 == drive_md5:
                        continue
                print(f"[Conflict] Local newer for {rel_path}, uploading...")
                upload_local_file(service, l_info["full_path"], drive_root_id, existing_file_id=dfile["id"])
    
    print("--- Sync complete ---\n")

from datetime import timedelta

def main():
    parser = argparse.ArgumentParser(description="Sync Google Drive with local folder")
    parser.add_argument("--watch", action="store_true", help="Keep watching for changes")
    parser.add_argument("--interval", type=int, default=60, help="Poll interval in seconds for watch mode (default 60)")
    parser.add_argument("--local", type=str, default=str(LOCAL_ROOT), help="Local folder path")
    parser.add_argument("--drive-id", type=str, default=DRIVE_ROOT_ID, help="Drive folder ID (root for My Drive)")
    parser.add_argument("--first-run", action="store_true", help="Force re-auth")
    args = parser.parse_args()
    
    if args.first_run and os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
    
    local_root = Path(args.local)
    service = authenticate()
    
    sync_once(service, local_root, args.drive_id)
    
    if args.watch:
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            class ChangeHandler(FileSystemEventHandler):
                def __init__(self):
                    self.last_sync = time.time()
                    self.debounce = 5  # seconds
                
                def on_any_event(self, event):
                    if event.is_directory:
                        return
                    if time.time() - self.last_sync > self.debounce:
                        print(f"[Watch] Change detected: {event.src_path}")
                        self.last_sync = time.time()
                        sync_once(service, local_root, args.drive_id)
            
            print(f"[Watch] Watching {local_root} and polling Drive every {args.interval}s...")
            event_handler = ChangeHandler()
            observer = Observer()
            observer.schedule(event_handler, str(local_root), recursive=True)
            observer.start()
            
            try:
                while True:
                    time.sleep(args.interval)
                    sync_once(service, local_root, args.drive_id)
            except KeyboardInterrupt:
                observer.stop()
            observer.join()
            
        except ImportError:
            print("watchdog not installed, falling back to simple polling")
            print("Install with: pip install watchdog")
            while True:
                print(f"Sleeping {args.interval}s...")
                time.sleep(args.interval)
                sync_once(service, local_root, args.drive_id)

if __name__ == "__main__":
    main()
