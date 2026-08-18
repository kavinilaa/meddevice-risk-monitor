from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserProfileResponse, UserUpdateProfile
from app.schemas.auth import PasswordChangeRequest
from app.models.user import User
from app.security.dependencies import get_current_user
from app.services.user_service import user_service

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserProfileResponse)
def update_current_user_profile(
    req: UserUpdateProfile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    updated = user_service.update_profile(db=db, user=current_user, req=req)
    return updated

@router.put("/me/password", status_code=status.HTTP_200_OK)
def change_user_password(
    req: PasswordChangeRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ip_address = request.client.host if request.client else None
    user_service.change_password(db=db, user=current_user, req=req, ip_address=ip_address)
    return {"message": "Password changed successfully"}
