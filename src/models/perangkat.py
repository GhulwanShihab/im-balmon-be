from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, Column, JSON
from sqlalchemy import Enum as SQLEnum
from enum import Enum

class DeviceStatus(str, Enum):
    TERSEDIA = "TERSEDIA"
    DIPINJAM = "DIPINJAM"
    MAINTENANCE = "MAINTENANCE"
    NONAKTIF = "NONAKTIF"

class Device(SQLModel, table=True):
    __tablename__ = "devices"

    id: Optional[int] = Field(default=None, primary_key=True)
    device_name: str = Field(index=True)
    device_code: str = Field(index=True)

    nup_device: Optional[str] = None
    bmn_brand: Optional[str] = None
    sample_brand: Optional[str] = None
    device_year: Optional[int] = None
    device_type: Optional[str] = None
    device_station: Optional[str] = None
    device_condition: Optional[str] = None
    device_status: Optional[DeviceStatus] = Field(
        sa_column=Column(SQLEnum(DeviceStatus), nullable=True)
    )
    description: Optional[str] = None
    device_room: Optional[str] = None
    photos_url: Optional[List[str]] = Field(default_factory=list, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})

    children: List["DeviceChild"] = Relationship(
        back_populates="parent",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"}
    )
