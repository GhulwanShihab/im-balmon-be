"""Endpoints for managing child devices (enhanced)."""

from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.device import DeviceRepository
from src.repositories.device_child import DeviceChildRepository
from src.services.device_child import DeviceChildService
from src.schemas.device_child import (
    DeviceChildResponse, DeviceChildCreate, DeviceChildUpdate, DeviceChildListResponse
)
from src.auth.permissions import get_current_active_user, require_admin

router = APIRouter()

# Dependency
async def get_device_child_service(session: AsyncSession = Depends(get_db)) -> DeviceChildService:
    device_child_repo = DeviceChildRepository(session)
    device_repo = DeviceRepository(session)
    return DeviceChildService(device_child_repo, device_repo)

# -------------------------
# List / Pagination / Filter
# -------------------------
@router.get("/", response_model=DeviceChildListResponse)
async def get_all_children(
    parent_id: Optional[int] = Query(None, description="Filter by parent device ID"),
    device_name: Optional[str] = Query(None, description="Filter by device name"),
    device_code: Optional[str] = Query(None, description="Filter by device code"),
    nup_device: Optional[str] = Query(None, description="Filter by NUP device"),
    device_status: Optional[str] = Query(None, description="Filter by device status"),
    device_condition: Optional[str] = Query(None, description="Filter by device condition"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_active_user),
    service: DeviceChildService = Depends(get_device_child_service)
):
    """Get all child devices with optional filters."""
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

# -------------------------
# Get by ID
# -------------------------
@router.get("/{child_id}", response_model=DeviceChildResponse)
async def get_child_by_id(
    child_id: int,
    current_user: dict = Depends(get_current_active_user),
    service: DeviceChildService = Depends(get_device_child_service)
):
    child = await service.get_child(child_id)
    if not child:
        raise HTTPException(status_code=404, detail="Child device not found")
    return child

# -------------------------
# Create / Update / Delete
# -------------------------
@router.post("/", response_model=DeviceChildResponse, dependencies=[Depends(require_admin)])
async def create_child(
    child_data: DeviceChildCreate,
    service: DeviceChildService = Depends(get_device_child_service)
):
    return await service.create_child(child_data)

@router.put("/{child_id}", response_model=DeviceChildResponse, dependencies=[Depends(require_admin)])
async def update_child(
    child_id: int,
    update_data: DeviceChildUpdate,
    service: DeviceChildService = Depends(get_device_child_service)
):
    child = await service.update_child(child_id, update_data)
    if not child:
        raise HTTPException(status_code=404, detail="Child device not found")
    return child

@router.delete("/{child_id}", dependencies=[Depends(require_admin)])
async def delete_child(
    child_id: int,
    service: DeviceChildService = Depends(get_device_child_service)
):
    success = await service.delete_child(child_id)
    if not success:
        raise HTTPException(status_code=404, detail="Child device not found")
    return {"message": "Child device deleted successfully"}

# -------------------------
# Search
# -------------------------
@router.get("/search", response_model=DeviceChildListResponse)
async def search_children(
    q: str = Query(..., description="Search term (name, code, NUP)"),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_active_user),
    service: DeviceChildService = Depends(get_device_child_service)
):
    return await service.search_children(q, limit)

# -------------------------
# Photo management
# -------------------------
@router.post("/{child_id}/photos", response_model=DeviceChildResponse, dependencies=[Depends(require_admin)])
async def upload_child_photo(
    child_id: int,
    file: UploadFile = File(...),
    service: DeviceChildService = Depends(get_device_child_service)
):
    return await service.upload_child_photo(child_id, file)

@router.delete("/{child_id}/photos/{filename}", response_model=DeviceChildResponse, dependencies=[Depends(require_admin)])
async def delete_child_photo(
    child_id: int,
    filename: str,
    service: DeviceChildService = Depends(get_device_child_service)
):
    return await service.delete_child_photo(child_id, filename)

@router.get("/{child_id}/photos", response_model=List[str])
async def get_child_photos(
    child_id: int,
    current_user: dict = Depends(get_current_active_user),
    service: DeviceChildService = Depends(get_device_child_service)
):
    return await service.get_child_photos(child_id)
