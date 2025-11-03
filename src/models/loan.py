"""Loan models for device loan system - FIXED."""

from typing import Optional, List
from datetime import datetime, date
from enum import Enum
from sqlmodel import Field, SQLModel, Relationship, Column, ForeignKey
from sqlalchemy import Enum as SQLEnum

from .base import BaseModel

# ❌ REMOVE these imports - use string annotations instead:
# from .perangkat import Device
# from .device_child import DeviceChild
# from .employee import Employee
# from .user import User


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


class ConditionChangeStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DeviceLoan(BaseModel, SQLModel, table=True):
    """Main device loan table."""
    __tablename__ = "device_loans"

    id: Optional[int] = Field(default=None, primary_key=True)
    loan_number: str = Field(unique=True, index=True, description="Auto-generated loan number (BA-YYYY-MM-XXX)")

    # Foreign key fields
    pihak_1_id: Optional[int] = Field(default=None, foreign_key="employees.id")
    pihak_2_id: Optional[int] = Field(default=None, foreign_key="employees.id")

    # ✅ Relationships - USE STRING ANNOTATIONS
    pihak_1: Optional["Employee"] = Relationship(  # ← String
        back_populates="loans_as_pihak_1",
        sa_relationship_kwargs={
            "foreign_keys": "[DeviceLoan.pihak_1_id]",
            "lazy": "joined"
        }
    )
    pihak_2: Optional["Employee"] = Relationship(  # ← String
        back_populates="loans_as_pihak_2",
        sa_relationship_kwargs={
            "foreign_keys": "[DeviceLoan.pihak_2_id]",
            "lazy": "joined"
        }
    )

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

    # Status and dates
    status: LoanStatus = Field(default=LoanStatus.ACTIVE, sa_column=Column(SQLEnum(LoanStatus)))
    actual_return_date: Optional[date] = Field(None, description="Tanggal pengembalian aktual")

    # Return information
    return_notes: Optional[str] = Field(None, description="Catatan pengembalian")
    returned_by_user_id: Optional[int] = Field(None, foreign_key="users.id", description="User yang mengembalikan")

    # ✅ Relationships to User and others - STRING ANNOTATIONS
    borrower: Optional["User"] = Relationship(
        back_populates="loans",
        sa_relationship_kwargs={"foreign_keys": "[DeviceLoan.borrower_user_id]"}
    )
    returned_by: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[DeviceLoan.returned_by_user_id]"}
    )

    loan_items: List["DeviceLoanItem"] = Relationship(
        back_populates="loan",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    loan_history: List["LoanHistory"] = Relationship(
        back_populates="loan",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class DeviceLoanItem(BaseModel, SQLModel, table=True):
    __tablename__ = "device_loan_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    loan_id: int = Field(foreign_key="device_loans.id", description="ID peminjaman")

    device_id: Optional[int] = Field(
        default=None,
        sa_column=Column(ForeignKey("devices.id"), nullable=True),
        description="ID perangkat parent"
    )

    child_device_id: Optional[int] = Field(
        default=None,
        sa_column=Column(ForeignKey("device_children.id"), nullable=True),
        description="ID perangkat child jika yang dipinjam child"
    )

    quantity: int = Field(default=1, ge=1, description="Jumlah yang dipinjam")

    condition_before: DeviceCondition = Field(
        default=DeviceCondition.BAIK,
        sa_column=Column(SQLEnum(DeviceCondition)),
    )
    condition_after: Optional[DeviceCondition] = Field(
        None,
        sa_column=Column(SQLEnum(DeviceCondition)),
    )

    # ✅ STRING ANNOTATIONS
    loan: Optional["DeviceLoan"] = Relationship(back_populates="loan_items")
    device: Optional["Device"] = Relationship()
    child_device: Optional["DeviceChild"] = Relationship()
    
    condition_notes: Optional[str] = Field(
        None, description="Catatan kondisi perangkat"
    )

    condition_change_requests: List["DeviceConditionChangeRequest"] = Relationship(
        back_populates="loan_item",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


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
    
    # ✅ STRING ANNOTATIONS
    loan: Optional["DeviceLoan"] = Relationship(back_populates="loan_history")
    changed_by: Optional["User"] = Relationship()


class DeviceConditionChangeRequest(BaseModel, SQLModel, table=True):
    __tablename__ = "device_condition_change_requests"

    id: Optional[int] = Field(default=None, primary_key=True)
    loan_item_id: int = Field(foreign_key="device_loan_items.id", description="Item peminjaman terkait")
    device_id: Optional[int] = Field(default=None, foreign_key="devices.id")
    child_device_id: Optional[int] = Field(foreign_key="device_children.id", default=None)
    requested_by_user_id: int = Field(foreign_key="users.id", description="User yang meminta perubahan")

    old_condition: DeviceCondition = Field(sa_column=Column(SQLEnum(DeviceCondition)))
    new_condition: DeviceCondition = Field(sa_column=Column(SQLEnum(DeviceCondition)))

    reason: Optional[str] = Field(None, description="Alasan perubahan kondisi")
    status: ConditionChangeStatus = Field(default=ConditionChangeStatus.PENDING, sa_column=Column(SQLEnum(ConditionChangeStatus)))

    requested_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    reviewed_by_admin_id: Optional[int] = Field(None, foreign_key="users.id")

    # ✅ STRING ANNOTATIONS
    loan_item: Optional["DeviceLoanItem"] = Relationship(
        back_populates="condition_change_requests"
    )

    device: Optional["Device"] = Relationship()
    child_device: Optional["DeviceChild"] = Relationship()
    requested_by: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[DeviceConditionChangeRequest.requested_by_user_id]"}
    )
    reviewed_by: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[DeviceConditionChangeRequest.reviewed_by_admin_id]"}
    )