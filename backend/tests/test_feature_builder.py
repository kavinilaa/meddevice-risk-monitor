import pytest
from app.services.feature_builder import feature_builder
from app.services.model_service import model_service, MODEL_FEATURES
from app.database import SessionLocal
from fastapi import HTTPException

@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_feature_builder_5_primary_fields(db_session):
    """Test that supplying ONLY 5 primary fields derives all 13 features including classification."""
    primary_5_input = {
        "type": "Recall",
        "status": "Completed",
        "risk_class": "3",
        "implanted": "Yes — Implanted",
        "name_manufacturer": "Medtronic"
        # classification is omitted by the user and derived by backend from MySQL
    }

    df, features_used = feature_builder.derive_and_validate(db_session, primary_5_input)

    # 1. Exactly 13 columns in exact order
    assert list(df.columns) == MODEL_FEATURES
    assert len(df) == 1

    # 2. Assert values & derived classification
    row = df.iloc[0].to_dict()
    assert row["type"] == "Recall"
    assert row["status"] == "Completed"
    assert len(row["classification"]) > 0  # Derived from MySQL
    assert row["risk_class"] == "3"
    assert row["implanted"] == "YES"
    assert row["name_manufacturer"] == "Medtronic"
    assert row["event_count"] >= 0
    assert row["manufacturer_event_count"] >= 0
    assert row["quantity_in_commerce"] >= 0
    assert 1980 <= row["event_year"] <= 2035
    assert 1 <= row["event_month"] <= 12

    # 3. Assert provenance
    assert len(features_used) == 13
    assert all("feature" in f and "feature_name" in f and "value" in f and "source" in f for f in features_used)

    # 4. Feed directly to existing XGBoost model without error
    pred, proba = model_service.predict(df)
    assert pred in [0, 1]
    assert 0.0 <= proba <= 1.0

def test_feature_builder_missing_primary_field(db_session):
    """Test that missing required primary fields raises HTTP 422."""
    incomplete_input = {
        "type": "Recall",
        # missing status
        "risk_class": "3",
        "implanted": "NO",
        # missing manufacturer
    }

    with pytest.raises(HTTPException) as exc_info:
        feature_builder.derive_and_validate(db_session, incomplete_input)

    assert exc_info.value.status_code == 422
    assert "Additional information is required" in exc_info.value.detail

def test_feature_builder_invalid_numerical_bounds(db_session):
    """Test that invalid numerical bounds are rejected."""
    invalid_input = {
        "type": "Recall",
        "status": "Completed",
        "risk_class": "3",
        "implanted": "NO",
        "name_manufacturer": "Medtronic",
        "event_year": 2025,
        "event_month": 15 # Invalid month
    }

    with pytest.raises(HTTPException) as exc_info:
        feature_builder.derive_and_validate(db_session, invalid_input)

    assert exc_info.value.status_code == 422
    assert "event_month" in exc_info.value.detail
