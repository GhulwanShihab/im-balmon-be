"""Device Group API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.device_group import DeviceGroupRepository
from src.repositories.loan import LoanRepository
from src.repositories.device import DeviceRepository
from src.services.device_group import DeviceGroupService
from src.schemas.device_group import (
    DeviceGroupCreate, DeviceGroupUpdate, DeviceGroupResponse,
    DeviceGroupDetailResponse, DeviceGroupListResponse,
    DeviceGroupAddDevices, DeviceGroupRemoveDevices,
    DeviceGroupBorrowRequest, DeviceGroupBorrowResponse
)
from src.auth.permissions import get_current_active_user

router = APIRouter()


async def get_device_group_service(session: AsyncSession = Depends(get_db)) -> DeviceGroupService:
    """Get device group service dependency."""
    device_group_repo = DeviceGroupRepository(session)
    loan_repo = LoanRepository(session)
    device_repo = DeviceRepository(session)
    return DeviceGroupService(device_group_repo, loan_repo, device_repo)


# ============================================================================
# CRUD Operations
# ============================================================================

@router.post("/", response_model=DeviceGroupDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_device_group(
    group_data: DeviceGroupCreate,
    current_user: dict = Depends(get_current_active_user),
    service: DeviceGroupService = Depends(get_device_group_service)
):
    """
    Create a new device group.
    
    - **name**: Group name (required)
    - **description**: Group description (optional)
    - **device_ids**: List of parent device IDs to add (optional)
    - **child_device_ids**: List of child device IDs to add (optional)
    """
    return await service.create_group(group_data, current_user["id"])


@router.get("/", response_model=DeviceGroupListResponse)
async def get_user_device_groups(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    name: Optional[str] = Query(None, description="Filter by group name"),
    current_user: dict = Depends(get_current_active_user),
    service: DeviceGroupService = Depends(get_device_group_service)
):
    """
    Get all device groups for the current user with pagination.
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **name**: Filter by group name (optional)
    """
    return await service.get_user_groups(
        current_user["id"], 
        page, 
        page_size, 
        name
    )


@router.get("/{group_id}", response_model=DeviceGroupDetailResponse)
async def get_device_group(
    group_id: int,
    current_user: dict = Depends(get_current_active_user),
    service: DeviceGroupService = Depends(get_device_group_service)
):
    """
    Get detailed information about a device group.
    
    Includes:
    - Group information
    - All devices in the group
    - Availability status of each device
    - Overall availability status
    """
    return await service.get_group(group_id, current_user["id"])


@router.put("/{group_id}", response_model=DeviceGroupResponse)
async def update_device_group(
    group_id: int,
    update_data: DeviceGroupUpdate,
    current_user: dict = Depends(get_current_active_user),
    service: DeviceGroupService = Depends(get_device_group_service)
):
    """
    Update device group information.
    
    - **name**: New group name (optional)
    - **description**: New group description (optional)
    """
    return await service.update_group(group_id, update_data, current_user["id"])


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device_group(
    group_id: int,
    current_user: dict = Depends(get_current_active_user),
    service: DeviceGroupService = Depends(get_device_group_service)
):
    """
    Delete a device group (hard delete).
    
    This will remove the group and all device associations.
    The devices themselves will not be deleted.
    """
    success = await service.delete_group(group_id, current_user["id"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device group not found"
        )
    return None


# ============================================================================
# Device Management in Group
# ============================================================================

@router.post("/{group_id}/devices", response_model=DeviceGroupDetailResponse)
async def add_devices_to_group(
    group_id: int,
    devices_data: DeviceGroupAddDevices,
    current_user: dict = Depends(get_current_active_user),
    service: DeviceGroupService = Depends(get_device_group_service)
):
    """
    Add devices to a group.
    
    - **device_ids**: List of parent device IDs to add
    - **child_device_ids**: List of child device IDs to add
    
    Devices that are already in the group will be skipped.
    """
    return await service.add_devices_to_group(group_id, devices_data, current_user["id"])


@router.delete("/{group_id}/devices", response_model=DeviceGroupDetailResponse)
async def remove_devices_from_group(
    group_id: int,
    devices_data: DeviceGroupRemoveDevices,
    current_user: dict = Depends(get_current_active_user),
    service: DeviceGroupService = Depends(get_device_group_service)
):
    """
    Remove devices from a group.
    
    - **device_ids**: List of parent device IDs to remove
    - **child_device_ids**: List of child device IDs to remove
    """
    return await service.remove_devices_from_group(group_id, devices_data, current_user["id"])


# ============================================================================
# Batch Borrow Operation
# ============================================================================

@router.post("/{group_id}/borrow", response_model=DeviceGroupBorrowResponse)
async def borrow_group_devices(
    group_id: int,
    borrow_data: DeviceGroupBorrowRequest,
    current_user: dict = Depends(get_current_active_user),
    service: DeviceGroupService = Depends(get_device_group_service)
):
    """
    Borrow all devices in a group (batch operation).
    
    **Requirements:**
    - All devices in the group must have status "TERSEDIA"
    - If any device is not available (DIPINJAM, MAINTENANCE, NONAKTIF), 
      the operation will fail and return the list of unavailable devices
    
    **Success Response:**
    - Creates a single loan with all devices from the group
    - Returns loan_id and list of borrowed device names
    
    **Failure Response:**
    - Returns list of unavailable devices with their current status
    - No loan is created
    
    **Request Body:**
    - **borrower_name**: Name of the borrower
    - **activity_name**: Activity name (as per assignment letter)
    - **assignment_letter_number**: Assignment letter number
    - **assignment_letter_date**: Assignment letter date (YYYY-MM-DD)
    - **loan_start_date**: Loan start date (YYYY-MM-DD)
    - **usage_duration_days**: Duration in days
    - **purpose**: Purpose of borrowing (optional)
    - **monitoring_devices**: Monitoring devices (optional)
    - **pihak_1_id**: Responsible party ID (optional)
    - **pihak_2_id**: Acknowledging party ID (optional)
    """
    return await service.borrow_group_devices(group_id, borrow_data, current_user["id"])


# ============================================================================
# Helper Endpoints
# ============================================================================

@router.get("/{group_id}/check-availability")
async def check_group_availability(
    group_id: int,
    current_user: dict = Depends(get_current_active_user),
    service: DeviceGroupService = Depends(get_device_group_service)
):
    """
    Check availability of all devices in a group without borrowing.
    
    Returns:
    - **all_available**: Boolean indicating if all devices are available
    - **unavailable_devices**: List of device names that are not available
    - **total_devices**: Total number of devices in the group
    - **available_count**: Number of available devices
    """
    group = await service.get_group(group_id, current_user["id"])
    
    return {
        "group_id": group_id,
        "group_name": group.name,
        "all_available": group.all_available,
        "unavailable_devices": group.unavailable_devices,
        "total_devices": group.device_count,
        "available_count": group.device_count - len(group.unavailable_devices)
    }