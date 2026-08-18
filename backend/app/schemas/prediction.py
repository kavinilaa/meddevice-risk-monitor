from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict

class RiskFactorItem(BaseModel):
    feature: str
    feature_name: str
    value: Any
    importance: float  # SHAP value or importance weight
    impact: str        # 'ELEVATED_RISK', 'REDUCED_RISK', or 'NEUTRAL'
    description: str

class FeatureItemProvenance(BaseModel):
    feature: str
    feature_name: str
    value: Any
    source: str        # 'User selection', 'MySQL historical dataset', 'Historical event record', 'User provided'

class PredictionAssessmentRequest(BaseModel):
    # PRIMARY USER-FACING FIELDS
    implanted: str = Field(..., min_length=1, description="Implant Status ('YES', 'NO', 'Yes — Implanted', 'No — Non-implanted')")
    name_manufacturer: str = Field(..., min_length=1, description="Manufacturer Name from MySQL dataset")

    # Device Name is not itself one of the 13 model features. It is used to look up
    # historical device records in MySQL to help derive the hidden model features below.
    name_device: Optional[str] = Field(None, description="Device Name (used for historical lookup; not a direct model feature)")

    # OPTIONAL / DERIVED MODEL FEATURES (Retrieved from MySQL if omitted).
    # type, status and risk_class are no longer collected directly from the user;
    # they are derived from historical MySQL records for the matched device /
    # manufacturer / classification (see feature_builder.py).
    type: Optional[str] = Field(None, description="Event / Alert Type (e.g. Field Safety Notice, Recall) — derived from MySQL if omitted")
    status: Optional[str] = Field(None, description="Action / Regulatory Status (e.g. Completed, Open Classified) — derived from MySQL if omitted")
    risk_class: Optional[str] = Field(None, description="Risk Class (e.g. 1, 2, 3, II, HDE) — derived from MySQL if omitted")
    classification: Optional[str] = Field(None, description="Device Category / Classification Specialty (user-selected; derived from MySQL dataset if omitted)")
    country_event: Optional[str] = Field(None, description="Country of Event (ISO 3-letter code)")
    country_device: Optional[str] = Field(None, description="Country of Device Origin (ISO 3-letter code)")
    quantity_in_commerce: Optional[float] = Field(None, ge=0, description="Commercial Distribution Volume")
    event_count: Optional[int] = Field(None, ge=0, description="Historical Device Event Count")
    manufacturer_event_count: Optional[int] = Field(None, ge=0, description="Manufacturer Historical Event Count")
    event_year: Optional[int] = Field(None, ge=1980, le=2035, description="Event Year")
    event_month: Optional[int] = Field(None, ge=1, le=12, description="Event Month (1 to 12)")

class PredictionCreateRequest(PredictionAssessmentRequest):
    """Alias for backwards compatibility"""
    pass

class PredictionResponse(BaseModel):
    id: int
    user_id: int
    
    # 13 Model Features
    type: str
    status: str
    classification: str
    risk_class: str
    country_event: str
    country_device: str
    implanted: str
    name_manufacturer: str
    quantity_in_commerce: float
    event_count: int
    manufacturer_event_count: int
    event_year: int
    event_month: int
    
    # Outputs
    prediction: int
    prediction_label: str
    risk_score: float
    risk_percentage: float
    risk_level: str
    
    # Explanations & Recommendations
    explanation: str
    risk_factors: List[RiskFactorItem]
    features_used: List[FeatureItemProvenance]
    maintenance_recommendation: str
    
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PredictionSummaryResponse(BaseModel):
    id: int
    created_at: datetime
    name_manufacturer: str
    classification: str
    risk_class: str
    prediction_label: str
    risk_score: float
    risk_percentage: float
    risk_level: str
    user_id: int
    user_name: Optional[str] = None
    user_role: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
