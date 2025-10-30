"""Schemas for DeviceChild CRUD operations."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from src.models.perangkat import DeviceStatus


class DeviceChildBase(BaseModel):
    parent_id: int
    device_name: str
    device_code: str
    nup_device: Optional[str] = None
    bmn_brand: Optional[str] = None
    sample_brand: Optional[str] = None
    device_year: Optional[int] = None
    device_type: Optional[str] = None
    device_station: Optional[str] = None
    device_condition: Optional[str] = None
    device_status: Optional[DeviceStatus] = DeviceStatus.TERSEDIA
    description: Optional[str] = None
    device_room: Optional[str] = None
    photos_url: Optional[List[str]] = []


class DeviceChildCreate(DeviceChildBase):
    """Schema for creating a new child device."""
    pass


class DeviceChildUpdate(BaseModel):
    """Schema for updating a child device."""
    device_name: Optional[str] = None
    device_code: Optional[str] = None
    nup_device: Optional[str] = None
    bmn_brand: Optional[str] = None
    sample_brand: Optional[str] = None
    device_year: Optional[int] = None
    device_type: Optional[str] = None
    device_station: Optional[str] = None
    device_condition: Optional[str] = None
    device_status: Optional[DeviceStatus] = None
    description: Optional[str] = None
    device_room: Optional[str] = None
    photos_url: Optional[List[str]] = None


class DeviceChildResponse(DeviceChildBase):
    """Response schema for a child device."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeviceChildListResponse(BaseModel):
    """Paginated list response."""
    total: int
    page: int
    page_size: int
    children: List[DeviceChildResponse]
