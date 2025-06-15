"""Comprehensive device management endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.device import DeviceRepository
from src.services.device import DeviceService
from src.schemas.device import (
    DeviceResponse, DeviceCreate, DeviceUpdate, DeviceListResponse,
    DeviceStats, DeviceConditionUpdate, DeviceStatusUpdate
)
from src.auth.permissions import get_current_active_user, require_admin

router = APIRouter()

async def get_device_service(session: AsyncSession = Depends(get_db)) -> DeviceService:
    """Get device service dependency."""
    device_repo = DeviceRepository(session)
    return DeviceService(device_repo)


@router.get("/", response_model=DeviceListResponse)
async def get_devices(
    device_name: Optional[str] = Query(None, description="Filter by device name"),
    device_code: Optional[str] = Query(None, description="Filter by device code"),
    nup_device: Optional[str] = Query(None, description="Filter by NUP device"),
    bmn_brand: Optional[str] = Query(None, description="Filter by BMN brand"),
    sample_brand: Optional[str] = Query(None, description="Filter by sample brand"),
    device_year: Optional[int] = Query(None, description="Filter by device year"),
    device_type: Optional[str] = Query(None, description="Filter by device type"),
    device_station: Optional[str] = Query(None, description="Filter by device station"),
    device_condition: Optional[str] = Query(None, description="Filter by device condition"),
    device_status: Optional[str] = Query(None, description="Filter by device status"),
    device_room: Optional[str] = Query(None, description="Filter by device room"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    current_user: dict = Depends(get_current_active_user),
    device_service: DeviceService = Depends(get_device_service)
):
    """Get all devices with pagination and filtering."""
    filters = {}
    if device_name:
        filters["device_name"] = device_name
    if device_code:
        filters["device_code"] = device_code
    if nup_device:
        filters["nup_device"] = nup_device
    if bmn_brand:
        filters["bmn_brand"] = bmn_brand
    if sample_brand:
        filters["sample_brand"] = sample_brand
    if device_year:
        filters["device_year"] = device_year
    if device_type:
        filters["device_type"] = device_type
    if device_station:
        filters["device_station"] = device_station
    if device_condition:
        filters["device_condition"] = device_condition
    if device_status:
        filters["device_status"] = device_status
    if device_room:
        filters["device_room"] = device_room
    
    skip = (page - 1) * page_size
    return await device_service.get_all_devices(skip, page_size, filters, sort_by, sort_order)


@router.post("/", response_model=DeviceResponse, dependencies=[Depends(require_admin)])
async def create_device(
    device_data: DeviceCreate,
    device_service: DeviceService = Depends(get_device_service)
):
    """Create a new device (Admin only)."""
    return await device_service.create_device(device_data)


@router.get("/stats", response_model=DeviceStats, dependencies=[Depends(require_admin)])
async def get_device_statistics(
    device_service: DeviceService = Depends(get_device_service)
):
    """Get device statistics (Admin only)."""
    stats = await device_service.get_device_stats()
    return DeviceStats(**stats)


@router.get("/search")
async def search_devices(
    q: str = Query(..., description="Search term"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    current_user: dict = Depends(get_current_active_user),
    device_service: DeviceService = Depends(get_device_service)
):
    """Search devices by name, code, or NUP."""
    return await device_service.search_devices(q, limit)


@router.get("/condition/{condition}")
async def get_devices_by_condition(
    condition: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_active_user),
    device_service: DeviceService = Depends(get_device_service)
):
    """Get devices by condition."""
    skip = (page - 1) * page_size
    return await device_service.get_devices_by_condition(condition, skip, page_size)


@router.get("/status/{status}")
async def get_devices_by_status(
    status: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_active_user),
    device_service: DeviceService = Depends(get_device_service)
):
    """Get devices by status."""
    skip = (page - 1) * page_size
    return await device_service.get_devices_by_status(status, skip, page_size)


@router.get("/room/{room}")
async def get_devices_by_room(
    room: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_active_user),
    device_service: DeviceService = Depends(get_device_service)
):
    """Get devices by room."""
    skip = (page - 1) * page_size
    return await device_service.get_devices_by_room(room, skip, page_size)


@router.get("/type/{device_type}")
async def get_devices_by_type(
    device_type: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_active_user),
    device_service: DeviceService = Depends(get_device_service)
):
    """Get devices by type."""
    skip = (page - 1) * page_size
    return await device_service.get_devices_by_type(device_type, skip, page_size)


@router.get("/code/{device_code}", response_model=DeviceResponse)
async def get_device_by_code(
    device_code: str,
    current_user: dict = Depends(get_current_active_user),
    device_service: DeviceService = Depends(get_device_service)
):
    """Get device by code."""
    device = await device_service.get_device_by_code(device_code)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.get("/nup/{nup_device}", response_model=DeviceResponse)
async def get_device_by_nup(
    nup_device: str,
    current_user: dict = Depends(get_current_active_user),
    device_service: DeviceService = Depends(get_device_service)
):
    """Get device by NUP."""
    device = await device_service.get_device_by_nup(nup_device)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device_by_id(
    device_id: int,
    current_user: dict = Depends(get_current_active_user),
    device_service: DeviceService = Depends(get_device_service)
):
    """Get device by ID."""
    device = await device_service.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.put("/{device_id}", response_model=DeviceResponse, dependencies=[Depends(require_admin)])
async def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    device_service: DeviceService = Depends(get_device_service)
):
    """Update device information (Admin only)."""
    return await device_service.update_device(device_id, device_data)


@router.put("/{device_id}/condition", response_model=DeviceResponse, dependencies=[Depends(require_admin)])
async def update_device_condition(
    device_id: int,
    condition_data: DeviceConditionUpdate,
    device_service: DeviceService = Depends(get_device_service)
):
    """Update device condition (Admin only)."""
    return await device_service.update_device_condition(device_id, condition_data)


@router.put("/{device_id}/status", response_model=DeviceResponse, dependencies=[Depends(require_admin)])
async def update_device_status(
    device_id: int,
    status_data: DeviceStatusUpdate,
    device_service: DeviceService = Depends(get_device_service)
):
    """Update device status (Admin only)."""
    return await device_service.update_device_status(device_id, status_data)


@router.delete("/{device_id}", dependencies=[Depends(require_admin)])
async def delete_device(
    device_id: int,
    device_service: DeviceService = Depends(get_device_service)
):
    """Delete device (soft delete, Admin only)."""
    success = await device_service.delete_device(device_id)
    return {"message": "Device deleted successfully"}