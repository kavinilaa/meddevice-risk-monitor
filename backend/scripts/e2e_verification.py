import urllib.request
import urllib.parse
import json
import uuid
import sys

BASE_URL = "http://127.0.0.1:8000"

def request(method, path, data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            return e.code, json.loads(content)
        except Exception:
            return e.code, {"error": content}

def run_e2e_tests():
    print("\n" + "="*70)
    print("RUNNING COMPREHENSIVE E2E VERIFICATION (5-FIELD PRIMARY UI -> 13 MODEL FEATURES)")
    print("="*70)

    # 1. Health check
    status, res = request("GET", "/api/health")
    print(f"[1] Health Check: Status={status}, Response={res}")
    assert status == 200 and res["status"] == "healthy" and res["model"] == "loaded"

    # 2. Model Info
    status, res = request("GET", "/api/model/info")
    print(f"[2] Model Info: Status={status}, Features={len(res['features'])}, Model={res['model_name']}")
    assert status == 200 and len(res["features"]) == 13

    # 3. Dedicated Metadata Endpoints
    status, ev_types = request("GET", "/api/metadata/event-types")
    assert status == 200 and len(ev_types) > 0
    status, statuses = request("GET", "/api/metadata/statuses")
    assert status == 200 and len(statuses) > 0
    status, risk_classes = request("GET", "/api/metadata/risk-classes")
    assert status == 200 and len(risk_classes) > 0
    print(f"[3] Dedicated Metadata Endpoints: Types={len(ev_types)}, Statuses={len(statuses)}, RiskClasses={len(risk_classes)}")

    # 4. Manufacturer Server-Side Parameterized Search
    status, mfr_res = request("GET", "/api/metadata/manufacturers?search=medtronic&page=1&limit=10")
    print(f"[4] Manufacturer Search ('medtronic'): Status={status}, Total Matches={mfr_res['total']}, Items Returned={len(mfr_res['items'])}")
    assert status == 200 and mfr_res["total"] > 0 and len(mfr_res["items"]) > 0

    # 5. Historical Counts Lookup from MySQL
    status, res = request("GET", "/api/metadata/historical-counts?manufacturer=Medtronic")
    print(f"[5] Historical Count Lookup (Medtronic): Status={status}, Mfr Events={res['manufacturer_event_count']}, Avg Quantity={res['avg_quantity_in_commerce']}")
    assert status == 200

    # 6. Biomedical Engineer Signup
    bio_email = f"bio_eng_{uuid.uuid4().hex[:6]}@hospital.org"
    status, res = request("POST", "/api/auth/signup", {
        "full_name": "Dr. Chen Wei",
        "email": bio_email,
        "password": "Password123!",
        "confirm_password": "Password123!",
        "role": "BIOMEDICAL_ENGINEER"
    })
    print(f"[6] Bio Engineer Signup: Status={status}, Email={bio_email}")
    assert status == 201
    bio_token = res["access_token"]

    # 7. Submit PRIMARY 5-FIELD RISK ASSESSMENT (Classification is omitted and derived from MySQL)
    primary_5_field_payload = {
        "type": "Recall",
        "status": "Completed",
        "risk_class": "3",
        "implanted": "Yes — Implanted",
        "name_manufacturer": "Medtronic"
        # classification is derived by backend from MySQL
    }
    status, res = request("POST", "/api/predictions", primary_5_field_payload, token=bio_token)
    print(f"[7] 5-Field Primary Risk Assessment Execution:")
    print(f"    - Status: {status}")
    print(f"    - Derived Classification: {res['classification']}")
    print(f"    - Label: {res['prediction_label']}")
    print(f"    - Score: {res['risk_percentage']}%")
    print(f"    - Risk Level: {res['risk_level']}")
    print(f"    - 13 Features Used Count: {len(res['features_used'])}")
    print(f"    - Sample Provenance: {[f'{f['feature_name']}: {f['value']} ({f['source']})' for f in res['features_used'][:4]]}")
    assert status == 201
    assert len(res["features_used"]) == 13
    assert len(res["classification"]) > 0
    assert len(res["risk_factors"]) > 0
    assert "explanation" in res and "maintenance_recommendation" in res
    bio_pred_id = res["id"]

    # 8. Verify History updated
    status, res = request("GET", "/api/predictions", token=bio_token)
    print(f"[8] Updated Prediction History: Count={len(res)}, First ID={res[0]['id']}")
    assert status == 200 and len(res) == 1 and res[0]["id"] == bio_pred_id

    # 9. Verify Prediction Details endpoint with 13 features provenance
    status, res = request("GET", f"/api/predictions/{bio_pred_id}", token=bio_token)
    print(f"[9] Prediction Details: ID={res['id']}, Mfr={res['name_manufacturer']}, Provenance Count={len(res['features_used'])}")
    assert status == 200 and res["id"] == bio_pred_id and len(res["features_used"]) == 13

    # 10. Admin Login & Dashboard Check
    status, res = request("POST", "/api/auth/login", {
        "email": "admin@meddevice.local",
        "password": "Admin@123456"
    })
    print(f"[10] Admin Login: Status={status}, Role={res['user']['role']}")
    assert status == 200 and res["user"]["role"] == "ADMIN"
    admin_token = res["access_token"]

    status, res = request("GET", "/api/admin/dashboard", token=admin_token)
    print(f"[10b] Admin Dashboard: Total Predictions={res['total_assessments']}, Historical Events={res['total_historical_events']:,}")
    assert status == 200 and res["total_assessments"] >= 1

    # 11. Validation Test: Missing primary field
    incomplete_payload = {
        "type": "Recall",
        "risk_class": "3",
        "implanted": "NO"
        # missing status and manufacturer
    }
    status, res = request("POST", "/api/predictions", incomplete_payload, token=bio_token)
    print(f"[11] Validation on Missing Primary Fields: Status={status} (Expected 422 Unprocessable Entity)")
    assert status == 422

    print("\n" + "="*70)
    print("ALL 5-FIELD E2E WORKFLOW CHECKS COMPLETED SUCCESSFULLY (100% PASS)!")
    print("="*70 + "\n")

if __name__ == "__main__":
    run_e2e_tests()
