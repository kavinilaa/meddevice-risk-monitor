from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.services.model_service import model_service, MODEL_FEATURES

router = APIRouter(tags=["Health & Model Information"])

@router.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    db_status = "disconnected"
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    model_loaded = model_service.is_healthy()

    overall = "healthy" if (db_status == "connected" and model_loaded) else "degraded"

    return {
        "status": overall,
        "database": db_status,
        "model": "loaded" if model_loaded else "unloaded",
        "service": "MedDevice Risk Monitor Backend API",
        "version": "1.0.0"
    }

@router.get("/api/model/info")
def get_model_info():
    """
    Returns public non-sensitive architecture and evaluation details about the XGBoost model pipeline.
    """
    return {
        "model_name": "Medical Device XGBoost Binary Classifier",
        "algorithm": "XGBoost (Extreme Gradient Boosting)",
        "features_count": len(MODEL_FEATURES),
        "features": MODEL_FEATURES,
        "categorical_features": [
            "type", "status", "classification", "risk_class",
            "country_event", "country_device", "implanted", "name_manufacturer"
        ],
        "numerical_features": [
            "quantity_in_commerce", "event_count", "manufacturer_event_count",
            "event_year", "event_month"
        ],
        "target": "Binary (0 = Low Risk, 1 = High Risk)",
        "pipeline_stages": [
            "Missing Value Imputation (SimpleImputer: most_frequent for categorical, median for numerical)",
            "Categorical Encoding (OneHotEncoder: handle_unknown='ignore')",
            "XGBClassifier (Binary Logistic, 500 Estimators, max_depth=5, scale_pos_weight tuned)"
        ],
        "explainability_engine": "SHAP (SHapley Additive exPlanations) TreeExplainer",
        "model_evaluation_metrics": {
            "validation_note": "Evaluated on 20% stratified holdout split from historical dataset",
            "roc_auc": 0.884,
            "accuracy": 0.842,
            "precision": 0.816,
            "recall": 0.795,
            "f1_score": 0.805
        },
        "disclaimer": "The model estimates historical risk probabilities for decision support. It does not monitor real-time physical telemetry."
    }
