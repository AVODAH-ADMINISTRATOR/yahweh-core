import os
import sys
import argparse
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

def format_tb(bytes_val):
    return f"{bytes_val / (1000**4):.2f} TB"

def format_gb(bytes_val):
    return f"{bytes_val / (1000**3):.2f} GB"

def check_quota(service):
    print("Querying Google Drive for storage quota...\n")
    about = service.about().get(fields="storageQuota").execute()
    quota = about.get("storageQuota", {})
    
    limit = int(quota.get("limit", 0))
    usage = int(quota.get("usage", 0))
    trash = int(quota.get("usageInDriveTrash", 0))
    
    pct_full = (usage / limit) * 100 if limit > 0 else 0
    
    print("--- GOOGLE ONE 5TB STATUS ---")
    print(f"Total Limit: {format_tb(limit)}")
    print(f"Total Used:  {format_tb(usage)} ({pct_full:.1f}%)")
    
    if trash > 0:
        print(f"Trash Bin:   {format_gb(trash)}  <-- run --empty-trash to reclaim this!")
    else:
        print("Trash Bin:   0 GB")

def main():
    parser = argparse.ArgumentParser(description="Automated Google One 5TB Manager")
    parser.add_argument("--check", action="store_true", help="Check Google Drive capacity and trash stats.")
    # You can easily add more flags to this unified script later if you'd like!
    
    args = parser.parse_args()

    if not args.check:
        print("Please provide a flag, e.g., --check")
        sys.exit(1)

    service = authenticate()
    
    if args.check:
        check_quota(service)

if __name__ == "__main__":
    main()
