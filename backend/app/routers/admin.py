from typing import List, Optional
from fastapi import APIRouter, Depends, Request, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.user import User
from app.models.prediction import Prediction
from app.models.audit_log import AuditLog
from app.models.dataset import Event, Device, Manufacturer
from app.schemas.admin import AdminDashboardStats, AdminUserStatusUpdate, AuditLogResponse
from app.schemas.user import UserAdminResponse
from app.schemas.prediction import PredictionSummaryResponse, PredictionResponse
from app.security.dependencies import require_admin
from app.services.user_service import user_service
from app.services.prediction_service import prediction_service

router = APIRouter(prefix="/api/admin", tags=["Admin Management"], dependencies=[Depends(require_admin)])

@router.get("/dashboard", response_model=AdminDashboardStats)
def get_admin_dashboard_stats(db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    
    total_assessments = db.query(Prediction).count()
    high_risk_assessments = db.query(Prediction).filter(Prediction.risk_level == "HIGH").count()
    low_risk_assessments = db.query(Prediction).filter(Prediction.risk_level == "LOW").count()
    
    total_historical_events = db.query(Event).count()
    total_historical_devices = db.query(Device).count()
    total_historical_manufacturers = db.query(Manufacturer).count()

    # User distribution by role
    user_roles_query = db.query(User.role, func.count(User.id)).group_by(User.role).all()
    user_distribution = {role: count for role, count in user_roles_query}

    # Risk distribution
    risk_distribution = {
        "HIGH": high_risk_assessments,
        "LOW": low_risk_assessments
    }

    return AdminDashboardStats(
        total_users=total_users,
        active_users=active_users,
        total_assessments=total_assessments,
        high_risk_assessments=high_risk_assessments,
        low_risk_assessments=low_risk_assessments,
        total_historical_events=total_historical_events,
        total_historical_devices=total_historical_devices,
        total_historical_manufacturers=total_historical_manufacturers,
        user_distribution=user_distribution,
        risk_distribution=risk_distribution
    )

@router.get("/users", response_model=List[UserAdminResponse])
def get_all_users(
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    users, _ = user_service.get_users_for_admin(
        db=db,
        search=search,
        role=role,
        is_active=is_active,
        limit=limit,
        offset=offset
    )
    return users

@router.get("/users/{id}", response_model=UserAdminResponse)
def get_user_by_id(id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    count = db.query(Prediction).filter(Prediction.user_id == id).count()
    return UserAdminResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        assessment_count=count
    )

@router.put("/users/{id}/status", response_model=UserAdminResponse)
def update_user_status(
    id: int,
    req: AdminUserStatusUpdate,
    request: Request,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    ip_address = request.client.host if request.client else None
    target_user = user_service.update_user_status(
        db=db,
        target_user_id=id,
        is_active=req.is_active,
        admin_user=current_admin,
        ip_address=ip_address
    )
    count = db.query(Prediction).filter(Prediction.user_id == id).count()
    return UserAdminResponse(
        id=target_user.id,
        full_name=target_user.full_name,
        email=target_user.email,
        role=target_user.role,
        is_active=target_user.is_active,
        created_at=target_user.created_at,
        assessment_count=count
    )

@router.get("/predictions", response_model=List[PredictionSummaryResponse])
def get_all_predictions_admin(
    risk_level: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    predictions, _ = prediction_service.get_all_predictions(
        db=db,
        limit=limit,
        offset=offset,
        risk_level=risk_level,
        user_id=user_id,
        search=search
    )

    # Collect user names
    user_ids = list(set([p.user_id for p in predictions]))
    users_map = {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}

    results = []
    for pred in predictions:
        u = users_map.get(pred.user_id)
        results.append(PredictionSummaryResponse(
            id=pred.id,
            created_at=pred.created_at,
            name_manufacturer=pred.name_manufacturer,
            classification=pred.classification,
            risk_class=pred.risk_class,
            prediction_label=pred.prediction_label,
            risk_score=pred.risk_score,
            risk_percentage=pred.risk_percentage,
            risk_level=pred.risk_level,
            user_id=pred.user_id,
            user_name=u.full_name if u else "Unknown",
            user_role=u.role if u else "Unknown"
        ))
    return results

@router.get("/predictions/{id}", response_model=PredictionResponse)
def get_admin_prediction_details(
    id: int,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    pred = prediction_service.get_prediction_by_id(db=db, prediction_id=id, user=current_admin)
    if not pred:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment record not found")
    return prediction_service.format_prediction_response(pred)

@router.get("/logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    action: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog, User).outerjoin(User, AuditLog.user_id == User.id)

    if action:
        query = query.filter(AuditLog.action == action.upper())

    results = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

    log_responses = []
    for log, u in results:
        log_responses.append(AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            user_name=u.full_name if u else (None if log.user_id is None else f"User #{log.user_id}"),
            user_email=u.email if u else None,
            user_role=u.role if u else None,
            action=log.action,
            description=log.description,
            ip_address=log.ip_address,
            created_at=log.created_at
        ))
    return log_responses
