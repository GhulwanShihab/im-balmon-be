from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

from .base import BaseModel


class Employee(BaseModel, SQLModel, table=True):
    """Model for employee data."""
    __tablename__ = "employees"

    id: Optional[int] = Field(default=None, primary_key=True)
    nama: str = Field(index=True, max_length=255)
    nip: str = Field(index=True, max_length=50, unique=True)
    jabatan: str = Field(max_length=255)

    loans_as_pihak_1: List["DeviceLoan"] = Relationship(
        back_populates="pihak_1",
        sa_relationship_kwargs={"foreign_keys": "[DeviceLoan.pihak_1_id]"},
    )
    loans_as_pihak_2: List["DeviceLoan"] = Relationship(
        back_populates="pihak_2",
        sa_relationship_kwargs={"foreign_keys": "[DeviceLoan.pihak_2_id]"},
    )
