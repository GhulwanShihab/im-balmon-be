"""Comprehensive device management endpoints with permission-based authorization."""

from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.device import DeviceRepository
from src.services.device import DeviceService
from src.schemas.device import (
    DeviceResponse, DeviceCreate, DeviceUpdate, DeviceListResponse,
    DeviceStats, DeviceConditionUpdate, DeviceStatusUpdate,
    DeviceUsageFilter, DeviceUsageListResponse, DeviceUsageSummary,
    DeviceUsageStatistics
)
from src.auth.permissions import (
    get_current_active_user, 
    require_permission,
    require_any_permission,
    require_roles
)
from src.auth.role_permissions import Permission

router = APIRouter()

async def get_device_service(session: AsyncSession = Depends(get_db)) -> DeviceService:
    """Get device service dependency."""
    device_repo = DeviceRepository(session)
    return DeviceService(device_repo)


# ============================================================================
# READ OPERATIONS - All authenticated users
# ============================================================================

@router.get("/", response_model=DeviceListResponse, dependencies=[Depends(require_permission(Permission.DEVICE_VIEW))])
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
    device_service: DeviceService = Depends(get_device_service)
):
    """
    Get all devices with pagination and filtering.
    
    **Permission Required:** DEVICE_VIEW
    **Roles:** admin, manager, user
    """
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


@router.get("/stats", response_model=DeviceStats, dependencies=[Depends(require_permission(Permission.DEVICE_STATS))])
async def get_device_statistics(
    device_service: DeviceService = Depends(get_device_service)
):
    """
    Get device statistics.
    
    **Permission Required:** DEVICE_STATS
    **Roles:** admin, manager
    """
    stats = await device_service.get_device_stats()
    return DeviceStats(**stats)


@router.get("/search", dependencies=[Depends(require_permission(Permission.DEVICE_VIEW))])
async def search_devices(
    q: str = Query(..., description="Search term"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    device_service: DeviceService = Depends(get_device_service)
):
    """
    Search devices by name, code, or NUP.
    
    **Permission Required:** DEVICE_VIEW
    **Roles:** admin, manager, user
    """
    return await device_service.search_devices(q, limit)


@router.get("/condition/{condition}", dependencies=[Depends(require_permission(Permission.DEVICE_VIEW))])
async def get_devices_by_condition(
    condition: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    device_service: DeviceService = Depends(get_device_service)
):
    """
    Get devices by condition.
    
    **Permission Required:** DEVICE_VIEW
    **Roles:** admin, manager, user
    """
    skip = (page - 1) * page_size
    return await device_service.get_devices_by_condition(condition, skip, page_size)


@router.get("/status/{status}", dependencies=[Depends(require_permission(Permission.DEVICE_VIEW))])
async def get_devices_by_status(
    status: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    device_service: DeviceService = Depends(get_device_service)
):
    """
    Get devices by status.
    
    **Permission Required:** DEVICE_VIEW
    **Roles:** admin, manager, user
    """
    skip = (page - 1) * page_size
    return await device_service.get_devices_by_status(status, skip, page_size)


@router.get("/room/{room}", dependencies=[Depends(require_permission(Permission.DEVICE_VIEW))])
async def get_devices_by_room(
    room: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    device_service: DeviceService = Depends(get_device_service)
):
    """
    Get devices by room.
    
    **Permission Required:** DEVICE_VIEW
    **Roles:** admin, manager, user
    """
    skip = (page - 1) * page_size
    return await device_service.get_devices_by_room(room, skip, page_size)


@router.get("/type/{device_type}", dependencies=[Depends(require_permission(Permission.DEVICE_VIEW))])
async def get_devices_by_type(
    device_type: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    device_service: DeviceService = Depends(get_device_service)
):
    """
    Get devices by type.
    
    **Permission Required:** DEVICE_VIEW
    **Roles:** admin, manager, user
    """
    skip = (page - 1) * page_size
    return await device_service.get_devices_by_type(device_type, skip, page_size)


@router.get("/code/{device_code}", response_model=DeviceResponse, dependencies=[Depends(require_permission(Permission.DEVICE_VIEW))])
async def get_device_by_code(
    device_code: str,
    device_service: DeviceService = Depends(get_device_service)
):
    """
    Get device by code.
    
    **Permission Required:** DEVICE_VIEW
    **Roles:** admin, manager, user
    """
    device = await device_service.get_device_by_code(device_code)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.get("/nup/{nup_device}", response_model=DeviceResponse, dependencies=[Depends(require_permission(Permission.DEVICE_VIEW))])
async def get_device_by_nup(
    nup_device: str,
    device_service: DeviceService = Depends(get_device_service)
):
    """
    Get device by NUP.
    
    **Permission Required:** DEVICE_VIEW
    **Roles:** admin, manager, user
    """
    device = await device_service.get_device_by_nup(nup_device)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.get("/{device_id}", response_model=DeviceResponse, dependencies=[Depends(require_permission(Permission.DEVICE_VIEW))])
async def get_device_by_id(
    device_id: int,
    device_service: DeviceService = Depends(get_device_service)
):
    """
    Get device by ID.
    
    **Permission Required:** DEVICE_VIEW
    **Roles:** admin, manager, user
    """
    device = await device_service.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return DeviceResponse.model_validate(device)


@router.get("/{device_id}/photos", response_model=List[str], dependencies=[Depends(require_permission(Permission.DEVICE_VIEW))])
async def get_device_photos(
    device_id: int,
    device_service: DeviceService = Depends(get_device_service)
):
    """
    Retrieve all photo URLs for a given device.
    
    **Permission Required:** DEVICE_VIEW
    **Roles:** admin, manager, user
    """
    return await device_service.get_device_photos(device_id)


# ============================================================================
# CREATE OPERATIONS - Admin only
# ============================================================================

@router.post("/", response_model=DeviceResponse, dependencies=[Depends(require_permission(Permission.DEVICE_CREATE))])
async def create_device(
    device_data: DeviceCreate,
    device_service: DeviceService = Depends(get_device_service)
):
    """
    Create a new device.
    
    **Permission Required:** DEVICE_CREATE
    **Roles:** admin only
    """
    return await device_service.create_device(device_data)


@router.post("/{device_id}/photos", response_model=DeviceResponse, dependencies=[Depends(require_permission(Permission.DEVICE_UPDATE))])
async def upload_device_photo(
    device_id: int,
    file: UploadFile = File(...),
    device_service: DeviceService = Depends(get_device_service)
):
    """
    Upload a photo for a device.
    Stores file in static/uploads/devices/ and updates device record.
    
    **Permission Required:** DEVICE_UPDATE
    **Roles:** admin only
    """
    return await device_service.upload_device_photo(device_id, file)


# ============================================================================
# UPDATE OPERATIONS - Admin only
# ============================================================================

@router.put("/{device_id}", response_model=DeviceResponse, dependencies=[Depends(require_permission(Permission.DEVICE_UPDATE))])
async def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    device_service: DeviceService = Depends(get_device_service)
):
    """
    Update device information.
    
    **Permission Required:** DEVICE_UPDATE
    **Roles:** admin only
    """
    return await device_service.update_device(device_id, device_data)


