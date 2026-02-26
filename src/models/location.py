"""Location model for managing device stations and rooms."""

from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint
from datetime import datetime

from .base import BaseModel


class Location(BaseModel, SQLModel, table=True):
    """Model for location data (stations and rooms)."""
    __tablename__ = "locations"
    __table_args__ = (
        UniqueConstraint("name", "type", name="uq_location_name_type"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, max_length=255)
    type: str = Field(max_length=20)  # "STASIUN" or "RUANGAN"
    description: Optional[str] = Field(default=None, max_length=500)
