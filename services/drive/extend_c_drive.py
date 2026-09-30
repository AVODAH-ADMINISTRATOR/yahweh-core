import subprocess
import sys

def force_remove_partition_and_extend(disk_number: int, partition_number: int, target_volume: str = "C"):
    # Using 'override' bypasses Windows restrictions on protected volumes
    script_commands = f"""
    select disk {disk_number}
    select partition {partition_number}
    delete partition override
    select volume {target_volume}
    extend
    """
    
    try:
        print(f"Executing diskpart on Disk {disk_number}, Partition {partition_number}...")
        process = subprocess.run(
            ["diskpart"],
            input=script_commands,
            text=True,
            capture_output=True,
            check=True
        )
        print("Success: Partition forcibly removed and volume extended.")
        print(process.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error executing diskpart: {e.stderr}", file=sys.stderr)
        print(f"Output: {e.stdout}", file=sys.stderr)

if __name__ == "__main__":
    # Ensure you run your Python environment as Administrator/Root.
    # Update these targets to match your exact Disk Management configuration.
    TARGET_DISK = 0
    TARGET_PARTITION = 3
    
    # Uncomment to execute:
    # force_remove_partition_and_extend(TARGET_DISK, TARGET_PARTITION, "C")
