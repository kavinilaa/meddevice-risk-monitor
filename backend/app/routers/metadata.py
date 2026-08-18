import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from app.database import get_db
from app.models.dataset import Manufacturer, Device, Event
from app.schemas.metadata import (
    MetadataOptionsResponse,
    HistoricalCountsResponse,
    DatasetStatsResponse
)

logger = logging.getLogger("meddevice.metadata")
router = APIRouter(prefix="/api/metadata", tags=["Metadata"])

@router.get("/event-types", response_model=List[str])
def get_event_types(db: Session = Depends(get_db)):
    """Get distinct event / alert types from the real MySQL dataset."""
    results = db.query(distinct(Event.type)).filter(Event.type.isnot(None)).all()
    types = sorted([r[0] for r in results if r[0]])
    return types

STANDARD_STATUSES = [
    "Completed",
    "Firm initiated action",
    "Not yet classified",
    "Open, Classified",
    "Terminated",
    "Classified"
]

@router.get("/statuses", response_model=List[str])
def get_statuses(db: Session = Depends(get_db)):
    """Get standard action / regulatory statuses without date contamination."""
    return STANDARD_STATUSES

@router.get("/classifications", response_model=List[str])
def get_classifications(db: Session = Depends(get_db)):
    """Get distinct device clinical specialties from the real MySQL dataset."""
    results = db.query(distinct(Device.classification)).filter(Device.classification.isnot(None)).all()
    classifications = sorted([r[0] for r in results if r[0]])
    return classifications

@router.get("/risk-classes", response_model=List[str])
def get_risk_classes(db: Session = Depends(get_db)):
    """Get distinct risk classes from the real MySQL dataset."""
    results = db.query(distinct(Device.risk_class)).filter(Device.risk_class.isnot(None)).all()
    risk_classes = sorted([r[0] for r in results if r[0]])
    return risk_classes

@router.get("/implant-statuses", response_model=List[Dict[str, str]])
def get_implant_statuses():
    """Get standard implant status options."""
    return [
        {"value": "NO", "label": "No — Non-implanted"},
        {"value": "YES", "label": "Yes — Implanted"}
    ]

@router.get("/countries", response_model=List[str])
def get_countries(db: Session = Depends(get_db)):
    """Get distinct country codes from real dataset events and devices."""
    evt_countries = db.query(distinct(Event.country)).filter(Event.country.isnot(None)).all()
    dev_countries = db.query(distinct(Device.country)).filter(Device.country.isnot(None)).all()
    all_c = set([r[0].upper() for r in evt_countries if r[0]] + [r[0].upper() for r in dev_countries if r[0]])
    return sorted(list(all_c))

