from fastapi import APIRouter, Depends, Request, status, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, UserResponse
from app.services.user_service import user_service
from app.services.audit_service import audit_service
from app.security.jwt import create_access_token
from app.security.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(req: SignupRequest, request: Request, db: Session = Depends(get_db)):
    ip_address = request.client.host if request.client else None
    user = user_service.create_user(db=db, req=req, ip_address=ip_address)
    
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip_address = request.client.host if request.client else None
    user = user_service.authenticate_user(db=db, email=req.email, password=req.password, ip_address=ip_address)
    
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ip_address = request.client.host if request.client else None
    audit_service.log(
        db=db,
        action="LOGOUT",
        description=f"User logged out: {current_user.email}",
        user_id=current_user.id,
        ip_address=ip_address
    )
    return {"message": "Logged out successfully"}