@router.put("/{device_id}/condition", response_model=DeviceResponse, dependencies=[Depends(require_permission(Permission.DEVICE_UPDATE))])
async def update_device_condition(
    device_id: int,
    condition_data: DeviceConditionUpdate,
    device_service: DeviceService = Depends(get_device_service)
):
    """
    Update device condition.
    
    **Permission Required:** DEVICE_UPDATE
    **Roles:** admin only
    """
    return await device_service.update_device_condition(device_id, condition_data)


@router.put("/{device_id}/status", response_model=DeviceResponse, dependencies=[Depends(require_permission(Permission.DEVICE_UPDATE))])
async def update_device_status(
    device_id: int,
    status_data: DeviceStatusUpdate,
    device_service: DeviceService = Depends(get_device_service)
):
    """
    Update device status.
    
    **Permission Required:** DEVICE_UPDATE
    **Roles:** admin only
    """
    return await device_service.update_device_status(device_id, status_data)


# ============================================================================
# DELETE OPERATIONS - Admin only
# ============================================================================

@router.delete("/{device_id}", dependencies=[Depends(require_permission(Permission.DEVICE_DELETE))])
async def delete_device(
    device_id: int,
    device_service: DeviceService = Depends(get_device_service)
):
    """
    Delete device (hard delete).
    
    **Permission Required:** DEVICE_DELETE
    **Roles:** admin only
    """
    success = await device_service.delete_device(device_id)
    return {"message": "Device deleted successfully"}


@router.delete("/{device_id}/photos/{filename}", response_model=DeviceResponse, dependencies=[Depends(require_permission(Permission.DEVICE_UPDATE))])
async def delete_device_photo(
    device_id: int,
    filename: str,
    device_service: DeviceService = Depends(get_device_service)
):
    """
    Delete a specific photo of a device by filename.
    Removes both database record and file from storage.
    
    **Permission Required:** DEVICE_UPDATE
    **Roles:** admin only
    """
    return await device_service.delete_device_photo(device_id, filename)


# ============================================================================
# DEVICE USAGE STATISTICS - Admin and Manager
# ============================================================================

