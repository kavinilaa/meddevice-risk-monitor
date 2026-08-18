import os
import logging
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, List
from app.config import settings

logger = logging.getLogger("meddevice.model")

MODEL_FEATURES = [
    "type",
    "status",
    "classification",
    "risk_class",
    "country_event",
    "country_device",
    "implanted",
    "name_manufacturer",
    "quantity_in_commerce",
    "event_count",
    "manufacturer_event_count",
    "event_year",
    "event_month"
]

class ModelService:
    _instance = None
    _model = None
    _preprocessor = None
    _classifier = None
    _is_loaded = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _resolve_model_path(self) -> str:
        candidates = [
            settings.MODEL_PATH,
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ml", "medical_device_xgboost_13features.pkl")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ml", "medical_device_xgboost_13features.pkl")),
            os.path.abspath("backend/ml/medical_device_xgboost_13features.pkl"),
            os.path.abspath("ml/medical_device_xgboost_13features.pkl"),
            r"C:\Users\kavin\Downloads\xgboost_model train.pkl"
        ]
        for path in candidates:
            if path and os.path.exists(path):
                return path
        return candidates[0]

    def load_model(self):
        if self._is_loaded and self._model is not None:
            return

        model_path = self._resolve_model_path()

        if not os.path.exists(model_path):
            logger.error(f"Medical device model file NOT found at: {model_path}")
            raise FileNotFoundError(f"Model file not found at: {model_path}")

        try:
            logger.info(f"Loading trained XGBoost pipeline from: {model_path}")
            self._model = joblib.load(model_path)
            
            # Verify steps
            if hasattr(self._model, "named_steps"):
                self._preprocessor = self._model.named_steps.get("preprocessor")
                self._classifier = self._model.named_steps.get("classifier")
            else:
                self._preprocessor = None
                self._classifier = self._model

            # Validate predict and predict_proba
            if not hasattr(self._model, "predict") or not hasattr(self._model, "predict_proba"):
                raise AttributeError("Loaded model pipeline lacks predict() or predict_proba() method")

            self._is_loaded = True
            logger.info("Medical device XGBoost model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model pipeline: {str(e)}")
            self._is_loaded = False
            raise RuntimeError(f"Failed to load XGBoost model pipeline: {str(e)}")

    def is_healthy(self) -> bool:
        return self._is_loaded and self._model is not None

    def create_dataframe(self, input_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Creates a pandas DataFrame with exact 13 features and correct data types.
        """
        row = {
            "type": str(input_data.get("type", "")),
            "status": str(input_data.get("status", "")),
            "classification": str(input_data.get("classification", "")),
            "risk_class": str(input_data.get("risk_class", "")),
            "country_event": str(input_data.get("country_event", "")),
            "country_device": str(input_data.get("country_device", "")),
            "implanted": str(input_data.get("implanted", "NO")),
            "name_manufacturer": str(input_data.get("name_manufacturer", "")),
            "quantity_in_commerce": float(input_data.get("quantity_in_commerce", 0.0)),
            "event_count": int(input_data.get("event_count", 0)),
            "manufacturer_event_count": int(input_data.get("manufacturer_event_count", 0)),
            "event_year": int(input_data.get("event_year", 2025)),
            "event_month": int(input_data.get("event_month", 1))
        }
        df = pd.DataFrame([row], columns=MODEL_FEATURES)
        return df

    def predict(self, input_df: pd.DataFrame) -> Tuple[int, float]:
        """
        Runs model inference using the loaded pipeline.
        Returns:
            prediction: int (0 for Low Risk, 1 for High Risk)
            probability: float (probability of positive class, 0.0 to 1.0)
        """
        if not self._is_loaded or self._model is None:
            self.load_model()

        preds = self._model.predict(input_df)
        probas = self._model.predict_proba(input_df)

        prediction = int(preds[0])
        # Positive class probability (High Risk)
        if probas.shape[1] >= 2:
            probability = float(probas[0, 1])
        else:
            probability = float(probas[0, 0])

        return prediction, probability

    @property
    def model(self):
        if not self._is_loaded:
            self.load_model()
        return self._model

    @property
    def preprocessor(self):
        if not self._is_loaded:
            self.load_model()
        return self._preprocessor

    @property
    def classifier(self):
        if not self._is_loaded:
            self.load_model()
        return self._classifier

model_service = ModelService.get_instance()
