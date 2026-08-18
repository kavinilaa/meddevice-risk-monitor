from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

class AdminDashboardStats(BaseModel):
    total_users: int
    active_users: int
    total_assessments: int
    high_risk_assessments: int
    low_risk_assessments: int
    total_historical_events: int
    total_historical_devices: int
    total_historical_manufacturers: int
    user_distribution: Dict[str, int]
    risk_distribution: Dict[str, int]

class AdminUserStatusUpdate(BaseModel):
    is_active: bool

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    action: str
    description: str
    ip_address: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
