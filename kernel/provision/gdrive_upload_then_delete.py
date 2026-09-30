import os
import sys
import argparse
import hashlib
from pathlib import Path

from send2trash import send2trash
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

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

def md5_of_file(path: Path):
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        print(f"  [Error] Failed to read {path} for MD5: {e}")
        return None

def ensure_drive_folder_path(service, drive_path, drive_root_id="root"):
    if not drive_path or drive_path in (".", "/", "\\"):
        return drive_root_id
    
    parts = [p for p in Path(drive_path.replace("\\", "/")).parts if p and p not in ("/", "\\")]
    current_id = drive_root_id
    for part in parts:
        q = f"name='{part}' and '{current_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        resp = service.files().list(q=q, fields="files(id)").execute()
        if resp["files"]:
            current_id = resp["files"][0]["id"]
        else:
            meta = {"name": part, "mimeType": "application/vnd.google-apps.folder", "parents": [current_id]}
            folder = service.files().create(body=meta, fields="id").execute()
            current_id = folder["id"]
    return current_id

def get_file_on_drive(service, parent_id, filename):
    q = f"name='{filename}' and '{parent_id}' in parents and trashed=false"
    resp = service.files().list(q=q, fields="files(id, md5Checksum, size)").execute()
    files = resp.get("files", [])
    return files[0] if files else None

def delete_local_file(local_path: Path, use_trash: bool, dry_run: bool):
    if dry_run:
        action = "[DRY RUN] Would TRASH" if use_trash else "[DRY RUN] Would PERMANENTLY DELETE"
        print(f"  {action}: {local_path}")
        return

    try:
        if use_trash:
            send2trash(str(local_path))
            print(f"  [TRASH] {local_path}")
        else:
            local_path.unlink()
            print(f"  [DELETED] {local_path}")
    except Exception as e:
        print(f"  [Error] Could not delete {local_path}: {e}")

def remove_empty_dirs(directory: Path, dry_run: bool):
    # Walk bottom-up
    for dirpath, dirnames, filenames in os.walk(directory, topdown=False):
        d = Path(dirpath)
        if d == directory:
            continue # Don't delete the root directory itself
        try:
            if not os.listdir(d):
                if dry_run:
                    print(f"  [DRY RUN] Would delete empty dir: {d}")
                else:
                    d.rmdir()
                    print(f"  [DELETED EMPTY DIR] {d}")
        except Exception as e:
            pass

def main():
    parser = argparse.ArgumentParser(description="Upload files to Google Drive then delete them locally.")
    parser.add_argument("--local", type=str, required=True, help="Local directory to upload")
    parser.add_argument("--drive-path", type=str, default="", help="Target path on Google Drive (default: root)")
    parser.add_argument("--dry-run", action="store_true", help="Do not upload or delete anything, just show what would happen")
    parser.add_argument("--no-trash", action="store_true", help="Permanently delete files instead of sending to recycle bin")
    parser.add_argument("--include-empty-dirs", action="store_true", help="Delete empty directories locally after files are uploaded")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt for permanent deletion")
    args = parser.parse_args()

    local_root = Path(args.local).resolve()
    if not local_root.exists() or not local_root.is_dir():
        print(f"Error: Local path {local_root} does not exist or is not a directory.")
        sys.exit(1)

    if args.no_trash and not args.yes and not args.dry_run:
        ans = input("WARNING: You specified --no-trash without --yes. Files will be PERMANENTLY DELETED. Are you sure? [y/N]: ")
        if ans.lower() not in ("y", "yes"):
            print("Aborted.")
            sys.exit(0)

    print("Authenticating with Google Drive...")
    service = authenticate()
    print("Authentication successful.\n")

    # Gather all files
    all_files = []
    for filepath in local_root.rglob("*"):
        if filepath.is_file():
            all_files.append(filepath)

    total_files = len(all_files)
    if total_files == 0:
        print("No files found to process.")
        return

    print(f"Found {total_files} files to process.")

    for i, local_path in enumerate(all_files, start=1):
        rel_path = local_path.relative_to(local_root)
        rel_path_str = str(rel_path).replace("\\", "/")
        print(f"\n[{i}/{total_files}] {rel_path_str}")

        # Compute target folder on drive
        target_dir = args.drive_path
        if rel_path.parent != Path("."):
            target_dir = str(Path(args.drive_path) / rel_path.parent).replace("\\", "/").strip("/")
        
        # Calculate local MD5
        local_md5 = md5_of_file(local_path)
        if not local_md5:
            continue

        if args.dry_run:
            print(f"  [DRY RUN] Local MD5: {local_md5}")
            # We don't make API calls to create folders on dry run if they don't exist
            # For simplicity, we just simulate the deletion part
            print(f"  [DRY RUN] Would check/upload to Drive path: {target_dir}")
            delete_local_file(local_path, not args.no_trash, True)
            continue

        # Ensure drive folder exists
        parent_id = ensure_drive_folder_path(service, target_dir)

        # Check if file exists
        drive_file = get_file_on_drive(service, parent_id, local_path.name)
        needs_upload = True

        if drive_file:
            drive_md5 = drive_file.get("md5Checksum")
            if drive_md5 == local_md5:
                print(f"  [Verified] MD5 match: {local_md5}")
                needs_upload = False
            else:
                print(f"  [Warning] File exists on Drive but MD5 differs (Local: {local_md5} vs Drive: {drive_md5}). Uploading as update.")
        
        if needs_upload:
            print(f"  [Uploading] {local_path.name}...")
            media = MediaFileUpload(str(local_path), resumable=True)
            try:
                if drive_file:
                    # Update
                    updated = service.files().update(fileId=drive_file["id"], media_body=media, fields="id, md5Checksum").execute()
                    drive_md5 = updated.get("md5Checksum")
                else:
                    # Create
                    meta = {"name": local_path.name, "parents": [parent_id]}
                    created = service.files().create(body=meta, media_body=media, fields="id, md5Checksum").execute()
                    drive_md5 = created.get("md5Checksum")
                
                if drive_md5 == local_md5:
                    print(f"  [Verified] Upload complete. MD5 match: {local_md5}")
                else:
                    print(f"  [Error] MD5 mismatch after upload! Local: {local_md5}, Drive: {drive_md5}. Skipping deletion.")
                    continue
            except Exception as e:
                print(f"  [Error] Upload failed: {e}")
                continue
        
        # If we got here, file is on Drive and MD5 matches. We can delete.
        delete_local_file(local_path, not args.no_trash, False)

    if args.include_empty_dirs:
        print("\nCleaning up empty directories...")
        remove_empty_dirs(local_root, args.dry_run)

    print("\nDone!")

if __name__ == "__main__":
    main()
