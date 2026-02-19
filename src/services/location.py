"""Location service for business logic."""

from typing import List
from src.models.location import Location
from src.models.perangkat import Device
from src.repositories.location import LocationRepository
from src.schemas.location import LocationCreate, LocationUpdate


class LocationService:
    def __init__(self, repo: LocationRepository):
        self.repo = repo

    async def create_location(self, data: LocationCreate) -> Location:
        location = Location(**data.model_dump())
        return await self.repo.create(location)

    async def get_locations(self) -> List[Location]:
        return await self.repo.get_all()

    async def get_locations_by_type(self, location_type: str) -> List[Location]:
        return await self.repo.get_by_type(location_type)

    async def get_location(self, location_id: int) -> Location:
        return await self.repo.get_by_id(location_id)

    async def update_location(self, location_id: int, data: LocationUpdate) -> Location:
        location = await self.repo.get_by_id(location_id)
        if not location:
            return None
        return await self.repo.update(location, data.model_dump(exclude_unset=True))

    async def delete_location(self, location_id: int) -> bool:
        location = await self.repo.get_by_id(location_id)
        if not location:
            return False
        await self.repo.delete(location)
        return True

    async def get_devices_for_location(self, location_id: int) -> List[Device]:
        location = await self.repo.get_by_id(location_id)
        if not location:
            return []
        return await self.repo.get_devices_for_location(location)
