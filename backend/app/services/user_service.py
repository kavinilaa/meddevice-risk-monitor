from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app.models.user import User
from app.models.prediction import Prediction
from app.schemas.auth import SignupRequest, PasswordChangeRequest
from app.schemas.user import UserUpdateProfile, UserAdminResponse
from app.security.password import get_password_hash, verify_password
from app.security.jwt import create_access_token
from app.services.audit_service import audit_service

class UserService:
    def create_user(
        self,
        db: Session,
        req: SignupRequest,
        ip_address: Optional[str] = None
    ) -> User:
        # Check existing email
        existing = db.query(User).filter(User.email == req.email.lower().strip()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email address already exists."
            )

        hashed_pwd = get_password_hash(req.password)
        db_user = User(
            full_name=req.full_name.strip(),
            email=req.email.lower().strip(),
            password_hash=hashed_pwd,
            role=req.role,
            is_active=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Audit log
        audit_service.log(
            db=db,
            action="SIGNUP",
            description=f"User signed up: {db_user.full_name} ({db_user.email}) as {db_user.role}",
            user_id=db_user.id,
            ip_address=ip_address
        )

        return db_user

    def authenticate_user(
        self,
        db: Session,
        email: str,
        password: str,
        ip_address: Optional[str] = None
    ) -> User:
        user = db.query(User).filter(User.email == email.lower().strip()).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Please contact an administrator."
            )

        # Audit log login
        audit_service.log(
            db=db,
            action="LOGIN",
            description=f"User logged in: {user.email} ({user.role})",
            user_id=user.id,
            ip_address=ip_address
        )

        return user

    def update_profile(
        self,
        db: Session,
        user: User,
        req: UserUpdateProfile
    ) -> User:
        user.full_name = req.full_name.strip()
        db.commit()
        db.refresh(user)
        return user

    def change_password(
        self,
        db: Session,
        user: User,
        req: PasswordChangeRequest,
        ip_address: Optional[str] = None
    ) -> None:
        if not verify_password(req.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        user.password_hash = get_password_hash(req.new_password)
        db.commit()

        audit_service.log(
            db=db,
            action="PASSWORD_CHANGED",
            description=f"Password updated for user: {user.email}",
            user_id=user.id,
            ip_address=ip_address
        )

    def get_users_for_admin(
        self,
        db: Session,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[UserAdminResponse], int]:
        # Subquery for count of predictions
        pred_count_sub = (
            db.query(
                Prediction.user_id,
                func.count(Prediction.id).label("assessment_count")
            )
            .group_by(Prediction.user_id)
            .subquery()
        )

        query = db.query(
            User,
            func.coalesce(pred_count_sub.c.assessment_count, 0).label("assessment_count")
        ).outerjoin(pred_count_sub, User.id == pred_count_sub.c.user_id)

        if role:
            query = query.filter(User.role == role.upper())

        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (User.full_name.ilike(search_pattern)) |
                (User.email.ilike(search_pattern))
            )

        total = query.count()
        results = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()

        user_responses = []
        for user, count in results:
            user_responses.append(UserAdminResponse(
                id=user.id,
                full_name=user.full_name,
                email=user.email,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                assessment_count=int(count)
            ))

        return user_responses, total

    def update_user_status(
        self,
        db: Session,
        target_user_id: int,
        is_active: bool,
        admin_user: User,
        ip_address: Optional[str] = None
    ) -> User:
        target_user = db.query(User).filter(User.id == target_user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Prevent deactivating self or the last active admin
        if target_user.id == admin_user.id and not is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Administrators cannot deactivate their own account."
            )

        if target_user.role == "ADMIN" and not is_active:
            active_admin_count = db.query(User).filter(User.role == "ADMIN", User.is_active == True).count()
            if active_admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot deactivate the last active administrator."
                )

        target_user.is_active = is_active
        db.commit()
        db.refresh(target_user)

        action_name = "USER_ACTIVATED" if is_active else "USER_DEACTIVATED"
        audit_service.log(
            db=db,
            action=action_name,
            description=f"Admin '{admin_user.email}' {'activated' if is_active else 'deactivated'} user '{target_user.email}'",
            user_id=admin_user.id,
            ip_address=ip_address
        )

        return target_user

user_service = UserService()
