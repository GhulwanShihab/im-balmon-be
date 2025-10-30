from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, Column, JSON, ForeignKey
from sqlalchemy import Enum as SQLEnum
from enum import Enum

from .perangkat import DeviceStatus

if TYPE_CHECKING:
    from .perangkat import Device

class DeviceChild(SQLModel, table=True):
    __tablename__ = "device_children"

    id: Optional[int] = Field(default=None, primary_key=True)
    parent_id: int = Field(sa_column=Column(ForeignKey("devices.id", ondelete="CASCADE"), index=True))

    device_name: str = Field(index=True)
    device_code: str = Field(index=True)
    nup_device: Optional[str] = None
    bmn_brand: Optional[str] = None
    sample_brand: Optional[str] = None
    device_year: Optional[int] = None
    device_type: Optional[str] = None
    device_station: Optional[str] = None
    device_condition: Optional[str] = None
    device_status: DeviceStatus = Field(
        default=DeviceStatus.TERSEDIA,
        sa_column=Column(SQLEnum(DeviceStatus), nullable=False)
    )
    description: Optional[str] = None
    device_room: Optional[str] = None
    photos_url: List[str] = Field(default_factory=list, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})

    parent: Optional["Device"] = Relationship(back_populates="children", sa_relationship_kwargs={"lazy": "selectin"})

    def __repr__(self):
        return f"<DeviceChild id={self.id} parent_id={self.parent_id} name={self.device_name}>"
