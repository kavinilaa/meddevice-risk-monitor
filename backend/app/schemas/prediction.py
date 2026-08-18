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
    # 5 PRIMARY USER-FACING FIELDS (Classification is derived automatically by backend)
    type: str = Field(..., min_length=1, description="Event / Alert Type (e.g. Field Safety Notice, Recall)")
    status: str = Field(..., min_length=1, description="Action / Regulatory Status (e.g. Completed, Open Classified)")
    risk_class: str = Field(..., min_length=1, description="Risk Class (e.g. 1, 2, 3, II, HDE)")
    implanted: str = Field(..., min_length=1, description="Implant Status ('YES', 'NO', 'Yes — Implanted', 'No — Non-implanted')")
    name_manufacturer: str = Field(..., min_length=1, description="Manufacturer Name from MySQL dataset")

    # OPTIONAL / DERIVED MODEL FEATURES (Retrieved from MySQL if omitted)
    classification: Optional[str] = Field(None, description="Device Classification Specialty (Derived from MySQL dataset if omitted)")
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
