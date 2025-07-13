"""Loan schemas for validation and response."""

from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re

from ..models.loan import LoanStatus, DeviceCondition


class DeviceLoanItemBase(BaseModel):
    """Base schema for loan items."""
    device_id: int = Field(..., description="ID perangkat")
    quantity: int = Field(default=1, ge=1, description="Jumlah yang dipinjam")
    condition_before: DeviceCondition = Field(default=DeviceCondition.BAIK, description="Kondisi sebelum dipinjam")
    condition_notes: Optional[str] = Field(None, description="Catatan kondisi perangkat")


class DeviceLoanItemCreate(DeviceLoanItemBase):
    """Schema for creating loan items."""
    pass


class DeviceLoanItemReturn(BaseModel):
    """Schema for returning loan items."""
    id: int = Field(..., description="ID loan item")
    condition_after: DeviceCondition = Field(..., description="Kondisi setelah dikembalikan")
    condition_notes: Optional[str] = Field(None, description="Catatan kondisi setelah dikembalikan")


class DeviceLoanItemResponse(DeviceLoanItemBase):
    """Schema for loan item response."""
    id: int
    loan_id: int
    condition_after: Optional[DeviceCondition]
    created_at: datetime
    updated_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class DeviceLoanBase(BaseModel):
    """Base schema for device loans."""
    assignment_letter_number: str = Field(
        ..., 
        description="Nomor surat tugas - Format: XX/BALMON.18/KP.01.06/XX XX/YYYY"
    )
    assignment_letter_date: date = Field(..., description="Tanggal surat tugas")
    borrower_name: str = Field(..., min_length=1, max_length=255, description="Nama pengguna")
    activity_name: str = Field(..., min_length=1, max_length=255, description="Nama kegiatan")
    usage_duration_days: int = Field(..., ge=1, le=365, description="Lama penggunaan dalam hari")
    loan_start_date: date = Field(..., description="Tanggal mulai peminjaman")
    purpose: Optional[str] = Field(None, max_length=1000, description="Tujuan penggunaan")
    monitoring_devices: Optional[str] = Field(None, max_length=500, description="Perangkat monitoring")
    
    @field_validator('assignment_letter_number')
    @classmethod
    def validate_assignment_letter_number(cls, v: str) -> str:
        """
        Validate assignment letter number format.
        Format: XX/BALMON.18/KP.01.06/XX XX/YYYY
        Example: 03/BALMON.18/KP.01.06/LAB 01/2025
        """
        if not v:
            raise ValueError("Assignment letter number is required")
        
        # Regex pattern for validation
        pattern = r'^\d+/BALMON\.18/KP\.01\.06/[A-Z0-9]+ \d+/\d{4}$'
        
        if not re.match(pattern, v.strip()):
            raise ValueError(
                "Assignment letter number format is invalid. "
                "Required format: XX/BALMON.18/KP.01.06/XX XX/YYYY "
                "Example: 03/BALMON.18/KP.01.06/LAB 01/2025"
            )
        
        return v.strip()
    
    @field_validator('loan_start_date')
    @classmethod
    def validate_loan_start_date(cls, v: date) -> date:
        """Validate loan start date is not in the past."""
        if v < date.today():
            raise ValueError("Loan start date cannot be in the past")
        return v
    
    @field_validator('assignment_letter_date')
    @classmethod
    def validate_assignment_letter_date(cls, v: date) -> date:
        """Validate assignment letter date is reasonable."""
        if v > date.today():
            raise ValueError("Assignment letter date cannot be in the future")
        return v


class DeviceLoanCreate(DeviceLoanBase):
    """Schema for creating a device loan."""
    loan_items: List[DeviceLoanItemCreate] = Field(..., min_length=1, description="Daftar perangkat yang dipinjam")


