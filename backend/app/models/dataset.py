from sqlalchemy import Column, String, Float, Integer, Text
from app.database import Base

class Manufacturer(Base):
    __tablename__ = "manufacturers"

    id = Column(String(64), primary_key=True)
    name = Column(String(500), index=True)
    parent_company = Column(String(500), nullable=True)
    address = Column(Text, nullable=True)
    representative = Column(String(500), nullable=True)
    comment = Column(Text, nullable=True)
    source = Column(String(255), nullable=True)
    slug = Column(String(500), nullable=True)
    created_at = Column(String(100), nullable=True)
    updated_at = Column(String(100), nullable=True)

class Device(Base):
    __tablename__ = "devices"

    id = Column(String(64), primary_key=True)
    manufacturer_id = Column(String(64), index=True, nullable=True)
    name = Column(String(500), nullable=True)
    classification = Column(String(255), index=True, nullable=True)
    code = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    distributed_to = Column(Text, nullable=True)
    implanted = Column(String(50), index=True, nullable=True)
    number = Column(String(255), nullable=True)
    quantity_in_commerce = Column(Float, nullable=True)
    risk_class = Column(String(50), index=True, nullable=True)
    slug = Column(String(500), nullable=True)
    country = Column(String(50), index=True, nullable=True)
    created_at = Column(String(100), nullable=True)
    updated_at = Column(String(100), nullable=True)

class Event(Base):
    __tablename__ = "events"

    id = Column(String(64), primary_key=True)
    device_id = Column(String(64), index=True, nullable=True)
    type = Column(String(100), index=True, nullable=True)
    status = Column(String(100), index=True, nullable=True)
    country = Column(String(50), index=True, nullable=True)
    action = Column(Text, nullable=True)
    action_classification = Column(String(100), nullable=True)
    action_level = Column(String(100), nullable=True)
    action_summary = Column(Text, nullable=True)
    determined_cause = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    date = Column(String(100), nullable=True)
    event_year = Column(Integer, index=True, nullable=True)
    event_month = Column(Integer, index=True, nullable=True)
    date_initiated_by_firm = Column(String(100), nullable=True)
    date_posted = Column(String(100), nullable=True)
    date_terminated = Column(String(100), nullable=True)
    date_updated = Column(String(100), nullable=True)
    created_at = Column(String(100), nullable=True)
    updated_at = Column(String(100), nullable=True)