@router.get("/manufacturers")
def search_manufacturers(
    search: Optional[str] = Query(None, min_length=1, description="Search term for manufacturer name"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search manufacturer names safely using parameterized SQL queries with pagination.
    Does not dump 31,000+ records into the browser at once.
    """
    query = db.query(Manufacturer.id, Manufacturer.name)
    if search:
        query = query.filter(Manufacturer.name.ilike(f"%{search}%"))

    total = query.count()
    offset = (page - 1) * limit
    items = query.order_by(Manufacturer.name).offset(offset).limit(limit).all()

    return {
        "items": [{"id": m.id, "name": m.name} for m in items],
        "total": total,
        "page": page,
        "limit": limit
    }

@router.get("/options", response_model=MetadataOptionsResponse)
def get_all_metadata_options(db: Session = Depends(get_db)):
    """Consolidated metadata endpoint for initial frontend page hydration."""
    types = get_event_types(db)
    statuses = get_statuses(db)
    classifications = get_classifications(db)
    risk_classes = get_risk_classes(db)
    countries = get_countries(db)

    # Top manufacturers for initial datalist
    mfr_records = db.query(Manufacturer.name).order_by(Manufacturer.name).limit(100).all()
    top_mfrs = [m[0] for m in mfr_records if m[0]]

    return MetadataOptionsResponse(
        types=types,
        statuses=statuses,
        classifications=classifications,
        risk_classes=risk_classes,
        countries=countries,
        manufacturers=top_mfrs,
        implanted_options=["NO", "YES"]
    )

@router.get("/historical-counts", response_model=HistoricalCountsResponse)
def get_historical_counts(
    manufacturer: Optional[str] = Query(None, description="Manufacturer name to look up"),
    classification: Optional[str] = Query(None, description="Device classification specialty to look up"),
    risk_class: Optional[str] = Query(None, description="Risk class to look up"),
    db: Session = Depends(get_db)
):
    """
    Retrieves real historical metrics and derivable fields from the MySQL dataset.
    Uses identical logic to feature_builder.py to ensure 100% data consistency.
    """
    mfr_event_count = 0
    device_event_count = 0
    avg_quantity = 0.0
    matched_devices = 0
    matched_mfr_name = None
    notes = []

    mfr_ids = []
    if manufacturer:
        mfrs = db.query(Manufacturer).filter(Manufacturer.name.ilike(f"%{manufacturer}%")).limit(50).all()
        mfr_ids = [m.id for m in mfrs]
        if mfrs:
            matched_mfr_name = mfrs[0].name

        if mfr_ids:
            dev_ids = [d[0] for d in db.query(Device.id).filter(Device.manufacturer_id.in_(mfr_ids)).all()]
            matched_devices = len(dev_ids)
            if dev_ids:
                mfr_event_count = db.query(Event).filter(Event.device_id.in_(dev_ids)).count()
                notes.append(f"Found {mfr_event_count} historical events for '{matched_mfr_name}'.")

            # Average quantity in commerce
            qty_res = db.query(func.avg(Device.quantity_in_commerce)).filter(
                Device.manufacturer_id.in_(mfr_ids),
                Device.quantity_in_commerce.isnot(None),
                Device.quantity_in_commerce > 0
            ).scalar()
            if qty_res and float(qty_res) > 0:
                avg_quantity = round(float(qty_res), 1)

    # Derive classification if omitted
    if not classification and mfr_ids:
        mfr_dev_class = db.query(Device.classification).filter(
            Device.manufacturer_id.in_(mfr_ids),
            Device.classification.isnot(None)
        ).group_by(Device.classification).order_by(func.count(Device.id).desc()).first()
        if mfr_dev_class and mfr_dev_class[0]:
            classification = mfr_dev_class[0]

    if not classification and risk_class:
        rc_class = db.query(Device.classification).filter(
            Device.risk_class == risk_class,
            Device.classification.isnot(None)
        ).group_by(Device.classification).order_by(func.count(Device.id).desc()).first()
        if rc_class and rc_class[0]:
            classification = rc_class[0]

    if not classification:
        top_class = db.query(Device.classification).filter(Device.classification.isnot(None)).first()
        if top_class and top_class[0]:
            classification = top_class[0]

    # Calculate device event count
    if mfr_ids and classification:
        target_dev_ids = [d[0] for d in db.query(Device.id).filter(
            Device.manufacturer_id.in_(mfr_ids),
            Device.classification.ilike(f"%{classification}%")
        ).all()]
        if target_dev_ids:
            db_dev_events = db.query(Event).filter(Event.device_id.in_(target_dev_ids)).count()
            if db_dev_events > 0:
                device_event_count = db_dev_events

    if device_event_count == 0 and classification:
        cat_dev_ids = [d[0] for d in db.query(Device.id).filter(Device.classification.ilike(f"%{classification}%")).limit(200).all()]
        if cat_dev_ids:
            device_event_count = db.query(Event).filter(Event.device_id.in_(cat_dev_ids)).count()

    if avg_quantity == 0.0 and classification:
        avg_cat_res = db.query(func.avg(Device.quantity_in_commerce)).filter(
            Device.classification.ilike(f"%{classification}%"),
            Device.quantity_in_commerce.isnot(None),
            Device.quantity_in_commerce > 0
        ).scalar()
        if avg_cat_res and float(avg_cat_res) > 0:
            avg_quantity = round(float(avg_cat_res), 1)

    if avg_quantity == 0.0:
        avg_quantity = 10000.0

    note_str = " ".join(notes) if notes else "No matching historical records found for the selection."

    return HistoricalCountsResponse(
        event_count=device_event_count,
        manufacturer_event_count=mfr_event_count,
        avg_quantity_in_commerce=avg_quantity,
        matched_device_count=matched_devices,
        matched_manufacturer_name=matched_mfr_name,
        note=note_str
    )

@router.get("/dataset-stats", response_model=DatasetStatsResponse)
def get_dataset_stats(db: Session = Depends(get_db)):
    """Return live dataset volume metrics from MySQL database tables."""
    total_events = db.query(func.count(Event.id)).scalar() or 0
    total_devices = db.query(func.count(Device.id)).scalar() or 0
    total_manufacturers = db.query(func.count(Manufacturer.id)).scalar() or 0

    return DatasetStatsResponse(
        total_events=total_events,
        total_devices=total_devices,
        total_manufacturers=total_manufacturers
    )
