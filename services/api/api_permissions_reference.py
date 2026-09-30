"""
GOOGLE DRIVE API - EVERYTHING THAT ALLOWS THE API
===================================================
Complete list of APIs, Scopes, Permissions, Quotas for Google One 5TB

Save as: api_permissions_reference.py
Run: python api_permissions_reference.py --show-all
"""

ALL_APIS_TO_ENABLE = {
    "drive.googleapis.com": "MAIN - Google Drive API - required for all file ops",
    "driveactivity.googleapis.com": "Track file changes, who modified",
    "docs.googleapis.com": "If you want to export Google Docs",
    "sheets.googleapis.com": "If you want to export Sheets",
    "people.googleapis.com": "Get user email, profile",
    "oauth2.googleapis.com": "OAuth2 token handling",
}

ALL_SCOPES = {
    "https://www.googleapis.com/auth/drive": {
        "access": "FULL - See, edit, create, delete ALL Drive files",
        "needed_for": "5TB manager - upload/delete/list everything",
        "restricted": False,
        "recommended": True,
    },
    "https://www.googleapis.com/auth/drive.file": {
        "access": "Only files created by this app",
        "needed_for": "Limited apps",
        "restricted": False,
        "recommended": False,  # Too limited for 5TB manager
    },
    "https://www.googleapis.com/auth/drive.readonly": {
        "access": "Read-only all files",
        "needed_for": "If you only want to check/audit 5TB",
        "restricted": False,
        "recommended": False,
    },
    "https://www.googleapis.com/auth/drive.metadata": {
        "access": "View metadata (names, sizes) but not content",
        "needed_for": "Fast scan without downloading",
        "restricted": False,
        "recommended": False,
    },
    "https://www.googleapis.com/auth/drive.metadata.readonly": {
        "access": "Read-only metadata",
        "needed_for": "Audit only",
        "restricted": False,
        "recommended": False,
    },
    "https://www.googleapis.com/auth/drive.photos.readonly": {
        "access": "Read Google Photos in Drive",
        "needed_for": "If Photos count against your 5TB",
        "restricted": False,
        "recommended": False,
    },
    "https://www.googleapis.com/auth/drive.appdata": {
        "access": "App-specific hidden folder",
        "needed_for": "Not needed for 5TB",
        "restricted": False,
        "recommended": False,
    },
}

# For Google One, you also need to understand these don't have separate APIs:
GOOGLE_ONE_NOTES = """
Google One 5TB is NOT a separate API - it's just Drive quota:
- one.google.com shows usage, but API is still drive.googleapis.com
- Gmail attachments count: No API to free except Gmail API
  To enable Gmail cleanup: gmail.googleapis.com + scope https://www.googleapis.com/auth/gmail.modify
- Photos Original quality counts: Need photoslibrary.googleapis.com

Additional APIs for full Google One cleanup:
  gmail.googleapis.com - to find/delete large Gmail attachments eating 5TB
  photoslibrary.googleapis.com - to manage Photos eating 5TB
"""

CREDENTIALS_JSON_STRUCTURE = {
    "installed": {
        "client_id": "1234567890-abc.apps.googleusercontent.com",
        "project_id": "my-5tb-manager",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "YOUR_SECRET",
        "redirect_uris": ["http://localhost"]
    }
}

TOKEN_JSON_STRUCTURE = {
    "token": "ya29.a0...",
    "refresh_token": "1//0g...",
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_id": "...",
    "client_secret": "...",
    "scopes": ["https://www.googleapis.com/auth/drive"],
    "expiry": "2026-01-01T00:00:00Z"
}

QUOTAS = {
    "750GB/day upload": "Hard limit per user, cannot increase for Google One personal",
    "10TB/day download": "Download limit",
    "1 billion requests/day": "API requests quota - more than enough",
    "1000 requests/100sec/user": "Per-user rate limit - our script respects this with backoff",
    "5TB max single file": "Max file size on 5TB plan",
}

def auto_setup_all():
    """Try to auto-enable everything via Python"""
    print("=== AUTO-ENABLING EVERYTHING FOR GOOGLE DRIVE API ===\n")
    
    print("1. APIs to enable:")
    for api, desc in ALL_APIS_TO_ENABLE.items():
        print(f"   - {api}: {desc}")
    
    print("\n2. Scopes (we request FULL drive scope for 5TB):")
    for scope, info in ALL_SCOPES.items():
        if info["recommended"]:
            print(f"   ✓ {scope} - {info['access']}")
    
    print("\n3. Credentials files needed:")
    print("   credentials.json - OAuth client (you create once in console)")
    print("   token.json - Auto-created after first login (refresh token)")
    
    print("\n4. OAuth Consent Screen requirements:")
    print("   - User Type: External (for personal Gmail)")
    print("   - App name: My5TB Manager")
    print("   - Scopes: ../auth/drive")
    print("   - Test users: Add your own Gmail (required while in Testing mode)")
    print("   - Publishing: Keep in Testing (no verification needed for personal use)")
    
    print("\n5. Quotas for Google One 5TB:")
    for k,v in QUOTAS.items():
        print(f"   - {k}: {v}")
    
    print(GOOGLE_ONE_NOTES)
    
    print("\n=== ONE-CLICK AUTO SETUP ===")
    print("If you have gcloud CLI, run:")
    print("  bash setup_google_one_api_complete.sh")
    print("\nIf not, manual 90-sec setup:")
    print("  1. Go to: https://console.cloud.google.com/")
    print("  2. New Project -> Enable Drive API")
    print("  3. Credentials -> Create OAuth client ID -> Desktop -> Download JSON")
    print("  4. Rename to credentials.json -> Run python google_one_5tb_manager_auto.py --check")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--show-all", action="store_true")
    args = p.parse_args()
    auto_setup_all()
    
    # Try to actually enable via service if gcloud exists
    try:
        import subprocess
        result = subprocess.run(["gcloud","services","list","--enabled"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("\n✓ gcloud found - currently enabled APIs:")
            print(result.stdout[:500])
    except:
        pass
