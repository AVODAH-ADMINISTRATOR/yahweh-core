import os
import sys
import argparse
from collections import defaultdict
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

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
                print(f"ERROR: {CREDENTIALS_FILE} not found. Please download from Google Cloud Console.")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("drive", "v3", credentials=creds)

def format_size(bytes_val):
    if bytes_val >= 1000**4:
        return f"{bytes_val / (1000**4):.2f} TB"
    elif bytes_val >= 1000**3:
        return f"{bytes_val / (1000**3):.2f} GB"
    elif bytes_val >= 1000**2:
        return f"{bytes_val / (1000**2):.2f} MB"
    return f"{bytes_val} Bytes"

def find_duplicates(service):
    print("Scanning Google Drive for files (this may take a while for 5TB)...")
    
    files_by_md5 = defaultdict(list)
    page_token = None
    total_files_scanned = 0
    
    # We only care about files with an md5 (ignores folders and native Google docs)
    query = "trashed=false and mimeType != 'application/vnd.google-apps.folder'"
    
    while True:
        resp = service.files().list(
            q=query,
            pageSize=1000,
            fields="nextPageToken, files(id, name, size, md5Checksum)",
            pageToken=page_token
        ).execute()
        
        for f in resp.get("files", []):
            total_files_scanned += 1
            md5 = f.get("md5Checksum")
            if md5:
                files_by_md5[md5].append(f)
                
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
            
    print(f"Scanned {total_files_scanned} files.")
    
    # Process duplicates
    wasted_bytes = 0
    duplicate_groups = 0
    
    # Sort groups by wasted space to show the worst offenders first
    duplicate_summaries = []
    
    for md5, f_list in files_by_md5.items():
        if len(f_list) > 1:
            duplicate_groups += 1
            size = int(f_list[0].get("size", 0))
            wasted = size * (len(f_list) - 1)
            wasted_bytes += wasted
            
            duplicate_summaries.append({
                "count": len(f_list),
                "name": f_list[0].get("name", "Unknown"),
                "wasted": wasted,
                "files": f_list
            })
            
    duplicate_summaries.sort(key=lambda x: x["wasted"], reverse=True)
    
    print("\n--- Duplicate Analysis ---")
    print(f"Total duplicate groups found: {duplicate_groups}")
    print(f"Total space wasted by duplicates: {format_size(wasted_bytes)}")
    
    if duplicate_groups > 0:
        print("\nTop 5 Worst Offenders:")
        for dup in duplicate_summaries[:5]:
            print(f"- {dup['name']} ({dup['count']} copies) wasting {format_size(dup['wasted'])}")
            
    return wasted_bytes

def full_cleanup_checklist(service):
    print("Gathering data for Full Cleanup Checklist...\n")
    
    about = service.about().get(fields="storageQuota").execute()
    quota = about.get("storageQuota", {})
    
    limit = int(quota.get("limit", 0))
    usage = int(quota.get("usage", 0))
    trash = int(quota.get("usageInDriveTrash", 0))
    
    print("--- GOOGLE ONE 5TB CLEANUP CHECKLIST ---")
    
    # 1. Trash
    print(f"[1] TRASH BIN: You have {format_size(trash)} sitting in the trash.")
    if trash > 0:
        print("    -> Action: Run `python restore_cloud_capacity.py --empty-trash --yes` to reclaim this immediately.")
    else:
        print("    -> Action: None. Trash is already empty.")
        
    print("")
        
    # 2. Duplicates
    print("[2] DUPLICATES: Scanning for identical files...")
    wasted_dups = find_duplicates(service)
    print(f"    -> Action: You could save {format_size(wasted_dups)} by deleting duplicate files.")
    
    print("")
    
    # 3. Quota Summary
    pct = (usage / limit) * 100 if limit > 0 else 0
    potential_savings = trash + wasted_dups
    new_usage = usage - potential_savings
    new_pct = (new_usage / limit) * 100 if limit > 0 else 0
    
    print("--- SUMMARY ---")
    print(f"Current Usage:   {format_size(usage)} ({pct:.1f}%)")
    print(f"Potential Space: {format_size(potential_savings)}")
    print(f"Optimized Usage: {format_size(new_usage)} ({new_pct:.1f}%)")

def main():
    parser = argparse.ArgumentParser(description="Google One 5TB Manager - Duplicates & Cleanup")
    parser.add_argument("--duplicates", action="store_true", help="Find duplicates wasting TBs.")
    parser.add_argument("--cleanup", action="store_true", help="Run the full cleanup checklist.")
    args = parser.parse_args()

    if not args.duplicates and not args.cleanup:
        print("Please provide a flag, e.g., --duplicates or --cleanup")
        sys.exit(1)

    service = authenticate()
    
    if args.duplicates and not args.cleanup:
        find_duplicates(service)
        
    if args.cleanup:
        full_cleanup_checklist(service)

if __name__ == "__main__":
    main()
