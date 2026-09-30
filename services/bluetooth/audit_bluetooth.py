import subprocess
import json
import platform
import datetime

def audit_bluetooth_and_system():
    print("[*] Initializing Integrated Avodah LLC corporate hardware audit...")
    
    audit_data = {
        "organization": "Integrated Avodah LLC",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "system_info": {
            "node": platform.node(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version()
        },
        "bluetooth_drivers": []
    }

    # Query Windows Management Instrumentation (WMI) via PowerShell for Bluetooth drivers
    ps_command = "Get-PnpDevice -Class Bluetooth | Select-Object FriendlyName, Status, Class, DriverVersion, Manufacturer | ConvertTo-Json"
    
    try:
        result = subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True, check=True)
        if result.stdout.strip():
            devices = json.loads(result.stdout)
            if isinstance(devices, dict):
                devices = [devices]
            audit_data["bluetooth_drivers"] = devices
            print(f"[+] Discovered {len(devices)} Bluetooth interface elements.")
        else:
            print("[-] No active Bluetooth devices detected via WMI.")
    except Exception as e:
        print(f"[-] Error querying hardware interfaces: {e}")

    # Export audit record for portal synchronization
    output_file = "bluetooth_compliance_audit.json"
    with open(output_file, "w") as f:
        json.dump(audit_data, f, indent=4)
        
    print(f"[✓] Corporate audit record compiled: {output_file}")
    print("[✓] System ready for secure repository synchronization.")

if __name__ == "__main__":
    audit_bluetooth_and_system()
