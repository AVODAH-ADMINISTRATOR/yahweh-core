import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from services.scoring import calculate_variant_score

def test_scoring_alexandrian():
    # Testing early highly-weighted manuscripts
    result = calculate_variant_score(["Aleph", "B"], "theos")
    assert result["affinity"] == "Alexandrian"
    assert result["confidence"] == 0.99 # Capped at 0.99

def test_scoring_byzantine():
    result = calculate_variant_score(["K", "Byz"], "kurios")
    assert result["affinity"] == "Byzantine"
    assert result["confidence"] < 1.0 # Should be lower than Alexandrian
    assert result["weight"] == 0.8 # 0.4 + 0.4
