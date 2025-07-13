"""Loan models for device loan system."""

from typing import Optional, List
from datetime import datetime, date
from enum import Enum
from sqlmodel import Field, SQLModel, Relationship, Column, String
from sqlalchemy import Enum as SQLEnum

from .base import BaseModel
from .perangkat import Device
from .user import User


class LoanStatus(str, Enum):
    """Loan status enumeration."""
    ACTIVE = "ACTIVE"
    RETURNED = "RETURNED"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class DeviceCondition(str, Enum):
    """Device condition enumeration."""
    BAIK = "BAIK"
    RUSAK_RINGAN = "RUSAK_RINGAN"
    RUSAK_BERAT = "RUSAK_BERAT"


class DeviceLoan(BaseModel, SQLModel, table=True):
    """Main device loan table."""
    
    __tablename__ = "device_loans"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    loan_number: str = Field(unique=True, index=True, description="Auto-generated loan number (BA-YYYY-MM-XXX)")
    
    # Assignment letter fields
    assignment_letter_number: str = Field(index=True, description="Nomor surat tugas")
    assignment_letter_date: date = Field(description="Tanggal surat tugas")
    
    # Borrower information
    borrower_name: str = Field(description="Nama pengguna")
    borrower_user_id: int = Field(foreign_key="users.id", description="ID user peminjam")
    
    # Activity details
    activity_name: str = Field(description="Nama kegiatan")
    usage_duration_days: int = Field(ge=1, description="Lama penggunaan dalam hari")
    loan_start_date: date = Field(description="Tanggal mulai peminjaman")
    loan_end_date: date = Field(description="Tanggal akhir peminjaman (calculated)")
    
    # Optional fields
    purpose: Optional[str] = Field(None, description="Tujuan penggunaan")
    monitoring_devices: Optional[str] = Field(None, description="Perangkat monitoring")
    
    # Status and dates
    status: LoanStatus = Field(default=LoanStatus.ACTIVE, sa_column=Column(SQLEnum(LoanStatus)))
    actual_return_date: Optional[date] = Field(None, description="Tanggal pengembalian aktual")
    
    # Return information
    return_notes: Optional[str] = Field(None, description="Catatan pengembalian")
    returned_by_user_id: Optional[int] = Field(None, foreign_key="users.id", description="User yang mengembalikan")
    
    # Relationships
    borrower: Optional[User] = Relationship(
        back_populates="loans",
        sa_relationship_kwargs={"foreign_keys": "DeviceLoan.borrower_user_id"}
    )
    returned_by: Optional[User] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "DeviceLoan.returned_by_user_id"}
    )
    
    # Related items and history
    loan_items: List["DeviceLoanItem"] = Relationship(
        back_populates="loan",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    loan_history: List["LoanHistory"] = Relationship(
        back_populates="loan",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class DeviceLoanItem(BaseModel, SQLModel, table=True):
    """Items (devices) in each loan."""
    
    __tablename__ = "device_loan_items"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    loan_id: int = Field(foreign_key="device_loans.id", description="ID peminjaman")
    device_id: int = Field(foreign_key="devices.id", description="ID perangkat")
    quantity: int = Field(default=1, ge=1, description="Jumlah yang dipinjam")
    
    # Device condition tracking
    condition_before: DeviceCondition = Field(
        default=DeviceCondition.BAIK, 
        sa_column=Column(SQLEnum(DeviceCondition)),
        description="Kondisi sebelum dipinjam"
    )
    condition_after: Optional[DeviceCondition] = Field(
        None, 
        sa_column=Column(SQLEnum(DeviceCondition)),
        description="Kondisi setelah dikembalikan"
    )
    
    condition_notes: Optional[str] = Field(None, description="Catatan kondisi perangkat")
    
    # Relationships
    loan: Optional[DeviceLoan] = Relationship(back_populates="loan_items")
    device: Optional[Device] = Relationship()


class LoanHistory(BaseModel, SQLModel, table=True):
    """Status change tracking for loans."""
    
    __tablename__ = "loan_history"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    loan_id: int = Field(foreign_key="device_loans.id", description="ID peminjaman")
    
    # Status change information
    old_status: Optional[LoanStatus] = Field(None, sa_column=Column(SQLEnum(LoanStatus)))
    new_status: LoanStatus = Field(sa_column=Column(SQLEnum(LoanStatus)))
    
    change_reason: Optional[str] = Field(None, description="Alasan perubahan status")
    changed_by_user_id: int = Field(foreign_key="users.id", description="User yang mengubah")
    change_date: datetime = Field(default_factory=datetime.utcnow, description="Tanggal perubahan")
    
    # Additional notes
    notes: Optional[str] = Field(None, description="Catatan tambahan")
    
    # Relationships
    loan: Optional[DeviceLoan] = Relationship(back_populates="loan_history")
    changed_by: Optional[User] = Relationship()


# Update User model to include loan relationship
# This should be added to the User model in user.py
# loans: List[DeviceLoan] = Relationship(back_populates="borrower")