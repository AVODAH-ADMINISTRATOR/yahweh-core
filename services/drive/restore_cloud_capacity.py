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

def main():
    parser = argparse.ArgumentParser(description="Restore Google Drive cloud capacity by permanently clearing the trash.")
    parser.add_argument("--empty-trash", action="store_true", help="Empty the Google Drive trash.")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt.")
    args = parser.parse_args()

    if not args.empty_trash:
        print("Please specify an action, e.g., --empty-trash")
        sys.exit(1)

    if not args.yes:
        ans = input("WARNING: This will PERMANENTLY DELETE all files in your Google Drive trash. Are you sure? [y/N]: ")
        if ans.lower() not in ("y", "yes"):
            print("Aborted.")
            sys.exit(0)

    print("Authenticating with Google Drive...")
    service = authenticate()
    
    print("Emptying Google Drive trash. This may take a while depending on the amount of data...")
    try:
        service.files().emptyTrash().execute()
        print("Trash emptied successfully. Cloud capacity restored!")
    except Exception as e:
        print(f"Error emptying trash: {e}")

if __name__ == "__main__":
    main()
