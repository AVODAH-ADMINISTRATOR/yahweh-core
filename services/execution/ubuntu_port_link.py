import urllib.request
import urllib.error

def verify_proxy_tunnel():
    proxy_ip = "192.168.56.101"  # Replace with your Ubuntu guest's host-only IP address
    proxy_port = 8888           # Default Tinyproxy port
    target_url = "https://www.integrated-avodah-llc.org/"

    proxy_handler = urllib.request.ProxyHandler({
        'http': f'http://{proxy_ip}:{proxy_port}',
        'https': f'http://{proxy_ip}:{proxy_port}'
    })
    
    opener = urllib.request.build_opener(proxy_handler)
    
    print(f"[*] Initializing secure proxy tunnel test through Ubuntu guest ({proxy_ip}:{proxy_port})...")
    
    try:
        response = opener.open(target_url, timeout=5)
        print(f"[+] Proxy Tunnel Active. Status Code: {response.status}")
        print(f"[✓] Secure cross-platform proxy routing verified successfully.")
    except urllib.error.URLError as e:
        print(f"[-] Proxy connection route unverified: {e.reason}")
    except Exception as e:
        print(f"[-] An unexpected error occurred during proxy verification: {e}")

if __name__ == "__main__":
    verify_proxy_tunnel()