@router.get("/usage/statistics", response_model=DeviceUsageListResponse, dependencies=[Depends(require_permission(Permission.DEVICE_USAGE_STATS))])
async def get_device_usage_statistics(
    device_name: Optional[str] = Query(None, description="Filter by device name"),
    nup_device: Optional[str] = Query(None, description="Filter by NUP device"),
    device_brand: Optional[str] = Query(None, description="Filter by device brand"),
    device_year: Optional[int] = Query(None, description="Filter by device year"),
    device_condition: Optional[str] = Query(None, description="Filter by device condition"),
    device_status: Optional[str] = Query(None, description="Filter by device status"),
    min_usage_days: Optional[int] = Query(None, ge=0, description="Minimum total usage days"),
    max_usage_days: Optional[int] = Query(None, ge=0, description="Maximum total usage days"),
    min_loans: Optional[int] = Query(None, ge=0, description="Minimum total loans"),
    last_used_from: Optional[str] = Query(None, description="Last used date from (YYYY-MM-DD)"),
    last_used_to: Optional[str] = Query(None, description="Last used date to (YYYY-MM-DD)"),
    sort_by: str = Query("total_usage_days", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    device_service: DeviceService = Depends(get_device_service)
):
    """
    Get comprehensive device usage statistics.
    
    **Permission Required:** DEVICE_USAGE_STATS
    **Roles:** admin, manager
    """
    from datetime import date as date_type
    
    last_used_from_date = None
    last_used_to_date = None
    
    if last_used_from:
        try:
            last_used_from_date = date_type.fromisoformat(last_used_from)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid last_used_from date format. Use YYYY-MM-DD"
            )
    
    if last_used_to:
        try:
            last_used_to_date = date_type.fromisoformat(last_used_to)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid last_used_to date format. Use YYYY-MM-DD"
            )
    
    usage_filter = DeviceUsageFilter(
        device_name=device_name,
        nup_device=nup_device,
        device_brand=device_brand,
        device_year=device_year,
        device_condition=device_condition,
        device_status=device_status,
        min_usage_days=min_usage_days,
        max_usage_days=max_usage_days,
        min_loans=min_loans,
        last_used_from=last_used_from_date,
        last_used_to=last_used_to_date,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size
    )
    
    return await device_service.get_device_usage_statistics(usage_filter)


@router.get("/usage/summary", response_model=DeviceUsageSummary, dependencies=[Depends(require_permission(Permission.DEVICE_USAGE_STATS))])
async def get_device_usage_summary(
    device_service: DeviceService = Depends(get_device_service)
):
    """
    Get device usage summary statistics.
    
    **Permission Required:** DEVICE_USAGE_STATS
    **Roles:** admin, manager
    """
    return await device_service.get_device_usage_summary()


@router.get("/usage/never-used", response_model=List[DeviceResponse], dependencies=[Depends(require_permission(Permission.DEVICE_USAGE_STATS))])
async def get_never_used_devices(
    device_service: DeviceService = Depends(get_device_service)
):
    """
    Get list of devices that have never been used in loans.
    
    **Permission Required:** DEVICE_USAGE_STATS
    **Roles:** admin, manager
    """
    return await device_service.get_never_used_devices()


@router.get("/usage/most-used", response_model=List[DeviceUsageStatistics], dependencies=[Depends(require_permission(Permission.DEVICE_USAGE_STATS))])
async def get_most_used_devices(
    limit: int = Query(10, ge=1, le=50, description="Number of devices to return"),
    device_service: DeviceService = Depends(get_device_service)
):
    """
    Get most used devices based on total usage days.
    
    **Permission Required:** DEVICE_USAGE_STATS
    **Roles:** admin, manager
    """
    return await device_service.get_most_used_devices(limit)


@router.get("/usage/{device_id}/history", response_model=Dict, dependencies=[Depends(require_permission(Permission.DEVICE_USAGE_STATS))])
async def get_device_usage_history(
    device_id: int,
    device_service: DeviceService = Depends(get_device_service)
):
    """
    Get detailed usage history for a specific device.
    
    **Permission Required:** DEVICE_USAGE_STATS
    **Roles:** admin, manager
    """
    device = await device_service.get_device(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    usage_filter = DeviceUsageFilter(page=1, page_size=1)
    usage_stats = await device_service.get_device_usage_statistics(usage_filter)
    
    device_stats = None
    for device_stat in usage_stats.devices:
        if device_stat.device_id == device_id:
            device_stats = device_stat
            break
    
    if not device_stats:
        device_stats = DeviceUsageStatistics(
            device_id=device.id,
            nup_device=device.nup_device,
            device_name=device.device_name,
            device_brand=device.bmn_brand or device.sample_brand,
            device_year=device.device_year,
            device_condition=device.device_condition,
            device_status=device.device_status,
            total_usage_days=0,
            total_loans=0,
            last_used_date=None,
            last_borrower=None,
            last_activity=None,
            average_usage_per_loan=0.0,
            usage_frequency_score=0.0
        )
    
    return {
        "device_info": device,
        "usage_statistics": device_stats,
        "message": "Device usage history retrieved successfully"
    }