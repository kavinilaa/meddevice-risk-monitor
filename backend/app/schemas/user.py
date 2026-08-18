from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class UserProfileResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserUpdateProfile(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)

class UserAdminResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    assessment_count: int = 0

    model_config = ConfigDict(from_attributes=True)
