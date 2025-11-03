"""Device Group schemas for API validation."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Device Group Item Schemas
# ============================================================================

class DeviceGroupItemBase(BaseModel):
    """Base schema for device group item."""
    device_id: Optional[int] = None
    child_device_id: Optional[int] = None
    
    @field_validator('device_id', 'child_device_id')
    @classmethod
    def validate_device_reference(cls, v, info):
        """Ensure at least one device reference is provided."""
        # This will be checked in the create method
        return v


class DeviceGroupItemCreate(DeviceGroupItemBase):
    """Schema for adding device to group."""
    pass


class DeviceGroupItemResponse(DeviceGroupItemBase):
    """Response schema for device group item with details."""
    id: int
    group_id: int
    added_at: datetime
    
    # Device details (populated from relationships)
    device_name: Optional[str] = None
    device_code: Optional[str] = None
    device_status: Optional[str] = None
    device_condition: Optional[str] = None
    is_available: bool = False
    
    class Config:
        from_attributes = True


# ============================================================================
# Device Group Schemas
# ============================================================================

class DeviceGroupBase(BaseModel):
    """Base schema for device group."""
    name: str = Field(..., min_length=1, max_length=100, description="Group name")
    description: Optional[str] = Field(None, max_length=500, description="Group description")


class DeviceGroupCreate(DeviceGroupBase):
    """Schema for creating a device group."""
    device_ids: Optional[List[int]] = Field(default_factory=list, description="List of parent device IDs to add")
    child_device_ids: Optional[List[int]] = Field(default_factory=list, description="List of child device IDs to add")


class DeviceGroupUpdate(BaseModel):
    """Schema for updating a device group."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Group name")
    description: Optional[str] = Field(None, max_length=500, description="Group description")


class DeviceGroupAddDevices(BaseModel):
    """Schema for adding devices to a group."""
    device_ids: Optional[List[int]] = Field(default_factory=list, description="Parent device IDs to add")
    child_device_ids: Optional[List[int]] = Field(default_factory=list, description="Child device IDs to add")


class DeviceGroupRemoveDevices(BaseModel):
    """Schema for removing devices from a group."""
    device_ids: Optional[List[int]] = Field(default_factory=list, description="Parent device IDs to remove")
    child_device_ids: Optional[List[int]] = Field(default_factory=list, description="Child device IDs to remove")


class DeviceGroupResponse(DeviceGroupBase):
    """Response schema for device group."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    device_count: int = Field(0, description="Total number of devices in group")
    
    class Config:
        from_attributes = True


class DeviceGroupDetailResponse(DeviceGroupResponse):
    """Detailed response schema for device group with all devices."""
    devices: List[DeviceGroupItemResponse] = Field(default_factory=list)
    all_available: bool = Field(False, description="True if all devices in group are available")
    unavailable_devices: List[str] = Field(default_factory=list, description="List of unavailable device names")
    
    class Config:
        from_attributes = True


class DeviceGroupListResponse(BaseModel):
    """Paginated list response for device groups."""
    groups: List[DeviceGroupResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    class Config:
        from_attributes = True


# ============================================================================
# Batch Borrow Schema
# ============================================================================

class DeviceGroupBorrowRequest(BaseModel):
    """Schema for borrowing all devices in a group."""
    borrower_name: str = Field(..., description="Nama pengguna")
    activity_name: str = Field(..., description="Nama kegiatan")
    assignment_letter_number: str = Field(..., description="Nomor surat tugas")
    assignment_letter_date: str = Field(..., description="Tanggal surat tugas (YYYY-MM-DD)")
    loan_start_date: str = Field(..., description="Tanggal mulai peminjaman (YYYY-MM-DD)")
    usage_duration_days: int = Field(..., ge=1, description="Durasi penggunaan dalam hari")
    purpose: Optional[str] = Field(None, description="Tujuan peminjaman")
    monitoring_devices: Optional[str] = Field(None, description="Perangkat monitoring")
    pihak_1_id: Optional[int] = Field(None, description="Pihak 1 (Penanggung Jawab)")
    pihak_2_id: Optional[int] = Field(None, description="Pihak 2 (Mengetahui)")


class DeviceGroupBorrowResponse(BaseModel):
    """Response schema for group borrow operation."""
    success: bool
    message: str
    loan_id: Optional[int] = None
    borrowed_devices: List[str] = Field(default_factory=list)
    unavailable_devices: List[dict] = Field(default_factory=list)
    
    class Config:
        from_attributes = True