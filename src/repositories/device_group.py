"""Device Group repository for database operations."""

from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.device_group import DeviceGroup, DeviceGroupItem
from src.models.perangkat import Device, DeviceStatus
from src.models.device_child import DeviceChild


class DeviceGroupRepository:
    """Repository for device group database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_group(self, group_data: Dict[str, Any]) -> DeviceGroup:
        """Create a new device group."""
        group = DeviceGroup(**group_data)
        self.session.add(group)
        await self.session.flush()
        await self.session.refresh(group)
        return group
    
    async def get_group(self, group_id: int) -> Optional[DeviceGroup]:
        """Get device group by ID with relationships."""
        query = (
            select(DeviceGroup)
            .options(
                selectinload(DeviceGroup.group_items)
                .selectinload(DeviceGroupItem.device),
                selectinload(DeviceGroup.group_items)
                .selectinload(DeviceGroupItem.child_device)
            )
            .where(DeviceGroup.id == group_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_groups(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[DeviceGroup], int]:
        """Get all groups for a user with pagination."""
        # Base query
        query = (
            select(DeviceGroup)
            .options(selectinload(DeviceGroup.group_items))
            .where(DeviceGroup.user_id == user_id)
        )
        
        # Apply filters
        if filters:
            if filters.get("name"):
                query = query.where(DeviceGroup.name.ilike(f"%{filters['name']}%"))
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()
        
        # Apply pagination and ordering
        query = query.order_by(DeviceGroup.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        groups = result.scalars().all()
        
        return list(groups), total
    
    async def update_group(self, group_id: int, update_data: Dict[str, Any]) -> Optional[DeviceGroup]:
        """Update device group."""
        group = await self.get_group(group_id)
        if not group:
            return None
        
        for key, value in update_data.items():
            if value is not None and hasattr(group, key):
                setattr(group, key, value)
        
        await self.session.flush()
        await self.session.refresh(group)
        return group
    
    async def delete_group(self, group_id: int) -> bool:
        """Delete device group (hard delete)."""
        group = await self.get_group(group_id)
        if not group:
            return False
        
        await self.session.delete(group)
        await self.session.flush()
        return True
    
    async def add_device_to_group(
        self, 
        group_id: int, 
        device_id: Optional[int] = None,
        child_device_id: Optional[int] = None
    ) -> Optional[DeviceGroupItem]:
        """Add a device to a group."""
        # Check if device already in group
        existing_query = (
            select(DeviceGroupItem)
            .where(DeviceGroupItem.group_id == group_id)
        )
        
        if device_id:
            existing_query = existing_query.where(DeviceGroupItem.device_id == device_id)
        if child_device_id:
            existing_query = existing_query.where(DeviceGroupItem.child_device_id == child_device_id)
        
        result = await self.session.execute(existing_query)
        existing = result.scalar_one_or_none()
        
        if existing:
            return None  # Already exists
        
        item = DeviceGroupItem(
            group_id=group_id,
            device_id=device_id,
            child_device_id=child_device_id
        )
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item)
        return item
    
    async def remove_device_from_group(
        self, 
        group_id: int, 
        device_id: Optional[int] = None,
        child_device_id: Optional[int] = None
    ) -> bool:
        """Remove a device from a group."""
        query = delete(DeviceGroupItem).where(
            DeviceGroupItem.group_id == group_id
        )
        
        if device_id:
            query = query.where(DeviceGroupItem.device_id == device_id)
        if child_device_id:
            query = query.where(DeviceGroupItem.child_device_id == child_device_id)
        
        result = await self.session.execute(query)
        await self.session.flush()
        return result.rowcount > 0
    
    async def get_group_devices(self, group_id: int) -> List[DeviceGroupItem]:
        """Get all devices in a group with full details."""
        query = (
            select(DeviceGroupItem)
            .options(
                selectinload(DeviceGroupItem.device),
                selectinload(DeviceGroupItem.child_device)
            )
            .where(DeviceGroupItem.group_id == group_id)
            .order_by(DeviceGroupItem.added_at)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def check_group_devices_availability(self, group_id: int) -> Dict[str, Any]:
        """Check if all devices in a group are available."""
        items = await self.get_group_devices(group_id)
        
        all_available = True
        unavailable = []
        device_details = []
        
        for item in items:
            device = item.device if item.device_id else item.child_device
            if not device:
                continue
            
            is_available = device.device_status == DeviceStatus.TERSEDIA
            
            device_info = {
                "id": device.id,
                "name": device.device_name,
                "code": device.device_code,
                "status": device.device_status.value if isinstance(device.device_status, DeviceStatus) else device.device_status,
                "is_available": is_available,
                "is_child": item.child_device_id is not None
            }
            
            device_details.append(device_info)
            
            if not is_available:
                all_available = False
                unavailable.append(device_info)
        
        return {
            "all_available": all_available,
            "unavailable_devices": unavailable,
            "total_devices": len(device_details),
            "available_count": len(device_details) - len(unavailable),
            "device_details": device_details
        }
    
    async def get_device(self, device_id: int) -> Optional[Device]:
        """Get device by ID."""
        result = await self.session.execute(
            select(Device).where(Device.id == device_id)
        )
        return result.scalar_one_or_none()
    
    async def get_child_device(self, child_device_id: int) -> Optional[DeviceChild]:
        """Get child device by ID."""
        result = await self.session.execute(
            select(DeviceChild).where(DeviceChild.id == child_device_id)
        )
        return result.scalar_one_or_none()