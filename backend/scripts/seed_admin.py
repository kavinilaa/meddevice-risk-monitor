import os
import sys

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.config import settings
from app.security.password import get_password_hash

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
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
        print(f"Created Admin account: {admin_email} / {settings.ADMIN_PASSWORD}")
    else:
        # Reset password to default if required
        admin.password_hash = get_password_hash(settings.ADMIN_PASSWORD)
        admin.is_active = True
        db.commit()
        print(f"Admin account updated: {admin_email} / {settings.ADMIN_PASSWORD}")
    db.close()

if __name__ == "__main__":
    main()
