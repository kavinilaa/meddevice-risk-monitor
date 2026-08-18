import logging
from typing import Dict, Any, Tuple, List, Optional
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.dataset import Manufacturer, Device, Event
from app.services.model_service import MODEL_FEATURES

logger = logging.getLogger("meddevice.feature_builder")

FEATURE_LABELS = {
    "type": "Event / Alert Type",
    "status": "Action / Regulatory Status",
    "classification": "Device Classification",
    "risk_class": "Risk Class",
    "country_event": "Country of Event",
    "country_device": "Country of Device Origin",
    "implanted": "Implant Status",
    "name_manufacturer": "Manufacturer",
    "quantity_in_commerce": "Commercial Distribution Volume",
    "event_count": "Historical Device Event Count",
    "manufacturer_event_count": "Manufacturer Event Count",
    "event_year": "Event Year",
    "event_month": "Event Month"
}

class FeatureItemProvenance:
    def __init__(self, feature: str, feature_name: str, value: Any, source: str):
        self.feature = feature
        self.feature_name = feature_name
        self.value = value
        self.source = source

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature": self.feature,
            "feature_name": self.feature_name,
            "value": self.value,
            "source": self.source
        }

class FeatureBuilderService:
    def map_implant_status(self, val: str) -> str:
        s = str(val or "").strip().upper()
        if "YES" in s or "IMPLANTED" in s:
            return "YES"
        return "NO"

    def derive_and_validate(
        self,
        db: Session,
        req_data: Dict[str, Any]
    ) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """
        Takes the user-supplied primary fields (device name, device category / classification,
        manufacturer, implant status) plus any optional additional fields, derives the hidden
        model features (type, status, risk_class, country_*, quantity_in_commerce, event counts,
        event_year/month) from the real MySQL dataset, validates all 13 features, and returns the
        DataFrame in exact order along with feature provenance tracking.
        """
        missing_fields = []
        provenance: Dict[str, Dict[str, Any]] = {}

        # 1. Primary User Fields
        m_device_name = str(req_data.get("name_device") or "").strip()
        m_implanted_raw = str(req_data.get("implanted") or "").strip()
        m_manufacturer = str(req_data.get("name_manufacturer") or "").strip()

        if not m_implanted_raw: missing_fields.append("Implant Status (implanted)")
        if not m_manufacturer: missing_fields.append("Manufacturer (name_manufacturer)")

        # type, status and risk_class are no longer collected on the user-facing form.
        # They may still arrive via the API (backwards compatibility / advanced callers);
        # if omitted, they are derived from MySQL historical records below.
        req_type = str(req_data.get("type") or "").strip()
        req_status = str(req_data.get("status") or "").strip()
        req_risk_class = str(req_data.get("risk_class") or "").strip()

        m_implanted = self.map_implant_status(m_implanted_raw)

        provenance["implanted"] = {"val": m_implanted, "src": "User selection"}
        provenance["name_manufacturer"] = {"val": m_manufacturer, "src": "User selection"}

        # 2. Query MySQL Dataset for Historical Records
        mfr_records = []
        if m_manufacturer:
            mfr_records = db.query(Manufacturer).filter(Manufacturer.name.ilike(f"%{m_manufacturer}%")).limit(50).all()

        mfr_ids = [m.id for m in mfr_records]

        # 2b. Try to resolve a specific matched device from the Device Name field.
        # This is used only to improve derivation accuracy for hidden model features;
        # Device Name itself is not one of the 13 trained model features.
        matched_device = None
        if m_device_name:
            device_query = db.query(Device).filter(Device.name.ilike(f"%{m_device_name}%"))
            if mfr_ids:
                scoped = device_query.filter(Device.manufacturer_id.in_(mfr_ids)).first()
                matched_device = scoped if scoped else device_query.first()
            else:
                matched_device = device_query.first()

        # 3. Derive Classification from MySQL if omitted
        m_classification = str(req_data.get("classification") or "").strip()
        if m_classification and m_classification.lower() != "none":
            provenance["classification"] = {"val": m_classification, "src": "User selection"}
        else:
            m_classification = ""
            # Query MySQL devices for this manufacturer to find the cataloged classification
            if mfr_ids:
                mfr_dev_class = db.query(Device.classification).filter(
                    Device.manufacturer_id.in_(mfr_ids),
                    Device.classification.isnot(None)
                ).group_by(Device.classification).order_by(func.count(Device.id).desc()).first()
                if mfr_dev_class and mfr_dev_class[0]:
                    m_classification = mfr_dev_class[0]
                    provenance["classification"] = {"val": m_classification, "src": "MySQL historical dataset"}
            
            # If no device records for this manufacturer, query by risk_class in MySQL
            if not m_classification and req_risk_class:
                rc_class = db.query(Device.classification).filter(
                    Device.risk_class == req_risk_class,
                    Device.classification.isnot(None)
                ).group_by(Device.classification).order_by(func.count(Device.id).desc()).first()
                if rc_class and rc_class[0]:
                    m_classification = rc_class[0]
                    provenance["classification"] = {"val": m_classification, "src": "MySQL historical dataset"}

            # Fallback to top cataloged specialty in MySQL
            if not m_classification:
                top_class = db.query(Device.classification).filter(Device.classification.isnot(None)).first()
                m_classification = top_class[0] if top_class else "Cardiovascular Devices"
                provenance["classification"] = {"val": m_classification, "src": "Dataset catalog baseline"}

        # 3b. Derive risk_class from MySQL if omitted (no longer collected on the form)
        if req_risk_class:
            m_risk_class = req_risk_class
            provenance["risk_class"] = {"val": m_risk_class, "src": "User provided"}
        else:
            m_risk_class = ""
            if matched_device and matched_device.risk_class:
                m_risk_class = matched_device.risk_class
                provenance["risk_class"] = {"val": m_risk_class, "src": "Matched device record"}
            if not m_risk_class and mfr_ids:
                mfr_rc = db.query(Device.risk_class).filter(
                    Device.manufacturer_id.in_(mfr_ids),
                    Device.risk_class.isnot(None)
                ).group_by(Device.risk_class).order_by(func.count(Device.id).desc()).first()
                if mfr_rc and mfr_rc[0]:
                    m_risk_class = mfr_rc[0]
                    provenance["risk_class"] = {"val": m_risk_class, "src": "MySQL historical dataset"}
            if not m_risk_class and m_classification:
                cls_rc = db.query(Device.risk_class).filter(
                    Device.classification.ilike(f"%{m_classification}%"),
                    Device.risk_class.isnot(None)
                ).group_by(Device.risk_class).order_by(func.count(Device.id).desc()).first()
                if cls_rc and cls_rc[0]:
                    m_risk_class = cls_rc[0]
                    provenance["risk_class"] = {"val": m_risk_class, "src": "MySQL historical dataset"}
            if not m_risk_class:
                top_rc = db.query(Device.risk_class).filter(Device.risk_class.isnot(None)).first()
                m_risk_class = top_rc[0] if top_rc else "2"
                provenance["risk_class"] = {"val": m_risk_class, "src": "Dataset catalog baseline"}

        # 3c. Derive type (Event / Alert Type) from MySQL if omitted (no longer collected on the form)
        matched_device_ids = [matched_device.id] if matched_device else []
        mfr_device_ids = [d[0] for d in db.query(Device.id).filter(Device.manufacturer_id.in_(mfr_ids)).all()] if mfr_ids else []
        classification_device_ids = [d[0] for d in db.query(Device.id).filter(
            Device.classification.ilike(f"%{m_classification}%")
        ).limit(200).all()] if m_classification else []

        if req_type:
            m_type = req_type
            provenance["type"] = {"val": m_type, "src": "User provided"}
        else:
            m_type = ""
            for candidate_ids, source_label in (
                (matched_device_ids, "Matched device record"),
                (mfr_device_ids, "MySQL historical dataset"),
                (classification_device_ids, "MySQL historical dataset"),
            ):
                if candidate_ids:
                    top_type = db.query(Event.type).filter(
                        Event.device_id.in_(candidate_ids),
                        Event.type.isnot(None)
                    ).group_by(Event.type).order_by(func.count(Event.id).desc()).first()
                    if top_type and top_type[0]:
                        m_type = top_type[0]
                        provenance["type"] = {"val": m_type, "src": source_label}
                        break
            if not m_type:
                top_type = db.query(Event.type).filter(Event.type.isnot(None)).group_by(Event.type).order_by(func.count(Event.id).desc()).first()
                m_type = top_type[0] if top_type else "Recall"
                provenance["type"] = {"val": m_type, "src": "Dataset catalog baseline"}

        # 3d. Derive status (Action / Regulatory Status) from MySQL if omitted (no longer collected on the form)
        if req_status:
            m_status = req_status
            provenance["status"] = {"val": m_status, "src": "User provided"}
        else:
            m_status = ""
            for candidate_ids, source_label in (
                (matched_device_ids, "Matched device record"),
                (mfr_device_ids, "MySQL historical dataset"),
                (classification_device_ids, "MySQL historical dataset"),
            ):
                if candidate_ids:
                    top_status = db.query(Event.status).filter(
                        Event.device_id.in_(candidate_ids),
                        Event.status.isnot(None)
                    ).group_by(Event.status).order_by(func.count(Event.id).desc()).first()
                    if top_status and top_status[0]:
                        m_status = top_status[0]
                        provenance["status"] = {"val": m_status, "src": source_label}
                        break
            if not m_status:
                top_status = db.query(Event.status).filter(Event.status.isnot(None)).group_by(Event.status).order_by(func.count(Event.id).desc()).first()
                m_status = top_status[0] if top_status else "Completed"
                provenance["status"] = {"val": m_status, "src": "Dataset catalog baseline"}

        # 4. Calculate manufacturer_event_count from MySQL
        mfr_event_count = None
        if req_data.get("manufacturer_event_count") is not None and str(req_data.get("manufacturer_event_count")).strip() != "":
            try:
                mfr_event_count = int(req_data["manufacturer_event_count"])
                provenance["manufacturer_event_count"] = {"val": mfr_event_count, "src": "User provided"}
            except Exception:
                pass

        if mfr_event_count is None and mfr_ids:
            dev_ids = [d[0] for d in db.query(Device.id).filter(Device.manufacturer_id.in_(mfr_ids)).all()]
            if dev_ids:
                db_mfr_count = db.query(Event).filter(Event.device_id.in_(dev_ids)).count()
                mfr_event_count = db_mfr_count
                provenance["manufacturer_event_count"] = {"val": mfr_event_count, "src": "MySQL historical dataset"}
            else:
                mfr_event_count = 0
                provenance["manufacturer_event_count"] = {"val": 0, "src": "MySQL (0 records)"}
        elif mfr_event_count is None:
            mfr_event_count = 0
            provenance["manufacturer_event_count"] = {"val": 0, "src": "MySQL (0 records)"}

        # 5. Calculate event_count from MySQL
        event_count = None
        if req_data.get("event_count") is not None and str(req_data.get("event_count")).strip() != "":
            try:
                event_count = int(req_data["event_count"])
                provenance["event_count"] = {"val": event_count, "src": "User provided"}
            except Exception:
                pass

        if event_count is None:
            if matched_device_ids:
                db_device_events = db.query(Event).filter(Event.device_id.in_(matched_device_ids)).count()
                if db_device_events > 0:
                    event_count = db_device_events
                    provenance["event_count"] = {"val": event_count, "src": "Matched device record"}

            if event_count is None and mfr_ids and m_classification:
                target_dev_ids = [d[0] for d in db.query(Device.id).filter(
                    Device.manufacturer_id.in_(mfr_ids),
                    Device.classification.ilike(f"%{m_classification}%")
                ).all()]
                if target_dev_ids:
                    db_dev_events = db.query(Event).filter(Event.device_id.in_(target_dev_ids)).count()
                    if db_dev_events > 0:
                        event_count = db_dev_events
                        provenance["event_count"] = {"val": event_count, "src": "MySQL historical dataset"}
            
            if event_count is None and m_classification:
                cat_dev_ids = [d[0] for d in db.query(Device.id).filter(Device.classification.ilike(f"%{m_classification}%")).limit(200).all()]
                if cat_dev_ids:
                    db_cat_events = db.query(Event).filter(Event.device_id.in_(cat_dev_ids)).count()
                    event_count = db_cat_events
                    provenance["event_count"] = {"val": event_count, "src": "MySQL historical dataset"}

            if event_count is None:
                event_count = 0
                provenance["event_count"] = {"val": 0, "src": "MySQL (0 records)"}

        # 6. Derive country_device from MySQL
        country_device = str(req_data.get("country_device") or "").strip().upper()
        if country_device and country_device != "NONE":
            provenance["country_device"] = {"val": country_device, "src": "User selection"}
        else:
            country_device = ""
            if matched_device and matched_device.country:
                country_device = matched_device.country.upper()
                provenance["country_device"] = {"val": country_device, "src": "Matched device record"}
            if not country_device and mfr_ids:
                dev_countries = db.query(Device.country).filter(
                    Device.manufacturer_id.in_(mfr_ids),
                    Device.country.isnot(None)
                ).distinct().limit(2).all()
                valid_countries = [c[0] for c in dev_countries if c[0]]
                if len(valid_countries) >= 1:
                    country_device = valid_countries[0].upper()
                    provenance["country_device"] = {"val": country_device, "src": "MySQL historical dataset"}
            if not country_device:
                country_device = "USA"
                provenance["country_device"] = {"val": country_device, "src": "Dataset market baseline"}

        # 7. Derive country_event from MySQL
        country_event = str(req_data.get("country_event") or "").strip().upper()
        if country_event and country_event != "NONE":
            provenance["country_event"] = {"val": country_event, "src": "User selection"}
        else:
            country_event = ""
            if m_type:
                evt_countries = db.query(Event.country).filter(
                    Event.type.ilike(f"%{m_type}%"),
                    Event.country.isnot(None)
                ).distinct().limit(2).all()
                valid_evt_c = [c[0] for c in evt_countries if c[0]]
                if len(valid_evt_c) >= 1:
                    country_event = valid_evt_c[0].upper()
                    provenance["country_event"] = {"val": country_event, "src": "MySQL historical dataset"}
            if not country_event:
                country_event = "USA"
                provenance["country_event"] = {"val": country_event, "src": "Dataset incident baseline"}

        # 8. Derive quantity_in_commerce from MySQL
        quantity_in_commerce = None
        if req_data.get("quantity_in_commerce") is not None and str(req_data.get("quantity_in_commerce")).strip() != "":
            try:
                quantity_in_commerce = float(req_data["quantity_in_commerce"])
                provenance["quantity_in_commerce"] = {"val": quantity_in_commerce, "src": "User provided"}
            except Exception:
                pass

        if quantity_in_commerce is None and matched_device and matched_device.quantity_in_commerce and matched_device.quantity_in_commerce > 0:
            quantity_in_commerce = round(float(matched_device.quantity_in_commerce), 1)
            provenance["quantity_in_commerce"] = {"val": quantity_in_commerce, "src": "Matched device record"}

        if quantity_in_commerce is None and mfr_ids:
            avg_res = db.query(func.avg(Device.quantity_in_commerce)).filter(
                Device.manufacturer_id.in_(mfr_ids),
                Device.quantity_in_commerce.isnot(None),
                Device.quantity_in_commerce > 0
            ).scalar()
            if avg_res is not None and float(avg_res) > 0:
                quantity_in_commerce = round(float(avg_res), 1)
                provenance["quantity_in_commerce"] = {"val": quantity_in_commerce, "src": "MySQL historical dataset"}

        if quantity_in_commerce is None and m_classification:
            avg_cat_res = db.query(func.avg(Device.quantity_in_commerce)).filter(
                Device.classification.ilike(f"%{m_classification}%"),
                Device.quantity_in_commerce.isnot(None),
                Device.quantity_in_commerce > 0
            ).scalar()
            if avg_cat_res is not None and float(avg_cat_res) > 0:
                quantity_in_commerce = round(float(avg_cat_res), 1)
                provenance["quantity_in_commerce"] = {"val": quantity_in_commerce, "src": "MySQL historical dataset"}

        if quantity_in_commerce is None:
            quantity_in_commerce = 10000.0
            provenance["quantity_in_commerce"] = {"val": quantity_in_commerce, "src": "Catalog volume baseline"}

        # 9. Derive event_year and event_month from MySQL
        event_year = None
        if req_data.get("event_year") is not None and str(req_data.get("event_year")).strip() != "":
            try:
                event_year = int(req_data["event_year"])
                provenance["event_year"] = {"val": event_year, "src": "User selection"}
            except Exception:
                pass

        if event_year is None:
            latest_year = db.query(func.max(Event.event_year)).filter(Event.event_year >= 1980, Event.event_year <= 2035).scalar()
            event_year = int(latest_year) if latest_year else 2025
            provenance["event_year"] = {"val": event_year, "src": "Historical event record"}

        event_month = None
        if req_data.get("event_month") is not None and str(req_data.get("event_month")).strip() != "":
            try:
                event_month = int(req_data["event_month"])
                provenance["event_month"] = {"val": event_month, "src": "User selection"}
            except Exception:
                pass

        if event_month is None:
            latest_month = db.query(func.max(Event.event_month)).filter(Event.event_year == event_year, Event.event_month >= 1, Event.event_month <= 12).scalar()
            event_month = int(latest_month) if latest_month and 1 <= int(latest_month) <= 12 else 6
            provenance["event_month"] = {"val": event_month, "src": "Historical event record"}

        # 10. Check for any unresolved missing primary fields
        if missing_fields:
            detail_msg = f"Additional information is required before this assessment can be performed: {', '.join(missing_fields)}"
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail_msg)

        # 11. Numerical validation
        if quantity_in_commerce < 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="quantity_in_commerce must be non-negative.")
        if event_count < 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="event_count must be non-negative.")
        if mfr_event_count < 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="manufacturer_event_count must be non-negative.")
        if not (1980 <= event_year <= 2035):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="event_year must be between 1980 and 2035.")
        if not (1 <= event_month <= 12):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="event_month must be between 1 and 12.")

        # 12. Build Final 13-Feature DataFrame in EXACT REQUIRED ORDER
        row_data = {
            "type": str(m_type),
            "status": str(m_status),
            "classification": str(m_classification),
            "risk_class": str(m_risk_class),
            "country_event": str(country_event),
            "country_device": str(country_device),
            "implanted": str(m_implanted),
            "name_manufacturer": str(m_manufacturer),
            "quantity_in_commerce": float(quantity_in_commerce),
            "event_count": int(event_count),
            "manufacturer_event_count": int(mfr_event_count),
            "event_year": int(event_year),
            "event_month": int(event_month)
        }

        input_df = pd.DataFrame([row_data], columns=MODEL_FEATURES)

        # 13. Format Provenance List
        features_used = []
        for feat in MODEL_FEATURES:
            p_info = provenance.get(feat, {"val": row_data[feat], "src": "System derived"})
            features_used.append({
                "feature": feat,
                "feature_name": FEATURE_LABELS.get(feat, feat),
                "value": p_info["val"],
                "source": p_info["src"]
            })

        return input_df, features_used

feature_builder = FeatureBuilderService()
