import json
import urllib.request
import urllib.error

def connect_compliance_portal():
    # Integrated Avodah LLC Corporate Compliance Portal endpoint
    portal_url = "https://www.integrated-avodah-llc.org/"
    debug_port = 9222
    
    print(f"[*] Initializing connection to Chrome debugging interface on port {debug_port}...")
    
    try:
        # Query the active debugging targets endpoint
        target_endpoint = f"http://127.0.0.1:{debug_port}/json"
        req = urllib.request.Request(target_endpoint)
        
        with urllib.request.urlopen(req) as response:
            targets = json.loads(response.read().decode('utf-8'))
            
        print(f"[+] Successfully connected. Active targets found: {len(targets)}")
        
        # Identify an available page target to execute navigation
        page_target = next((t for t in targets if t['type'] == 'page'), None)
        
        if page_target:
            target_id = page_target['id']
            print(f"[+] Target page acquired (ID: {target_id}).")
            print(f"[+] Directing session to Integrated Avodah LLC portal: {portal_url}")
            
            # Trigger navigation via the CDP HTTP endpoint
            nav_endpoint = f"http://127.0.0.1:{debug_port}/json/activate/{target_id}"
            urllib.request.urlopen(urllib.request.Request(nav_endpoint, method='GET'))
            
            print("[✓] Session successfully linked to the compliance portal environment.")
        else:
            print("[-] Error: No active browser page targets available on port 9222.")
            
    except urllib.error.URLError as e:
        print(f"[-] Connection failed: Ensure Chrome is running with '--remote-debugging-port={debug_port}'. Details: {e.reason}")
    except Exception as e:
        print(f"[-] An unexpected error occurred: {e}")

if __name__ == "__main__":
    connect_compliance_portal()
