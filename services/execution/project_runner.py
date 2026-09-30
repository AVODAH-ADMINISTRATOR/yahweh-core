import os
import subprocess
import glob
import time

def run_all_scripts():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Starting master execution in {current_dir}...")
    
    # Collect all executable files
    py_files = sorted(glob.glob(os.path.join(current_dir, "*.py")))
    js_files = sorted(glob.glob(os.path.join(current_dir, "*.js")))
    ts_files = sorted(glob.glob(os.path.join(current_dir, "*.ts")))
    
    all_files = py_files + js_files + ts_files
    
    # Exclude this runner itself
    this_file = os.path.abspath(__file__)
    if this_file in all_files:
        all_files.remove(this_file)
        
    print(f"Found {len(all_files)} scripts to deploy.")
    
    success_count = 0
    fail_count = 0
    timeout_count = 0
    
    for script in all_files:
        filename = os.path.basename(script)
        print(f"\n[{time.strftime('%H:%M:%S')}] DEPLOYING: {filename}")
        print("-" * 50)
        
        cmd = []
        if script.endswith(".py"):
            cmd = ["C:\\Users\\scout\\.antigravity-ide\\avodah-mcp-core\\.venv\\Scripts\\python.exe", script]
        elif script.endswith(".js"):
            cmd = ["node.exe", "--require", os.path.join(current_dir, "mock_require.js"), script]
        elif script.endswith(".ts"):
            cmd = ["npx.cmd", "ts-node", "--require", os.path.join(current_dir, "mock_require.js"), script]
            
        try:
            # We use a timeout to prevent long-running server scripts from blocking the whole sequence forever
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"STDERR: {result.stderr}")
                
            if result.returncode == 0:
                print(f"[{filename}] Execution SUCCESS")
                success_count += 1
            else:
                print(f"[{filename}] Execution FAILED with code {result.returncode}")
                fail_count += 1
                
        except subprocess.TimeoutExpired:
            print(f"[{filename}] Execution TIMEOUT (Script likely a server or daemon).")
            timeout_count += 1
        except Exception as e:
            print(f"[{filename}] ERROR: {str(e)}")
            fail_count += 1
            
    print("\n" + "=" * 50)
    print("MASTER DEPLOYMENT COMPLETE")
    print(f"Total: {len(all_files)} | Success: {success_count} | Failed: {fail_count} | Timeout/Servers: {timeout_count}")
    print("=" * 50)

if __name__ == "__main__":
    run_all_scripts()
