"""Location repository for database operations."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List, Optional
from src.models.location import Location
from src.models.perangkat import Device


class LocationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, location: Location) -> Location:
        self.session.add(location)
        await self.session.commit()
        await self.session.refresh(location)
        return location

    async def get_all(self) -> List[Location]:
        result = await self.session.execute(select(Location))
        return result.scalars().all()

    async def get_by_type(self, location_type: str) -> List[Location]:
        result = await self.session.execute(
            select(Location).where(Location.type == location_type)
        )
        return result.scalars().all()

    async def get_by_id(self, location_id: int) -> Optional[Location]:
        result = await self.session.execute(select(Location).where(Location.id == location_id))
        return result.scalar_one_or_none()

    async def update(self, location: Location, data: dict) -> Location:
        for key, value in data.items():
            setattr(location, key, value)
        self.session.add(location)
        await self.session.commit()
        await self.session.refresh(location)
        return location

    async def delete(self, location: Location):
        await self.session.delete(location)
        await self.session.commit()

    async def get_devices_for_location(self, location: Location) -> List[Device]:
        """Get devices that are in this station or room."""
        if location.type == "STASIUN":
            result = await self.session.execute(
                select(Device).where(Device.device_station == location.name)
            )
        else:
            result = await self.session.execute(
                select(Device).where(Device.device_room == location.name)
            )
        return result.scalars().all()
