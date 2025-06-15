"""Device schemas for validation and response."""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class DeviceBase(BaseModel):
    """Base device schema."""
    device_name: str = Field(..., min_length=1, max_length=255, description="Nama perangkat")
    device_code: str = Field(..., min_length=1, max_length=100, description="Kode perangkat")
    nup_device: str = Field(..., min_length=1, max_length=100, description="NUP perangkat")
    bmn_brand: Optional[str] = Field(None, max_length=100, description="Merek BMN")
    sample_brand: Optional[str] = Field(None, max_length=100, description="Merek sample")
    device_year: Optional[int] = Field(None, ge=1900, le=2100, description="Tahun perangkat")
    device_type: Optional[str] = Field(None, max_length=100, description="Tipe perangkat")
    device_station: Optional[str] = Field(None, max_length=100, description="Stasiun perangkat")
    device_condition: Optional[str] = Field(None, max_length=50, description="Kondisi perangkat")
    device_status: Optional[str] = Field(None, max_length=50, description="Status perangkat")
    description: Optional[str] = Field(None, description="Deskripsi perangkat")
    device_room: Optional[str] = Field(None, max_length=100, description="Ruangan perangkat")
    photos_url: List[str] = Field(default=[], description="URL foto perangkat")


class DeviceCreate(DeviceBase):
    """Schema for creating a device."""
    pass


class DeviceUpdate(BaseModel):
    """Schema for updating a device."""
    device_name: Optional[str] = Field(None, min_length=1, max_length=255)
    device_code: Optional[str] = Field(None, min_length=1, max_length=100)
    nup_device: Optional[str] = Field(None, min_length=1, max_length=100)
    bmn_brand: Optional[str] = Field(None, max_length=100)
    sample_brand: Optional[str] = Field(None, max_length=100)
    device_year: Optional[int] = Field(None, ge=1900, le=2100)
    device_type: Optional[str] = Field(None, max_length=100)
    device_station: Optional[str] = Field(None, max_length=100)
    device_condition: Optional[str] = Field(None, max_length=50)
    device_status: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    device_room: Optional[str] = Field(None, max_length=100)
    photos_url: Optional[List[str]] = None


class DeviceResponse(DeviceBase):
    """Schema for device response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DeviceListResponse(BaseModel):
    """Schema for device list response with pagination."""
    devices: List[DeviceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DeviceSearchFilter(BaseModel):
    """Schema for device search and filtering."""
    device_name: Optional[str] = None
    device_code: Optional[str] = None
    nup_device: Optional[str] = None
    bmn_brand: Optional[str] = None
    sample_brand: Optional[str] = None
    device_year: Optional[int] = None
    device_type: Optional[str] = None
    device_station: Optional[str] = None
    device_condition: Optional[str] = None
    device_status: Optional[str] = None
    device_room: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    sort_by: Optional[str] = Field(default="created_at", description="Field to sort by")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class DeviceStats(BaseModel):
    """Schema for device statistics."""
    total_devices: int
    active_devices: int
    inactive_devices: int
    devices_by_condition: dict
    devices_by_status: dict
    devices_by_type: dict
    devices_by_room: dict
    new_devices_today: int
    new_devices_this_week: int
    new_devices_this_month: int


class DeviceConditionUpdate(BaseModel):
    """Schema for updating device condition."""
    device_condition: str = Field(..., max_length=50, description="Kondisi perangkat")
    description: Optional[str] = Field(None, description="Catatan perubahan kondisi")


class DeviceStatusUpdate(BaseModel):
    """Schema for updating device status."""
    device_status: str = Field(..., max_length=50, description="Status perangkat")
    description: Optional[str] = Field(None, description="Catatan perubahan status")