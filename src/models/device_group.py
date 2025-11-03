"""Device Group models for grouping devices - FIXED."""

from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, Column
from sqlalchemy import ForeignKey

# ❌ REMOVE all model imports:
# from .perangkat import Device
# from .device_child import DeviceChild
# from .user import User


class DeviceGroup(SQLModel, table=True):
    """Device group model - allows users to group devices for batch operations."""
    
    __tablename__ = "device_groups"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, description="Group name")
    description: Optional[str] = Field(None, description="Group description")
    
    # Owner
    user_id: int = Field(foreign_key="users.id", description="User who created this group")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, 
        sa_column_kwargs={"onupdate": datetime.utcnow}
    )
    
    # ✅ Relationships - ALL STRING ANNOTATIONS
    user: Optional["User"] = Relationship(back_populates="device_groups")
    group_items: List["DeviceGroupItem"] = Relationship(
        back_populates="group",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    
    def __repr__(self):
        return f"<DeviceGroup id={self.id} name={self.name} user_id={self.user_id}>"


class DeviceGroupItem(SQLModel, table=True):
    """Association table for devices in a group."""
    
    __tablename__ = "device_group_items"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="device_groups.id", description="Device group ID")
    
    # Device reference (either parent device OR child device)
    device_id: Optional[int] = Field(
        default=None,
        sa_column=Column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=True),
        description="Parent device ID"
    )
    child_device_id: Optional[int] = Field(
        default=None,
        sa_column=Column(ForeignKey("device_children.id", ondelete="CASCADE"), nullable=True),
        description="Child device ID"
    )
    
    # Timestamps
    added_at: datetime = Field(default_factory=datetime.utcnow)
    
    # ✅ Relationships - ALL STRING ANNOTATIONS
    group: Optional["DeviceGroup"] = Relationship(back_populates="group_items")
    device: Optional["Device"] = Relationship()
    child_device: Optional["DeviceChild"] = Relationship()
    
    def __repr__(self):
        return f"<DeviceGroupItem id={self.id} group_id={self.group_id} device_id={self.device_id} child_device_id={self.child_device_id}>"