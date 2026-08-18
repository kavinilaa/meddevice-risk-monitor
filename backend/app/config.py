import os
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    # App Information
    APP_NAME: str = "MedDevice Risk Monitor"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"
    
    # Database
    DATABASE_URL: str = "mysql+pymysql://root:root@localhost:3306/medical_device_prediction"
    
    # Security / JWT
    JWT_SECRET_KEY: str = "meddevice_risk_monitor_jwt_secret_key_hackathon_2026_super_secure"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # ML Model Path
    MODEL_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml", "medical_device_xgboost_13features.pkl")
    
    # CORS
    FRONTEND_URL: str = "http://localhost:5173"
    ALLOWED_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Initial Admin Seed
    ADMIN_NAME: str = "Platform Administrator"
    ADMIN_EMAIL: str = "admin@meddevice.local"
    ADMIN_PASSWORD: str = "Admin@123456"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="allow"
    )

settings = Settings()
