"""Location schemas for validation and response."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class LocationBase(BaseModel):
    """Base location schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Nama lokasi (stasiun/ruangan)")
    type: str = Field(..., description="Tipe lokasi: STASIUN atau RUANGAN")
    description: Optional[str] = Field(None, max_length=500, description="Deskripsi lokasi")


class LocationCreate(LocationBase):
    """Schema for creating a location."""
    pass


class LocationUpdate(BaseModel):
    """Schema for updating a location."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[str] = Field(None)
    description: Optional[str] = Field(None, max_length=500)


class LocationResponse(LocationBase):
    """Schema for location response."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class DeviceInLocation(BaseModel):
    """Minimal device info for location detail."""
    id: int
    device_name: Optional[str] = None
    device_code: Optional[str] = None
    device_condition: Optional[str] = None
    device_status: Optional[str] = None
    is_child: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)


class LocationWithDevices(LocationResponse):
    """Location response with associated devices."""
    devices: List[DeviceInLocation] = []
