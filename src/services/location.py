"""Location service for business logic."""

from typing import List
from fastapi import HTTPException
from src.models.location import Location
from src.models.perangkat import Device
from src.repositories.location import LocationRepository
from src.schemas.location import LocationCreate, LocationUpdate


class LocationService:
    def __init__(self, repo: LocationRepository):
        self.repo = repo

    def _normalize_name(self, name: str) -> str:
        """Normalize location name: strip whitespace and apply title case."""
        return name.strip().title()

    async def create_location(self, data: LocationCreate) -> Location:
        # Normalize name
        normalized_name = self._normalize_name(data.name)

        # Check for case-insensitive duplicate
        existing = await self.repo.get_by_name_and_type(normalized_name, data.type)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Lokasi '{normalized_name}' dengan tipe '{data.type}' sudah ada."
            )

        location_data = data.model_dump()
        location_data["name"] = normalized_name
        location = Location(**location_data)
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

        update_data = data.model_dump(exclude_unset=True)

        # Normalize name if provided
        if "name" in update_data and update_data["name"]:
            update_data["name"] = self._normalize_name(update_data["name"])

            # Check for case-insensitive duplicate (excluding current record)
            check_type = update_data.get("type", location.type)
            existing = await self.repo.get_by_name_and_type(update_data["name"], check_type)
            if existing and existing.id != location_id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Lokasi '{update_data['name']}' dengan tipe '{check_type}' sudah ada."
                )

        return await self.repo.update(location, update_data)

    async def delete_location(self, location_id: int) -> bool:
        location = await self.repo.get_by_id(location_id)
        if not location:
            return False
        await self.repo.delete(location)
        return True

    async def get_devices_for_location(self, location_id: int) -> List[dict]:
        location = await self.repo.get_by_id(location_id)
        if not location:
            return []
        return await self.repo.get_devices_for_location(location)

