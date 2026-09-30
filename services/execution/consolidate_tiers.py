def consolidate_to_major_tiers(micro_steps, num_tiers=10):
    """
    Consolidates a list of micro-steps into a defined number of major tiers.
    """
    total_steps = len(micro_steps)
    
    # Ensure the math works out perfectly
    if total_steps % num_tiers != 0:
        raise ValueError(f"Cannot evenly divide {total_steps} steps into {num_tiers} tiers.")
        
    chunk_size = total_steps // num_tiers
    major_tiers = {}

    # Slice the continuous list into 10 distinct chunks
    for i in range(num_tiers):
        start_idx = i * chunk_size
        end_idx = start_idx + chunk_size
        
        # Name the tier and assign its 36 constituent steps
        tier_name = f"Major Step {i + 1}"
        major_tiers[tier_name] = micro_steps[start_idx:end_idx]

    return major_tiers

# 1. Generate the 360 initial steps (This could be data, functions, or logs)
raw_sequence = [f"Sub-step {i:03d}" for i in range(1, 361)]

# 2. Execute the consolidation framework
try:
    structural_matrix = consolidate_to_major_tiers(raw_sequence, num_tiers=10)

    # 3. Output the system logs to verify the new structure
    print("--- CONSOLIDATION LOG ---")
    for major, micro in structural_matrix.items():
        start_step = micro[0]
        end_step = micro[-1]
        print(f"[{major}] Loaded {len(micro)} operations: {start_step} through {end_step}")

except ValueError as e:
    print(f"System Error: {e}")
