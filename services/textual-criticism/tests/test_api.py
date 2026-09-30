import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_score_variant_endpoint():
    payload = {
        "verse_ref": "John 1:18",
        "base_text": "monogenes huios",
        "variant_text": "monogenes theos",
        "witnesses": ["Aleph", "B", "P66"]
    }
    response = client.post("/api/v1/variants/score", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["verse_ref"] == "John 1:18"
    assert data["text_type_affinity"] == "Alexandrian"
    assert data["confidence_score"] > 0.8
