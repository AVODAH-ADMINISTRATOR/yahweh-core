def calculate_variant_score(witnesses: list[str], variant_text: str) -> dict:
    """Basic manuscript-variant scoring used by the textual criticism service."""
    alexandrian_witnesses = {"Aleph", "B", "P75", "P46", "P66"}
    byzantine_witnesses = {"A", "K", "W", "Byz"}

    weight = 0.0
    affinity_counts = {"Alexandrian": 0, "Byzantine": 0, "Western": 0}

    for witness in witnesses:
        if witness in alexandrian_witnesses:
            weight += 0.9
            affinity_counts["Alexandrian"] += 1
        elif witness in byzantine_witnesses:
            weight += 0.4
            affinity_counts["Byzantine"] += 1
        else:
            weight += 0.5

    affinity = "Mixed"
    if affinity_counts["Alexandrian"] > affinity_counts["Byzantine"]:
        affinity = "Alexandrian"
    elif affinity_counts["Byzantine"] > affinity_counts["Alexandrian"]:
        affinity = "Byzantine"

    confidence = min(0.99, weight / (len(witnesses) * 0.9)) if witnesses else 0.0

    return {
        "confidence": round(confidence, 3),
        "weight": round(weight, 3),
        "affinity": affinity,
    }
