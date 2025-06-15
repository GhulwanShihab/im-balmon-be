"""Comprehensive user management endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.user import UserRepository
from src.services.user import UserService
from src.schemas.user import (
    UserResponse, UserCreate, UserUpdate, UserListResponse, 
    UserSearchFilter, UserStatusUpdate, UserRoleUpdate, 
    UserWithRoles, RoleResponse, UserAccountStatus, UserStats
)
from src.auth.permissions import get_current_active_user, require_admin

router = APIRouter()

async def get_user_service(session: AsyncSession = Depends(get_db)) -> UserService:
    """Get user service dependency."""
    user_repo = UserRepository(session)
    return UserService(user_repo)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get current user information."""
    user = await user_service.get_user(current_user["id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/me/roles", response_model=UserWithRoles)
async def get_current_user_with_roles(
    current_user: dict = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get current user information with roles."""
    return await user_service.get_user_with_roles(current_user["id"])


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update current user information."""
    return await user_service.update_user(current_user["id"], user_data)


@router.get("/", response_model=UserListResponse, dependencies=[Depends(require_admin)])
async def get_users(
    email: Optional[str] = Query(None, description="Filter by email"),
    first_name: Optional[str] = Query(None, description="Filter by first name"),
    last_name: Optional[str] = Query(None, description="Filter by last name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_verified: Optional[bool] = Query(None, description="Filter by verified status"),
    mfa_enabled: Optional[bool] = Query(None, description="Filter by MFA status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    user_service: UserService = Depends(get_user_service)
):
    """Get all users with pagination and filtering (Admin only)."""
    filters = {}
    if email:
        filters["email"] = email
    if first_name:
        filters["first_name"] = first_name
    if last_name:
        filters["last_name"] = last_name
    if is_active is not None:
        filters["is_active"] = is_active
    if is_verified is not None:
        filters["is_verified"] = is_verified
    if mfa_enabled is not None:
        filters["mfa_enabled"] = mfa_enabled
    
    skip = (page - 1) * page_size
    return await user_service.get_all_users(skip, page_size, filters, sort_by, sort_order)


@router.post("/", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """Create a new user (Admin only)."""
    return await user_service.create_user(user_data)


@router.get("/stats", response_model=UserStats, dependencies=[Depends(require_admin)])
async def get_user_statistics(
    user_service: UserService = Depends(get_user_service)
):
    """Get user statistics (Admin only)."""
    stats = await user_service.get_user_stats()
    return UserStats(**stats)


@router.get("/roles", response_model=list[RoleResponse], dependencies=[Depends(require_admin)])
async def get_all_roles(
    user_service: UserService = Depends(get_user_service)
):
    """Get all available roles (Admin only)."""
    return await user_service.get_all_roles()


@router.get("/{user_id}", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def get_user_by_id(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """Get user by ID (Admin only)."""
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/{user_id}/roles", response_model=UserWithRoles, dependencies=[Depends(require_admin)])
async def get_user_with_roles(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """Get user with their roles (Admin only)."""
    return await user_service.get_user_with_roles(user_id)


@router.get("/{user_id}/status", response_model=UserAccountStatus, dependencies=[Depends(require_admin)])
async def get_user_account_status(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """Get detailed user account status (Admin only)."""
    return await user_service.get_user_account_status(user_id)


@router.put("/{user_id}", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    user_service: UserService = Depends(get_user_service)
):
    """Update user information (Admin only)."""
    return await user_service.update_user(user_id, user_data)


@router.put("/{user_id}/status", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def update_user_status(
    user_id: int,
    status_data: UserStatusUpdate,
    user_service: UserService = Depends(get_user_service)
):
    """Update user active status (Admin only)."""
    return await user_service.update_user_status(user_id, status_data.is_active)


@router.put("/{user_id}/roles", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def update_user_roles(
    user_id: int,
    role_data: UserRoleUpdate,
    user_service: UserService = Depends(get_user_service)
):
    """Update user roles (Admin only)."""
    return await user_service.update_user_roles(user_id, role_data.role_ids)


@router.post("/{user_id}/unlock", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def unlock_user_account(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """Unlock user account (Admin only)."""
    return await user_service.unlock_user_account(user_id)


@router.delete("/{user_id}", dependencies=[Depends(require_admin)])
async def delete_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """Delete user (soft delete, Admin only)."""
    success = await user_service.delete_user(user_id)
    return {"message": "User deleted successfully"}