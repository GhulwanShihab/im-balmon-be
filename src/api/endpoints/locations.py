"""Location management endpoints with permission-based authorization."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.location import LocationRepository
from src.services.location import LocationService
from src.schemas.location import (
    LocationCreate, LocationUpdate, LocationResponse,
    LocationWithDevices, DeviceInLocation
)
from src.auth.permissions import get_current_active_user, require_permission
from src.auth.role_permissions import Permission

router = APIRouter()


async def get_location_service(session: AsyncSession = Depends(get_db)) -> LocationService:
    """Get location service dependency."""
    return LocationService(LocationRepository(session))


# ============================================================================
# READ OPERATIONS
# ============================================================================

@router.get("/", response_model=List[LocationResponse], dependencies=[Depends(require_permission(Permission.LOCATION_VIEW))])
async def list_locations(
    type: Optional[str] = Query(None, description="Filter by type: STASIUN or RUANGAN"),
    service: LocationService = Depends(get_location_service)
):
    """
    Get all locations, optionally filtered by type.
    
    **Permission Required:** LOCATION_VIEW
    """
    if type:
        return await service.get_locations_by_type(type.upper())
    return await service.get_locations()


@router.get("/{location_id}", response_model=LocationWithDevices, dependencies=[Depends(require_permission(Permission.LOCATION_VIEW))])
async def get_location(
    location_id: int,
    service: LocationService = Depends(get_location_service)
):
    """
    Get location by ID, including associated devices.
    
    **Permission Required:** LOCATION_VIEW
    """
    location = await service.get_location(location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    devices = await service.get_devices_for_location(location_id)
    device_list = [DeviceInLocation.model_validate(d) for d in devices]
    
    return LocationWithDevices(
        id=location.id,
        name=location.name,
        type=location.type,
        description=location.description,
        created_at=location.created_at,
        updated_at=location.updated_at,
        devices=device_list
    )


# ============================================================================
# CREATE OPERATIONS - Admin only
# ============================================================================

@router.post("/", response_model=LocationResponse, dependencies=[Depends(require_permission(Permission.LOCATION_CREATE))])
async def create_location(
    data: LocationCreate,
    service: LocationService = Depends(get_location_service)
):
    """
    Create a new location (station or room).
    
    **Permission Required:** LOCATION_CREATE
    """
    return await service.create_location(data)


# ============================================================================
# UPDATE OPERATIONS - Admin only
# ============================================================================

@router.put("/{location_id}", response_model=LocationResponse, dependencies=[Depends(require_permission(Permission.LOCATION_UPDATE))])
async def update_location(
    location_id: int,
    data: LocationUpdate,
    service: LocationService = Depends(get_location_service)
):
    """
    Update location information.
    
    **Permission Required:** LOCATION_UPDATE
    """
    location = await service.update_location(location_id, data)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


# ============================================================================
# DELETE OPERATIONS - Admin only
# ============================================================================

@router.delete("/{location_id}", dependencies=[Depends(require_permission(Permission.LOCATION_DELETE))])
async def delete_location(
    location_id: int,
    service: LocationService = Depends(get_location_service)
):
    """
    Delete a location.
    
    **Permission Required:** LOCATION_DELETE
    """
    success = await service.delete_location(location_id)
    if not success:
        raise HTTPException(status_code=404, detail="Location not found")
    return {"message": "Location deleted successfully"}
