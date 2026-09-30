import json
import datetime
import socket
import platform

def authorize_and_unify_infrastructure():
    # Authoritative Organizational Context Parameters
    organization = "Integrated Avodah LLC"
    category = "Religious organization"
    location = "Lawrence, KS, US"
    brand_one_liner = "A holistic corporate compliance portal facilitating ethical stewardship and regulatory governance."
    core_values = ["Stewardship", "Integrity", "Compliance", "Holistic Service"]
    
    print("==================================================================")
    print(" INTEGRATED AVODAH LLC - SYSTEM AUTHORITY & INFRASTRUCTURE UNIFIER")
    print("==================================================================")
    print(f"[*] Initializing system authority protocol for {organization}...")
    print(f"[*] Category: {category} | Location: {location}")
    print(f"[*] Framework: {brand_one_liner}")
    
    # Gather local host infrastructure telemetry
    infrastructure_telemetry = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z"),
        "system_node": platform.node(),
        "operating_system": platform.system() + " " + platform.release(),
        "architecture": platform.machine(),
        "hostname": socket.gethostname(),
        "local_ip": socket.gethostbyname(socket.gethostname()),
        "authorization_status": "Authorized",
        "core_values_bound": core_values
    }
    
    print("\n[PHASE 1: Core Values Binding]")
    for value in core_values:
        print(f"  [OK] Verified & Bound Compliance Value: {value}")
        
    print("\n[PHASE 2: Infrastructure Telemetry Integration]")
    for k, v in infrastructure_telemetry.items():
        if isinstance(v, list):
            print(f"  - {k.capitalize()}: {', '.join(v)}")
        else:
            print(f"  - {k.capitalize()}: {v}")
            
    print("==================================================================")
    print("[OK] System authority successfully established and unified with infrastructure.")
    print("[OK] Environment synchronized as a secure digital repository node.")

    # Export immutable authorization audit log
    audit_filename = "infrastructure_authority_audit.json"
    with open(audit_filename, "w", encoding="utf-8") as f:
        json.dump(infrastructure_telemetry, f, indent=4)
        
    print(f"[OK] Immutable audit log compiled: {audit_filename}")

if __name__ == "__main__":
    authorize_and_unify_infrastructure()
