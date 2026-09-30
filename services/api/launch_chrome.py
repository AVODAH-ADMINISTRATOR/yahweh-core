import subprocess
import time
import os

def launch_persistent_chrome():
    # Chrome paths to check
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]
    
    valid_path = next((p for p in chrome_paths if os.path.exists(p)), None)
    if not valid_path:
        print("Chrome executable not found.")
        return None

    # Launch Chrome and keep the handle so it doesn't die
    chrome_process = subprocess.Popen([
        valid_path,
        "--headless=new",
        "--remote-debugging-port=9222",
        "--remote-debugging-address=127.0.0.1",
        "--remote-allow-origins=*",
        f"--user-data-dir=C:\\Users\\scout\\SecureChromeProfile",
        "about:blank"
    ])

    print("Chrome started! PID:", chrome_process.pid)
    time.sleep(2) # Give it time to bind the port
    return chrome_process

if __name__ == "__main__":
    process = launch_persistent_chrome()
    if process:
        print("Chrome is running in the background. Press Ctrl+C to terminate.")
        try:
            process.wait()
        except KeyboardInterrupt:
            print("Terminating Chrome...")
            process.terminate()
