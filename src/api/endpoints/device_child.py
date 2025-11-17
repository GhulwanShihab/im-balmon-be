"""Endpoints for managing child devices with permission-based authorization."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.device import DeviceRepository
from src.repositories.device_child import DeviceChildRepository
from src.services.device_child import DeviceChildService
from src.schemas.device_child import (
    DeviceChildResponse, DeviceChildCreate, DeviceChildUpdate, DeviceChildListResponse
)

from src.auth.permissions import (
    get_current_active_user, 
    require_permission,
    require_any_permission,
    require_roles
)
from src.auth.role_permissions import Permission

router = APIRouter()


async def get_device_child_service(session: AsyncSession = Depends(get_db)) -> DeviceChildService:
    """Get device child service dependency."""
    device_child_repo = DeviceChildRepository(session)
    device_repo = DeviceRepository(session)
    return DeviceChildService(device_child_repo, device_repo)


# ============================================================================
# READ OPERATIONS - All authenticated users
# ============================================================================

@router.get("/", response_model=DeviceChildListResponse, dependencies=[Depends(require_permission(Permission.DEVICE_CHILD_VIEW))])
async def get_all_children(
    parent_id: Optional[int] = Query(None, description="Filter by parent device ID"),
    device_name: Optional[str] = Query(None, description="Filter by device name"),
    device_code: Optional[str] = Query(None, description="Filter by device code"),
    nup_device: Optional[str] = Query(None, description="Filter by NUP device"),
    device_status: Optional[str] = Query(None, description="Filter by device status"),
    device_condition: Optional[str] = Query(None, description="Filter by device condition"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    service: DeviceChildService = Depends(get_device_child_service)
):
    """
    Get all child devices with optional filters.
    
    **Permission Required:** DEVICE_CHILD_VIEW
    **Roles:** admin, manager, user
    """
    filters = {}
    if parent_id is not None:
        filters["parent_id"] = parent_id
    if device_name:
        filters["device_name"] = device_name
    if device_code:
        filters["device_code"] = device_code
    if nup_device:
        filters["nup_device"] = nup_device
    if device_status:
        filters["device_status"] = device_status
    if device_condition:
        filters["device_condition"] = device_condition

    skip = (page - 1) * page_size
    return await service.get_all_children(skip, page_size, filters)


@router.get("/search", response_model=DeviceChildListResponse, dependencies=[Depends(require_permission(Permission.DEVICE_CHILD_VIEW))])
async def search_children(
    q: str = Query(..., description="Search term (name, code, NUP)"),
    limit: int = Query(10, ge=1, le=50),
    service: DeviceChildService = Depends(get_device_child_service)
):
    """
    Search child devices by name, code, or NUP.
    
    **Permission Required:** DEVICE_CHILD_VIEW
    **Roles:** admin, manager, user
    """
    return await service.search_children(q, limit)


@router.get("/{child_id}", response_model=DeviceChildResponse, dependencies=[Depends(require_permission(Permission.DEVICE_CHILD_VIEW))])
async def get_child_by_id(
    child_id: int,
    service: DeviceChildService = Depends(get_device_child_service)
):
    """
    Get child device by ID.
    
    **Permission Required:** DEVICE_CHILD_VIEW
    **Roles:** admin, manager, user
    """
    child = await service.get_child(child_id)
    if not child:
        raise HTTPException(status_code=404, detail="Child device not found")
    return child


@router.get("/{child_id}/photos", response_model=List[str], dependencies=[Depends(require_permission(Permission.DEVICE_CHILD_VIEW))])
async def get_child_photos(
    child_id: int,
    service: DeviceChildService = Depends(get_device_child_service)
):
    """
    Retrieve all photo URLs for a child device.
    
    **Permission Required:** DEVICE_CHILD_VIEW
    **Roles:** admin, manager, user
    """
    return await service.get_child_photos(child_id)


# ============================================================================
# CREATE OPERATIONS - Admin only
# ============================================================================

@router.post("/", response_model=DeviceChildResponse, dependencies=[Depends(require_permission(Permission.DEVICE_CHILD_CREATE))])
async def create_child(
    child_data: DeviceChildCreate,
    service: DeviceChildService = Depends(get_device_child_service)
):
    """
    Create a new child device.
    
    **Permission Required:** DEVICE_CHILD_CREATE
    **Roles:** admin only
    """
    return await service.create_child(child_data)


@router.post("/{child_id}/photos", response_model=DeviceChildResponse, dependencies=[Depends(require_permission(Permission.DEVICE_CHILD_UPDATE))])
async def upload_child_photo(
    child_id: int,
    file: UploadFile = File(...),
    service: DeviceChildService = Depends(get_device_child_service)
):
    """
    Upload a photo for a child device.
    
    **Permission Required:** DEVICE_CHILD_UPDATE
    **Roles:** admin only
    """
    return await service.upload_child_photo(child_id, file)


# ============================================================================
# UPDATE OPERATIONS - Admin only
# ============================================================================

@router.put("/{child_id}", response_model=DeviceChildResponse, dependencies=[Depends(require_permission(Permission.DEVICE_CHILD_UPDATE))])
async def update_child(
    child_id: int,
    update_data: DeviceChildUpdate,
    service: DeviceChildService = Depends(get_device_child_service)
):
    """
    Update child device information.
    
    **Permission Required:** DEVICE_CHILD_UPDATE
    **Roles:** admin only
    """
    child = await service.update_child(child_id, update_data)
    if not child:
        raise HTTPException(status_code=404, detail="Child device not found")
    return child


# ============================================================================
# DELETE OPERATIONS - Admin only
# ============================================================================

@router.delete("/{child_id}", dependencies=[Depends(require_permission(Permission.DEVICE_CHILD_DELETE))])
async def delete_child(
    child_id: int,
    service: DeviceChildService = Depends(get_device_child_service)
):
    """
    Delete a child device.
    
    **Permission Required:** DEVICE_CHILD_DELETE
    **Roles:** admin only
    """
    success = await service.delete_child(child_id)
    if not success:
        raise HTTPException(status_code=404, detail="Child device not found")
    return {"message": "Child device deleted successfully"}


@router.delete("/{child_id}/photos/{filename}", response_model=DeviceChildResponse, dependencies=[Depends(require_permission(Permission.DEVICE_CHILD_UPDATE))])
async def delete_child_photo(
    child_id: int,
    filename: str,
    service: DeviceChildService = Depends(get_device_child_service)
):
    """
    Delete a specific photo of a child device by filename.
    
    **Permission Required:** DEVICE_CHILD_UPDATE
    **Roles:** admin only
    """
    return await service.delete_child_photo(child_id, filename)