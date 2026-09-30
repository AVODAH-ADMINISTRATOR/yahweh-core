import os

# Initialize the secure Google Drive data holding path
DRIVE_VAULT = os.path.expanduser("~/Google Drive/Avodah_Master_Vault")
os.makedirs(DRIVE_VAULT, exist_ok=True)
print(f"[INIT] Google Drive data holding vault secured at: {DRIVE_VAULT}")
