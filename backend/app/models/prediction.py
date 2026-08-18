from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 13 Model Inputs (exact column names from ML pipeline)
    type = Column(String(100), nullable=False)
    status = Column(String(100), nullable=False)
    classification = Column(String(255), nullable=False)
    risk_class = Column(String(50), nullable=False)
    country_event = Column(String(50), nullable=False)
    country_device = Column(String(50), nullable=False)
    implanted = Column(String(50), nullable=False)
    name_manufacturer = Column(String(500), nullable=False)
    quantity_in_commerce = Column(Float, nullable=False, default=0.0)
    event_count = Column(Integer, nullable=False, default=0)
    manufacturer_event_count = Column(Integer, nullable=False, default=0)
    event_year = Column(Integer, nullable=False)
    event_month = Column(Integer, nullable=False)

    # Model Outputs
    prediction = Column(Integer, nullable=False)  # 0 or 1
    prediction_label = Column(String(50), nullable=False)  # 'Low Risk' or 'High Risk'
    risk_score = Column(Float, nullable=False)  # Raw probability (0.0 - 1.0)
    risk_percentage = Column(Float, nullable=False)  # Formatted percentage (0.0 - 100.0)
    risk_level = Column(String(50), nullable=False, index=True)  # 'LOW' or 'HIGH'

    # Explanations & Recommendations
    explanation = Column(Text, nullable=False)
    risk_factors = Column(Text, nullable=False)  # JSON-encoded array of contributing factors
    features_used = Column(Text, nullable=True)  # JSON-encoded array of 13 features + provenance
    maintenance_recommendation = Column(Text, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationship
    user = relationship("User", back_populates="predictions")

    __table_args__ = (
        Index("idx_pred_user_created", "user_id", "created_at"),
        Index("idx_pred_risk_level", "risk_level"),
    )
