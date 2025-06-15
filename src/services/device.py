"""Device service for business logic."""

from typing import Optional
from fastapi import HTTPException, status

from src.repositories.device import DeviceRepository
from src.schemas.device import (
    DeviceCreate, DeviceUpdate, DeviceResponse, DeviceListResponse,
    DeviceConditionUpdate, DeviceStatusUpdate
)


class DeviceService:
    def __init__(self, device_repo: DeviceRepository):
        self.device_repo = device_repo

    async def create_device(self, device_data: DeviceCreate) -> DeviceResponse:
        """Create a new device with validation."""
        # Check if device code already exists
        existing_device = await self.device_repo.get_by_code(device_data.device_code)
        if existing_device:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device code already exists"
            )
        
        # Check if NUP already exists
        existing_nup = await self.device_repo.get_by_nup(device_data.nup_device)
        if existing_nup:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="NUP device already exists"
            )
        
        # Create device
        device = await self.device_repo.create(device_data)
        return DeviceResponse.model_validate(device)

    async def get_device(self, device_id: int) -> Optional[DeviceResponse]:
        """Get device by ID."""
        device = await self.device_repo.get_by_id(device_id)
        if not device:
            return None
        
        return DeviceResponse.model_validate(device)

    async def get_device_by_code(self, device_code: str) -> Optional[DeviceResponse]:
        """Get device by code."""
        device = await self.device_repo.get_by_code(device_code)
        if not device:
            return None
        
        return DeviceResponse.model_validate(device)

    async def get_device_by_nup(self, nup_device: str) -> Optional[DeviceResponse]:
        """Get device by NUP."""
        device = await self.device_repo.get_by_nup(nup_device)
        if not device:
            return None
        
        return DeviceResponse.model_validate(device)

    async def get_all_devices(self, skip: int = 0, limit: int = 10, filters: dict = None, sort_by: str = "created_at", sort_order: str = "desc") -> DeviceListResponse:
        """Get all devices with pagination and filtering."""
        devices = await self.device_repo.get_all(skip, limit, filters, sort_by, sort_order)
        total = await self.device_repo.count(filters)
        
        device_responses = [DeviceResponse.model_validate(device) for device in devices]
        
        total_pages = (total + limit - 1) // limit
        page = (skip // limit) + 1
        
        return DeviceListResponse(
            devices=device_responses,
            total=total,
            page=page,
            page_size=limit,
            total_pages=total_pages
        )

    async def update_device(self, device_id: int, device_data: DeviceUpdate) -> DeviceResponse:
        """Update device information."""
        # Check if device exists
        existing_device = await self.device_repo.get_by_id(device_id)
        if not existing_device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        # Check if device code is being updated and already exists
        if device_data.device_code and device_data.device_code != existing_device.device_code:
            existing_code = await self.device_repo.get_by_code(device_data.device_code)
            if existing_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Device code already exists"
                )
        
        # Check if NUP is being updated and already exists
        if device_data.nup_device and device_data.nup_device != existing_device.nup_device:
            existing_nup = await self.device_repo.get_by_nup(device_data.nup_device)
            if existing_nup:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="NUP device already exists"
                )
        
        device = await self.device_repo.update(device_id, device_data)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        return DeviceResponse.model_validate(device)

    async def delete_device(self, device_id: int) -> bool:
        """Delete device (soft delete)."""
        success = await self.device_repo.delete(device_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        return success

    async def get_device_stats(self) -> dict:
        """Get device statistics."""
        return await self.device_repo.get_stats()

    async def update_device_condition(self, device_id: int, condition_data: DeviceConditionUpdate) -> DeviceResponse:
        """Update device condition."""
        device = await self.device_repo.update_condition(device_id, condition_data.device_condition)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        return DeviceResponse.model_validate(device)

    async def update_device_status(self, device_id: int, status_data: DeviceStatusUpdate) -> DeviceResponse:
        """Update device status."""
        device = await self.device_repo.update_status(device_id, status_data.device_status)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        return DeviceResponse.model_validate(device)

    async def search_devices(self, search_term: str, limit: int = 10) -> list[DeviceResponse]:
        """Search devices by name, code, or NUP."""
        devices = await self.device_repo.search_devices(search_term, limit)
        return [DeviceResponse.model_validate(device) for device in devices]

    async def get_devices_by_condition(self, condition: str, skip: int = 0, limit: int = 10) -> DeviceListResponse:
        """Get devices by condition."""
        filters = {"device_condition": condition}
        return await self.get_all_devices(skip, limit, filters)

    async def get_devices_by_status(self, status: str, skip: int = 0, limit: int = 10) -> DeviceListResponse:
        """Get devices by status."""
        filters = {"device_status": status}
        return await self.get_all_devices(skip, limit, filters)

    async def get_devices_by_room(self, room: str, skip: int = 0, limit: int = 10) -> DeviceListResponse:
        """Get devices by room."""
        filters = {"device_room": room}
        return await self.get_all_devices(skip, limit, filters)

    async def get_devices_by_type(self, device_type: str, skip: int = 0, limit: int = 10) -> DeviceListResponse:
        """Get devices by type."""
        filters = {"device_type": device_type}
        return await self.get_all_devices(skip, limit, filters)