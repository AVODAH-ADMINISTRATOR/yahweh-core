# Google Drive <-> Hard Drive Auto Sync

## Features:
- Bidirectional sync (upload new local files, download new Drive files)
- Conflict resolution by modified time + md5 checksum
- Creates missing folders automatically
- Handles Google Docs/Sheets/Slides by exporting (optional)
- One-shot sync or continuous `--watch` mode

## Setup:
1. Go to [Google Cloud Console](https://console.cloud.google.com/) -> New Project
2. Enable "Google Drive API"
3. APIs & Services -> Credentials -> Create Credentials -> OAuth Client ID -> Desktop App
4. Download JSON and save as `credentials.json` next to the script
5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. Authenticate (will open your browser to log in):
   ```bash
   python drive_sync.py --first-run
   ```

## Configuration
You can edit the top of `drive_sync.py` if you want a different default local folder or Drive ID:
```python
LOCAL_ROOT = Path.home() / "GoogleDriveSync"  # <- default
DRIVE_ROOT_ID = "root"  # <- or paste a specific Folder ID to sync only one folder
```

## Usage

**One-time sync:**
```bash
python drive_sync.py
```

**Continuous auto-sync:**
Watches local files + polls Drive every 60s
```bash
python drive_sync.py --watch
```

**Custom paths and polling interval:**
```bash
python drive_sync.py --local "D:/MyDrive" --drive-id "1aBcD...yourFolderId" --watch --interval 30
```

## Running on Startup (Linux/Mac)
You can use `cron` to automatically start the sync in the background when the system boots:
1. Open your crontab: `crontab -e`
2. Add the following line (adjusting paths as needed):
   ```bash
   @reboot /usr/bin/python3 /path/to/drive_sync.py --watch
   ```

*(Note: On Windows, you can achieve a similar result by pressing `Win + R`, typing `shell:startup`, and placing a shortcut or a `.bat` file there that runs the python script.)*
