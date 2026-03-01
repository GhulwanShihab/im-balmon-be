from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import ForeignKey
from datetime import datetime

from .base import BaseModel


class Employee(BaseModel, SQLModel, table=True):
    """Model for employee data."""
    __tablename__ = "employees"

    id: Optional[int] = Field(default=None, primary_key=True)
    nama: str = Field(unique=True, index=True, max_length=255)
    nip: Optional[str] = Field(default=None, unique=True, index=True, max_length=50, nullable=True)
    jabatan: str = Field(max_length=255, default="Pegawai")
    is_pihak_1: bool = Field(default=False)
    user_id: Optional[int] = Field(default=None, sa_column=Column(ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True))


    loans_as_pihak_1: List["DeviceLoan"] = Relationship(
        back_populates="pihak_1",
        sa_relationship_kwargs={"foreign_keys": "[DeviceLoan.pihak_1_id]"},
    )
    loans_as_pihak_2: List["DeviceLoan"] = Relationship(
        back_populates="pihak_2",
        sa_relationship_kwargs={"foreign_keys": "[DeviceLoan.pihak_2_id]"},
    )
