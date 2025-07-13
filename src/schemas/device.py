"""Device schemas for validation and response."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date


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


class DeviceUsageStatistics(BaseModel):
    """Schema for device usage statistics."""
    device_id: int
    nup_device: str = Field(..., description="NUP perangkat")
    device_name: str = Field(..., description="Nama perangkat")
    device_brand: Optional[str] = Field(None, description="Merk perangkat (BMN atau Sample)")
    device_year: Optional[int] = Field(None, description="Tahun perangkat")
    device_condition: Optional[str] = Field(None, description="Kondisi perangkat saat ini")
    device_status: Optional[str] = Field(None, description="Status perangkat saat ini")
    total_usage_days: int = Field(0, description="Total penggunaan dalam hari")
    total_loans: int = Field(0, description="Total jumlah peminjaman")
    last_used_date: Optional[date] = Field(None, description="Tanggal terakhir digunakan")
    last_borrower: Optional[str] = Field(None, description="Peminjam terakhir")
    last_activity: Optional[str] = Field(None, description="Kegiatan terakhir")
    average_usage_per_loan: float = Field(0.0, description="Rata-rata penggunaan per peminjaman (hari)")
    usage_frequency_score: float = Field(0.0, description="Skor frekuensi penggunaan (0-100)")


class DeviceUsageFilter(BaseModel):
    """Schema for filtering device usage statistics."""
    device_name: Optional[str] = None
    nup_device: Optional[str] = None
    device_brand: Optional[str] = None
    device_year: Optional[int] = None
    device_condition: Optional[str] = None
    device_status: Optional[str] = None
    min_usage_days: Optional[int] = Field(None, ge=0, description="Minimum total usage days")
    max_usage_days: Optional[int] = Field(None, ge=0, description="Maximum total usage days")
    min_loans: Optional[int] = Field(None, ge=0, description="Minimum total loans")
    last_used_from: Optional[date] = Field(None, description="Last used date from")
    last_used_to: Optional[date] = Field(None, description="Last used date to")
    sort_by: str = Field(default="total_usage_days", description="Field to sort by")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class DeviceUsageListResponse(BaseModel):
    """Schema for device usage statistics list response."""
    devices: List[DeviceUsageStatistics]
    total: int
    page: int
    page_size: int
    total_pages: int
    summary: Dict[str, Any] = Field(default_factory=dict, description="Summary statistics")


class DeviceUsageSummary(BaseModel):
    """Schema for device usage summary statistics."""
    total_devices: int
    devices_with_usage: int
    devices_never_used: int
    total_usage_days_all: int
    average_usage_per_device: float
    most_used_device: Optional[Dict[str, Any]]
    least_used_device: Optional[Dict[str, Any]]
    devices_by_condition: Dict[str, int]
    devices_by_status: Dict[str, int]
    usage_by_year: Dict[str, int]