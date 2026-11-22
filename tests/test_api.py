import pytest
from fastapi.testclient import TestClient
from app.main import app, load_model

client = TestClient(app)

@pytest.fixture(autouse=True)
def ensure_model_is_loaded():
    load_model()

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    # Returns HTML web UI or JSON fallback
    assert ("text/html" in response.headers.get("content-type", "") or 
            response.json().get("project") == "HN HIT Predictor")

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model_loaded" in data

def test_version_endpoint():
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "hn-hit-predictor-api"
    assert "version" in data
    assert "git_sha" in data
    assert "environment" in data
    assert "timestamp" in data

def test_predict_endpoint_success():
    payload = {
        "title": "Show HN: FastML – Lightweight MLOps Pipeline in Python",
        "url": "https://github.com/developer/fastml",
        "submission_time": "2026-11-08T15:00:00Z"
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "is_hit" in data
    assert "hit_probability" in data
    assert 0.0 <= data["hit_probability"] <= 1.0
    assert "prediction_label" in data

def test_predict_endpoint_validation_error():
    # Title too short (< 3 characters)
    payload = {"title": "ab"}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
