import pytest
import uuid

@pytest.fixture
def auth_headers(client):
    unique_email = f"bio_tester_{uuid.uuid4().hex[:8]}@hospital.org"
    payload = {
        "full_name": "Test Engineer",
        "email": unique_email,
        "password": "Password123!",
        "confirm_password": "Password123!",
        "role": "BIOMEDICAL_ENGINEER"
    }
    res = client.post("/api/auth/signup", json=payload)
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_prediction_workflow(client, auth_headers):
    # Valid 13-feature payload
    payload = {
        "type": "Recall",
        "status": "Completed",
        "classification": "Cardiovascular Devices",
        "risk_class": "3",
        "country_event": "USA",
        "country_device": "USA",
        "implanted": "YES",
        "name_manufacturer": "Medtronic",
        "quantity_in_commerce": 50000.0,
        "event_count": 8,
        "manufacturer_event_count": 120,
        "event_year": 2025,
        "event_month": 6
    }
    response = client.post("/api/predictions", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()

    # Check model output fields
    assert "prediction" in data
    assert data["prediction"] in [0, 1]
    assert data["prediction_label"] in ["Low Risk", "High Risk"]
    assert 0.0 <= data["risk_score"] <= 1.0
    assert 0.0 <= data["risk_percentage"] <= 100.0
    assert data["risk_level"] in ["LOW", "HIGH"]
    assert "explanation" in data
    assert len(data["risk_factors"]) > 0
    assert "maintenance_recommendation" in data

    # Check prediction history
    pred_id = data["id"]
    hist_res = client.get("/api/predictions", headers=auth_headers)
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert len(hist_data) >= 1
    assert any(p["id"] == pred_id for p in hist_data)

    # Check prediction details
    detail_res = client.get(f"/api/predictions/{pred_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["id"] == pred_id
    assert detail_data["name_manufacturer"] == "Medtronic"

def test_prediction_invalid_features(client, auth_headers):
    # Invalid month (15) and negative count (-5)
    payload = {
        "type": "Recall",
        "status": "Completed",
        "classification": "Cardiovascular Devices",
        "risk_class": "3",
        "country_event": "USA",
        "country_device": "USA",
        "implanted": "YES",
        "name_manufacturer": "Medtronic",
        "quantity_in_commerce": -100.0,
        "event_count": -5,
        "manufacturer_event_count": 10,
        "event_year": 2025,
        "event_month": 15
    }
    response = client.post("/api/predictions", json=payload, headers=auth_headers)
    assert response.status_code == 422
