from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class EmployeeBase(BaseModel):
    nama: str = Field(..., max_length=255)
    nip: str = Field(..., max_length=50)
    jabatan: str = Field(..., max_length=255)


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    nama: Optional[str] = Field(None, max_length=255)
    nip: Optional[str] = Field(None, max_length=50)
    jabatan: Optional[str] = Field(None, max_length=255)


class EmployeeResponse(EmployeeBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
