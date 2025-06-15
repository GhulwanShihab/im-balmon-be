from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, Column, JSON

from .base import BaseModel


class Device(BaseModel, SQLModel, table=True):
    """Device model to store information about various devices."""

    __tablename__ = "devices"

    id: Optional[int] = Field(default=None, primary_key=True)
    device_name: str = Field(index=True)
    device_code: str = Field(unique=True, index=True)
    nup_device: str = Field(unique=True, index=True) # NUP stands for Nomor Urut Pendaftaran, often unique
    bmn_brand: Optional[str] = None
    sample_brand: Optional[str] = None
    device_year: Optional[int] = None
    device_type: Optional[str] = None
    device_station: Optional[str] = None
    device_condition: Optional[str] = None # e.g., "Baik", "Rusak Ringan", "Rusak Berat"
    device_status: Optional[str] = None   # e.g., "Aktif", "Tidak Aktif", "Dipinjam"
    description: Optional[str] = None
    device_room: Optional[str] = None
    
    # For device photos, storing URLs or file paths is generally better
    # than storing binary data directly in the database.
    # We can store a list of URLs if a device can have multiple photos.
    photos_url: List[str] = Field(default=[], sa_column=Column(JSON))

    # You might want to add timestamps for creation and update
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})

    # Example of a relationship if devices are associated with users (e.g., who registered them)
    # registered_by_user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    # registered_by: Optional["User"] = Relationship(back_populates="registered_devices")