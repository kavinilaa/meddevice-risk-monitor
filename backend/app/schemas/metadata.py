from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class MetadataOptionsResponse(BaseModel):
    types: List[str]
    statuses: List[str]
    classifications: List[str]
    risk_classes: List[str]
    countries: List[str]
    manufacturers: List[str]
    implanted_options: List[str]

class HistoricalCountsResponse(BaseModel):
    event_count: int
    manufacturer_event_count: int
    avg_quantity_in_commerce: float
    matched_device_count: int = 0
    matched_manufacturer_name: Optional[str] = None
    note: str

class DatasetStatsResponse(BaseModel):
    total_events: int
    total_devices: int
    total_manufacturers: int
    top_classifications: Optional[List[Dict[str, Any]]] = None
    top_event_types: Optional[List[Dict[str, Any]]] = None

class DeviceHistoryPoint(BaseModel):
    year: int
    event_count: int

class DeviceHistoryResponse(BaseModel):
    device_id: str
    device_name: str
    history: List[DeviceHistoryPoint]
    trend: Optional[str] = None            # 'Stable' | 'Increasing' | 'Rapidly Increasing' | None (no data)
    trend_direction: Optional[str] = None  # 'stable' | 'up' | 'up_rapid' | None (no data)
    explanation: str
    total_events: int
    years_observed: int
    growth_ratio: Optional[float] = None   # (recent-period avg - early-period avg) / early-period avg
