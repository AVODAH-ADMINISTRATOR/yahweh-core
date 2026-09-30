def calculate_variant_score(witnesses: list[str], variant_text: str) -> dict:
    """
    Stub scoring algorithm for manuscript variants.
    In reality, this would query Neo4j for the exact weight/dating of each witness (e.g., P45, Aleph, B).
    """
    
    # Very basic stub weight logic
    alexandrian_witnesses = {"Aleph", "B", "P75", "P46", "P66"}
    byzantine_witnesses = {"A", "K", "W", "Byz"}
    
    weight = 0.0
    affinity_counts = {"Alexandrian": 0, "Byzantine": 0, "Western": 0}
    
    for w in witnesses:
        if w in alexandrian_witnesses:
            weight += 0.9  # High weight for early Alexandrian
            affinity_counts["Alexandrian"] += 1
        elif w in byzantine_witnesses:
            weight += 0.4  # Lower weight for later majority text
            affinity_counts["Byzantine"] += 1
        else:
            weight += 0.5  # Neutral default
            
    # Determine primary affinity
    affinity = "Mixed"
    if affinity_counts["Alexandrian"] > affinity_counts["Byzantine"]:
        affinity = "Alexandrian"
    elif affinity_counts["Byzantine"] > affinity_counts["Alexandrian"]:
        affinity = "Byzantine"
        
    # Cap confidence at 0.99
    confidence = min(0.99, weight / (len(witnesses) * 0.9)) if witnesses else 0.0
    
    return {
        "confidence": round(confidence, 3),
        "weight": round(weight, 3),
        "affinity": affinity
    }
