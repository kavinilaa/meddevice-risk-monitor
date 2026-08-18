import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models import User, Prediction, AuditLog, Manufacturer, Device, Event
from app.security.password import get_password_hash
from app.services.model_service import model_service
from app.routers import (
    auth_router,
    users_router,
    predictions_router,
    metadata_router,
    admin_router,
    health_router
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("meddevice.main")

def seed_admin_user(db: Session):
    admin_email = settings.ADMIN_EMAIL.lower().strip()
    existing_admin = db.query(User).filter(User.email == admin_email).first()
    if not existing_admin:
        admin = User(
            full_name=settings.ADMIN_NAME,
            email=admin_email,
            password_hash=get_password_hash(settings.ADMIN_PASSWORD),
            role="ADMIN",
            is_active=True
        )
        db.add(admin)
        db.commit()
        logger.info(f"Initialized default administrator account: {admin_email}")
    else:
        logger.info(f"Administrator account already present: {admin_email}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup:
    logger.info("Initializing MedDevice Risk Monitor backend...")
    
    # 1. Ensure DB tables exist
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("SQLAlchemy models and database tables verified.")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

    # 2. Seed Admin
    try:
        db = SessionLocal()
        seed_admin_user(db)
        db.close()
    except Exception as e:
        logger.error(f"Error seeding admin user: {e}")

    # 3. Load Trained Model
    try:
        model_service.load_model()
        logger.info("Medical device XGBoost model loaded successfully")
    except Exception as e:
        logger.error(f"Model startup check failed: {e}")
        # Note: Do not crash entire server so health endpoint can report degraded status

    yield

    # Shutdown:
    logger.info("MedDevice Risk Monitor backend shutting down.")

app = FastAPI(
    title="MedDevice Risk Monitor API",
    description="Medical Device Failure Prediction & Risk Assessment Platform REST API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Production & Development CORS Middleware
cors_origins = settings.ALLOWED_ORIGINS if isinstance(settings.ALLOWED_ORIGINS, list) else [settings.ALLOWED_ORIGINS]
if not cors_origins or "*" in cors_origins:
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later or contact support."}
    )

# Include Routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(predictions_router)
app.include_router(metadata_router)
app.include_router(admin_router)

@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs": "/docs"
    }
