from typing import List, Optional
from fastapi import APIRouter, Depends, Request, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.prediction import PredictionAssessmentRequest, PredictionResponse, PredictionSummaryResponse
from app.models.user import User
from app.security.dependencies import get_current_user, require_operational_user
from app.services.prediction_service import prediction_service

router = APIRouter(prefix="/api/predictions", tags=["Predictions"])

@router.post("", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
def create_prediction(
    req: PredictionAssessmentRequest,
    request: Request,
    current_user: User = Depends(require_operational_user),
    db: Session = Depends(get_db)
):
    ip_address = request.client.host if request.client else None
    db_prediction = prediction_service.create_prediction(
        db=db,
        user=current_user,
        request_data=req,
        ip_address=ip_address
    )
    return prediction_service.format_prediction_response(db_prediction)

@router.get("", response_model=List[PredictionSummaryResponse])
def get_user_predictions(
    risk_level: Optional[str] = Query(None, description="Filter by 'LOW' or 'HIGH'"),
    search: Optional[str] = Query(None, description="Search manufacturer or device class"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return prediction_service.get_user_predictions(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        risk_level=risk_level,
        search=search
    )

@router.get("/{id}", response_model=PredictionResponse)
def get_prediction_details(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_pred = prediction_service.get_prediction_by_id(db=db, prediction_id=id, user=current_user)
    return prediction_service.format_prediction_response(db_pred)
