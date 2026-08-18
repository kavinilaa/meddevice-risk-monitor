import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

logger = logging.getLogger("meddevice.db")

database_url = settings.DATABASE_URL

# Use PyMySQL driver for MySQL
if database_url.startswith("mysql://"):
    database_url = database_url.replace(
        "mysql://",
        "mysql+pymysql://",
        1
    )

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from app.models.user import User
    from app.models.prediction import Prediction
    from app.models.audit_log import AuditLog
    from app.models.dataset import Manufacturer, Device, Event
    from app.security.password import get_password_hash

    Base.metadata.create_all(bind=engine)
    
    # Ensure default admin
    db = SessionLocal()
    try:
        admin_email = settings.ADMIN_EMAIL.lower().strip()
        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
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
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        db.rollback()
    finally:
        db.close()
