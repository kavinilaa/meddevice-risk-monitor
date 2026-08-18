from typing import Optional
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog

class AuditService:
    @staticmethod
    def log(
        db: Session,
        action: str,
        description: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ) -> Optional[AuditLog]:
        try:
            entry = AuditLog(
                user_id=user_id,
                action=action,
                description=description,
                ip_address=ip_address
            )
            db.add(entry)
            db.commit()
            db.refresh(entry)
            return entry
        except Exception as e:
            db.rollback()
            print(f"Error creating audit log: {e}")
            return None

    def log_action(
        self,
        db: Session,
        action: str,
        description: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ) -> Optional[AuditLog]:
        return self.log(db=db, action=action, description=description, user_id=user_id, ip_address=ip_address)

audit_service = AuditService()
