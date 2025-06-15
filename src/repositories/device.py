"""Device repository for database operations."""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.perangkat import Device
from src.schemas.device import DeviceCreate, DeviceUpdate


class DeviceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, device_id: int) -> Optional[Device]:
        """Get device by ID."""
        query = select(Device).where(
            and_(Device.id == device_id, Device.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_code(self, device_code: str) -> Optional[Device]:
        """Get device by code."""
        query = select(Device).where(
            and_(Device.device_code == device_code, Device.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_nup(self, nup_device: str) -> Optional[Device]:
        """Get device by NUP."""
        query = select(Device).where(
            and_(Device.nup_device == nup_device, Device.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, device_data: DeviceCreate) -> Device:
        """Create a new device."""
        device = Device(
            device_name=device_data.device_name,
            device_code=device_data.device_code,
            nup_device=device_data.nup_device,
            bmn_brand=device_data.bmn_brand,
            sample_brand=device_data.sample_brand,
            device_year=device_data.device_year,
            device_type=device_data.device_type,
            device_station=device_data.device_station,
            device_condition=device_data.device_condition,
            device_status=device_data.device_status,
            description=device_data.description,
            device_room=device_data.device_room,
            photos_url=device_data.photos_url,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.session.add(device)
        await self.session.commit()
        await self.session.refresh(device)
        return device

    async def update(self, device_id: int, device_data: DeviceUpdate) -> Optional[Device]:
        """Update device."""
        device = await self.get_by_id(device_id)
        if not device:
            return None

        update_data = device_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(device, key, value)

        device.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(device)
        return device

    async def delete(self, device_id: int) -> bool:
        """Soft delete device."""
        query = (
            update(Device)
            .where(Device.id == device_id)
            .values(deleted_at=datetime.utcnow(), updated_at=datetime.utcnow())
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0

    async def get_all(self, skip: int = 0, limit: int = 10, filters: dict = None, sort_by: str = "created_at", sort_order: str = "desc") -> List[Device]:
        """Get all devices with pagination and filtering."""
        query = select(Device).where(Device.deleted_at.is_(None))
        
        # Apply filters
        if filters:
            if filters.get("device_name"):
                query = query.where(Device.device_name.ilike(f"%{filters['device_name']}%"))
            if filters.get("device_code"):
                query = query.where(Device.device_code.ilike(f"%{filters['device_code']}%"))
            if filters.get("nup_device"):
                query = query.where(Device.nup_device.ilike(f"%{filters['nup_device']}%"))
            if filters.get("bmn_brand"):
                query = query.where(Device.bmn_brand.ilike(f"%{filters['bmn_brand']}%"))
            if filters.get("sample_brand"):
                query = query.where(Device.sample_brand.ilike(f"%{filters['sample_brand']}%"))
            if filters.get("device_year"):
                query = query.where(Device.device_year == filters["device_year"])
            if filters.get("device_type"):
                query = query.where(Device.device_type.ilike(f"%{filters['device_type']}%"))
            if filters.get("device_station"):
                query = query.where(Device.device_station.ilike(f"%{filters['device_station']}%"))
            if filters.get("device_condition"):
                query = query.where(Device.device_condition == filters["device_condition"])
            if filters.get("device_status"):
                query = query.where(Device.device_status == filters["device_status"])
            if filters.get("device_room"):
                query = query.where(Device.device_room.ilike(f"%{filters['device_room']}%"))
        
        # Apply sorting
        if hasattr(Device, sort_by):
            if sort_order == "desc":
                query = query.order_by(getattr(Device, sort_by).desc())
            else:
                query = query.order_by(getattr(Device, sort_by))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count(self, filters: dict = None) -> int:
        """Count total devices with filters."""
        query = select(func.count(Device.id)).where(Device.deleted_at.is_(None))
        
        # Apply filters
        if filters:
            if filters.get("device_name"):
                query = query.where(Device.device_name.ilike(f"%{filters['device_name']}%"))
            if filters.get("device_code"):
                query = query.where(Device.device_code.ilike(f"%{filters['device_code']}%"))
            if filters.get("nup_device"):
                query = query.where(Device.nup_device.ilike(f"%{filters['nup_device']}%"))
            if filters.get("bmn_brand"):
                query = query.where(Device.bmn_brand.ilike(f"%{filters['bmn_brand']}%"))
            if filters.get("sample_brand"):
                query = query.where(Device.sample_brand.ilike(f"%{filters['sample_brand']}%"))
            if filters.get("device_year"):
                query = query.where(Device.device_year == filters["device_year"])
            if filters.get("device_type"):
                query = query.where(Device.device_type.ilike(f"%{filters['device_type']}%"))
            if filters.get("device_station"):
                query = query.where(Device.device_station.ilike(f"%{filters['device_station']}%"))
            if filters.get("device_condition"):
                query = query.where(Device.device_condition == filters["device_condition"])
            if filters.get("device_status"):
                query = query.where(Device.device_status == filters["device_status"])
            if filters.get("device_room"):
                query = query.where(Device.device_room.ilike(f"%{filters['device_room']}%"))
        
        result = await self.session.execute(query)
        return result.scalar()

    async def get_stats(self) -> dict:
        """Get comprehensive device statistics."""
        # Total devices
        total_query = select(func.count(Device.id)).where(Device.deleted_at.is_(None))
        total_result = await self.session.execute(total_query)
        total_devices = total_result.scalar()
        
        # Active devices (assuming 'Aktif' status means active)
        active_query = select(func.count(Device.id)).where(
            and_(Device.deleted_at.is_(None), Device.device_status == "Aktif")
        )
        active_result = await self.session.execute(active_query)
        active_devices = active_result.scalar()
        
        # Inactive devices
        inactive_devices = total_devices - active_devices
        
        # Devices by condition
        condition_query = select(Device.device_condition, func.count(Device.id)).where(
            Device.deleted_at.is_(None)
        ).group_by(Device.device_condition)
        condition_result = await self.session.execute(condition_query)
        devices_by_condition = {row[0] or "Unknown": row[1] for row in condition_result.fetchall()}
        
        # Devices by status
        status_query = select(Device.device_status, func.count(Device.id)).where(
            Device.deleted_at.is_(None)
        ).group_by(Device.device_status)
        status_result = await self.session.execute(status_query)
        devices_by_status = {row[0] or "Unknown": row[1] for row in status_result.fetchall()}
        
        # Devices by type
        type_query = select(Device.device_type, func.count(Device.id)).where(
            Device.deleted_at.is_(None)
        ).group_by(Device.device_type)
        type_result = await self.session.execute(type_query)
        devices_by_type = {row[0] or "Unknown": row[1] for row in type_result.fetchall()}
        
        # Devices by room
        room_query = select(Device.device_room, func.count(Device.id)).where(
            Device.deleted_at.is_(None)
        ).group_by(Device.device_room)
        room_result = await self.session.execute(room_query)
        devices_by_room = {row[0] or "Unknown": row[1] for row in room_result.fetchall()}
        
        # New devices statistics
        today = datetime.utcnow().date()
        week_ago = datetime.utcnow() - timedelta(days=7)
        month_ago = datetime.utcnow() - timedelta(days=30)
        
        # New devices today
        today_query = select(func.count(Device.id)).where(
            and_(Device.deleted_at.is_(None), func.date(Device.created_at) == today)
        )
        today_result = await self.session.execute(today_query)
        new_devices_today = today_result.scalar()
        
        # New devices this week
        week_query = select(func.count(Device.id)).where(
            and_(Device.deleted_at.is_(None), Device.created_at >= week_ago)
        )
        week_result = await self.session.execute(week_query)
        new_devices_this_week = week_result.scalar()
        
        # New devices this month
        month_query = select(func.count(Device.id)).where(
            and_(Device.deleted_at.is_(None), Device.created_at >= month_ago)
        )
        month_result = await self.session.execute(month_query)
        new_devices_this_month = month_result.scalar()
        
        return {
            "total_devices": total_devices,
            "active_devices": active_devices,
            "inactive_devices": inactive_devices,
            "devices_by_condition": devices_by_condition,
            "devices_by_status": devices_by_status,
            "devices_by_type": devices_by_type,
            "devices_by_room": devices_by_room,
            "new_devices_today": new_devices_today,
            "new_devices_this_week": new_devices_this_week,
            "new_devices_this_month": new_devices_this_month
        }

    async def update_condition(self, device_id: int, condition: str) -> Optional[Device]:
        """Update device condition."""
        device = await self.get_by_id(device_id)
        if not device:
            return None
        
        device.device_condition = condition
        device.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(device)
        return device

    async def update_status(self, device_id: int, status: str) -> Optional[Device]:
        """Update device status."""
        device = await self.get_by_id(device_id)
        if not device:
            return None
        
        device.device_status = status
        device.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(device)
        return device

    async def search_devices(self, search_term: str, limit: int = 10) -> List[Device]:
        """Search devices by name, code, or NUP."""
        query = select(Device).where(
            and_(
                Device.deleted_at.is_(None),
                (
                    Device.device_name.ilike(f"%{search_term}%") |
                    Device.device_code.ilike(f"%{search_term}%") |
                    Device.nup_device.ilike(f"%{search_term}%")
                )
            )
        ).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()