class DeviceLoanUpdate(BaseModel):
    """Schema for updating a device loan (limited fields for active loans)."""
    assignment_letter_number: Optional[str] = Field(None, description="Nomor surat tugas")
    assignment_letter_date: Optional[date] = Field(None, description="Tanggal surat tugas")
    borrower_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Nama pengguna")
    activity_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Nama kegiatan")
    purpose: Optional[str] = Field(None, max_length=1000, description="Tujuan penggunaan")
    monitoring_devices: Optional[str] = Field(None, max_length=500, description="Perangkat monitoring")
    
    @field_validator('assignment_letter_number')
    @classmethod
    def validate_assignment_letter_number(cls, v: Optional[str]) -> Optional[str]:
        """Validate assignment letter number format if provided."""
        if v is None:
            return v
        
        pattern = r'^\d+/BALMON\.18/KP\.01\.06/[A-Z0-9]+ \d+/\d{4}$'
        
        if not re.match(pattern, v.strip()):
            raise ValueError(
                "Assignment letter number format is invalid. "
                "Required format: XX/BALMON.18/KP.01.06/XX XX/YYYY "
                "Example: 03/BALMON.18/KP.01.06/LAB 01/2025"
            )
        
        return v.strip()


class DeviceLoanReturn(BaseModel):
    """Schema for returning a loan."""
    return_notes: Optional[str] = Field(None, max_length=1000, description="Catatan pengembalian")
    loan_items: List[DeviceLoanItemReturn] = Field(..., min_length=1, description="Kondisi perangkat yang dikembalikan")


class DeviceLoanCancel(BaseModel):
    """Schema for cancelling a loan."""
    cancel_reason: str = Field(..., min_length=1, max_length=500, description="Alasan pembatalan")


class DeviceLoanResponse(DeviceLoanBase):
    """Schema for loan response."""
    id: int
    loan_number: str
    borrower_user_id: int
    loan_end_date: date
    status: LoanStatus
    actual_return_date: Optional[date]
    return_notes: Optional[str]
    returned_by_user_id: Optional[int]
    loan_items: List[DeviceLoanItemResponse]
    created_at: datetime
    updated_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class DeviceLoanListResponse(BaseModel):
    """Schema for loan list response with pagination."""
    loans: List[DeviceLoanResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class DeviceLoanFilter(BaseModel):
    """Schema for loan search and filtering."""
    status: Optional[LoanStatus] = None
    borrower_name: Optional[str] = None
    activity_name: Optional[str] = None
    assignment_letter_number: Optional[str] = None
    loan_start_date_from: Optional[date] = None
    loan_start_date_to: Optional[date] = None
    loan_end_date_from: Optional[date] = None
    loan_end_date_to: Optional[date] = None
    borrower_user_id: Optional[int] = None
    device_id: Optional[int] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    sort_by: Optional[str] = Field(default="created_at", description="Field to sort by")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class LoanHistoryResponse(BaseModel):
    """Schema for loan history response."""
    id: int
    loan_id: int
    old_status: Optional[LoanStatus]
    new_status: LoanStatus
    change_reason: Optional[str]
    changed_by_user_id: int
    change_date: datetime
    notes: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


class DeviceLoanStats(BaseModel):
    """Schema for loan statistics."""
    total_loans: int
    active_loans: int
    returned_loans: int
    overdue_loans: int
    cancelled_loans: int
    loans_by_status: dict
    loans_this_month: int
    loans_this_week: int
    most_borrowed_devices: List[dict]
    top_borrowers: List[dict]


class AssignmentLetterValidation(BaseModel):
    """Schema for validating assignment letter number format."""
    assignment_letter_number: str = Field(..., description="Nomor surat tugas untuk divalidasi")
    
    @field_validator('assignment_letter_number')
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate assignment letter number format."""
        if not v:
            raise ValueError("Assignment letter number is required")
        
        pattern = r'^\d+/BALMON\.18/KP\.01\.06/[A-Z0-9]+ \d+/\d{4}$'
        
        if not re.match(pattern, v.strip()):
            raise ValueError(
                "Assignment letter number format is invalid. "
                "Required format: XX/BALMON.18/KP.01.06/XX XX/YYYY "
                "Example: 03/BALMON.18/KP.01.06/LAB 01/2025"
            )
        
        return v.strip()


class AssignmentLetterValidationResponse(BaseModel):
    """Schema for assignment letter validation response."""
    is_valid: bool
    message: str
    example_format: str = "03/BALMON.18/KP.01.06/LAB 01/2025"


class DeviceLoanSummary(BaseModel):
    """Schema for loan summary (for exports)."""
    id: int
    loan_number: str
    assignment_letter_number: str
    borrower_name: str
    activity_name: str
    loan_start_date: date
    loan_end_date: date
    status: LoanStatus
    total_devices: int
    device_names: List[str]