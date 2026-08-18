import json
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from fastapi import HTTPException, status

from app.models.prediction import Prediction
from app.models.user import User
from app.schemas.prediction import PredictionAssessmentRequest, PredictionResponse, PredictionSummaryResponse
from app.services.model_service import model_service
from app.services.explanation_service import explanation_service
from app.services.recommendation_service import recommendation_service
from app.services.feature_builder import feature_builder
from app.services.audit_service import audit_service

logger = logging.getLogger("meddevice.predictions")

class PredictionService:
    def create_prediction(
        self,
        db: Session,
        user: User,
        request_data: PredictionAssessmentRequest,
        ip_address: Optional[str] = None
    ) -> Prediction:
        """
        Builds the exact 13-feature input via feature_builder, executes the XGBoost model,
        computes SHAP explanation, generates maintenance recommendation, and saves to MySQL.
        """
        req_dict = request_data.model_dump()

        # Build & Validate 13-Feature DataFrame using MySQL historical data
        input_df, features_used = feature_builder.derive_and_validate(db, req_dict)

        # Model Inference
        pred_label_idx, proba_val = model_service.predict(input_df)
        risk_pct = round(proba_val * 100.0, 2)
        risk_level = "HIGH" if (pred_label_idx == 1 or proba_val >= 0.5) else "LOW"
        pred_label = "High Risk" if risk_level == "HIGH" else "Low Risk"

        # Model SHAP Explanation
        explanation_narrative, risk_factor_objs = explanation_service.explain(
            input_df=input_df,
            prediction=pred_label_idx,
            probability=proba_val
        )
        risk_factors = [rf.model_dump() if hasattr(rf, "model_dump") else rf.dict() for rf in risk_factor_objs]

        # Maintenance Recommendation
        first_row = input_df.iloc[0].to_dict()
        maintenance_text = recommendation_service.generate_recommendation(
            prediction=pred_label_idx,
            probability=proba_val,
            input_data=first_row
        )

        # Create Database Record
        db_prediction = Prediction(
            user_id=user.id,
            type=str(first_row["type"]),
            status=str(first_row["status"]),
            classification=str(first_row["classification"]),
            risk_class=str(first_row["risk_class"]),
            country_event=str(first_row["country_event"]),
            country_device=str(first_row["country_device"]),
            implanted=str(first_row["implanted"]),
            name_manufacturer=str(first_row["name_manufacturer"]),
            quantity_in_commerce=float(first_row["quantity_in_commerce"]),
            event_count=int(first_row["event_count"]),
            manufacturer_event_count=int(first_row["manufacturer_event_count"]),
            event_year=int(first_row["event_year"]),
            event_month=int(first_row["event_month"]),
            prediction=int(pred_label_idx),
            prediction_label=pred_label,
            risk_score=float(proba_val),
            risk_percentage=float(risk_pct),
            risk_level=risk_level,
            explanation=explanation_narrative,
            risk_factors=json.dumps(risk_factors),
            features_used=json.dumps(features_used),
            maintenance_recommendation=maintenance_text,
        )

        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)

        # Audit Log
        audit_service.log_action(
            db=db,
            user_id=user.id,
            action="PREDICTION_CREATED",
            description=f"Risk assessment created for {first_row['name_manufacturer']} ({first_row['classification']}) - Result: {risk_level} ({risk_pct}%)",
            ip_address=ip_address
        )

        return db_prediction

    def get_prediction_by_id(
        self,
        db: Session,
        prediction_id: int,
        user: User
    ) -> Prediction:
        query = db.query(Prediction).filter(Prediction.id == prediction_id)
        if user.role != "ADMIN":
            query = query.filter(Prediction.user_id == user.id)

        prediction = query.first()
        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prediction record not found or access denied."
            )
        return prediction

    def get_user_predictions(
        self,
        db: Session,
        user_id: int,
        search: Optional[str] = None,
        risk_level: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[PredictionSummaryResponse]:
        query = db.query(Prediction).filter(Prediction.user_id == user_id)

        if risk_level:
            query = query.filter(Prediction.risk_level == risk_level.upper())

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Prediction.name_manufacturer.ilike(search_pattern),
                    Prediction.classification.ilike(search_pattern),
                    Prediction.type.ilike(search_pattern),
                )
            )

        predictions = query.order_by(desc(Prediction.created_at)).offset(offset).limit(limit).all()

        return [
            PredictionSummaryResponse(
                id=p.id,
                created_at=p.created_at,
                name_manufacturer=p.name_manufacturer,
                classification=p.classification,
                risk_class=p.risk_class,
                prediction_label=p.prediction_label,
                risk_score=p.risk_score,
                risk_percentage=p.risk_percentage,
                risk_level=p.risk_level,
                user_id=p.user_id,
            )
            for p in predictions
        ]

    def format_prediction_response(self, p: Prediction) -> PredictionResponse:
        risk_factors = json.loads(p.risk_factors) if p.risk_factors else []
        features_used = json.loads(p.features_used) if p.features_used else []

        if not features_used:
            from app.services.feature_builder import FEATURE_LABELS
            features_used = [
                {"feature": f, "feature_name": FEATURE_LABELS.get(f, f), "value": getattr(p, f, ""), "source": "Recorded evaluation"}
                for f in [
                    "type", "status", "classification", "risk_class", "country_event", "country_device",
                    "implanted", "name_manufacturer", "quantity_in_commerce", "event_count",
                    "manufacturer_event_count", "event_year", "event_month"
                ]
            ]

        return PredictionResponse(
            id=p.id,
            user_id=p.user_id,
            type=p.type,
            status=p.status,
            classification=p.classification,
            risk_class=p.risk_class,
            country_event=p.country_event,
            country_device=p.country_device,
            implanted=p.implanted,
            name_manufacturer=p.name_manufacturer,
            quantity_in_commerce=p.quantity_in_commerce,
            event_count=p.event_count,
            manufacturer_event_count=p.manufacturer_event_count,
            event_year=p.event_year,
            event_month=p.event_month,
            prediction=p.prediction,
            prediction_label=p.prediction_label,
            risk_score=p.risk_score,
            risk_percentage=p.risk_percentage,
            risk_level=p.risk_level,
            explanation=p.explanation,
            risk_factors=risk_factors,
            features_used=features_used,
            maintenance_recommendation=p.maintenance_recommendation,
            created_at=p.created_at,
        )

prediction_service = PredictionService()
