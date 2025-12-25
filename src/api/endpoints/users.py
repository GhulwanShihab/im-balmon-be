"""Comprehensive user management endpoints with permission control."""

from typing import Optional
from datetime import datetime
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
from src.auth.permissions import (
    get_current_active_user, 
    require_permission,
    require_any_permission,
    require_roles
)
from src.auth.role_permissions import Permission

router = APIRouter()


async def get_user_service(session: AsyncSession = Depends(get_db)) -> UserService:
    """Dependency untuk mendapatkan service user."""
    user_repo = UserRepository(session)
    return UserService(user_repo)


# ============================================================================
# CURRENT USER ENDPOINTS - All authenticated users
# ============================================================================

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get current user information.
    
    **Permission Required:** USER_VIEW
    **Roles:** admin, manager, user
    """
    user = await user_service.get_user(current_user["id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/me/roles", response_model=UserWithRoles)
async def get_current_user_with_roles(
    current_user: dict = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get current user information with roles.
    
    **Permission Required:** USER_VIEW
    **Roles:** admin, manager, user
    """
    return await user_service.get_user_with_roles(current_user["id"])


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update current user information.
    
    **Permission Required:** USER_UPDATE (own profile)
    **Roles:** admin, manager, user
    """
    return await user_service.update_user(current_user["id"], user_data)


# ============================================================================
# VIEW ENDPOINTS - Admin and Manager
# ============================================================================

@router.get("/", response_model=UserListResponse, dependencies=[Depends(require_permission(Permission.USER_VIEW_ALL))])
async def get_users(
    email: Optional[str] = Query(None, description="Filter by email"),
    username: Optional[str] = Query(None, description="Filter by username"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_verified: Optional[bool] = Query(None, description="Filter by verified status"),
    mfa_enabled: Optional[bool] = Query(None, description="Filter by MFA status"),
    role_id: Optional[int] = Query(None, description="Filter by role ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get all users with pagination and filtering.
    
    **Permission Required:** USER_VIEW_ALL
    **Roles:** admin, manager
    """
    filters = {}
    if email:
        filters["email"] = email
    if username:
        filters["username"] = username
    if is_active is not None:
        filters["is_active"] = is_active
    if is_verified is not None:
        filters["is_verified"] = is_verified
    if mfa_enabled is not None:
        filters["mfa_enabled"] = mfa_enabled
    if role_id is not None:
        filters["role_id"] = role_id
    
    skip = (page - 1) * page_size
    return await user_service.get_all_users(skip, page_size, filters, sort_by, sort_order)


@router.get("/stats", response_model=UserStats, dependencies=[Depends(require_permission(Permission.USER_STATS))])
async def get_user_statistics(
    user_service: UserService = Depends(get_user_service)
):
    """
    Get user statistics.
    
    **Permission Required:** USER_STATS
    **Roles:** admin, manager
    """
    stats = await user_service.get_user_stats()
    return UserStats(**stats)


@router.get("/roles", response_model=list[RoleResponse], dependencies=[Depends(require_permission(Permission.USER_VIEW_ALL))])
async def get_all_roles(
    user_service: UserService = Depends(get_user_service)
):
    """
    Get all available roles.
    
    **Permission Required:** USER_VIEW_ALL
    **Roles:** admin, manager
    """
    return await user_service.get_all_roles()


@router.get("/pending", response_model=UserListResponse, dependencies=[Depends(require_permission(Permission.USER_VIEW_ALL))])
async def get_pending_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get all pending users waiting for approval.
    
    **Permission Required:** USER_VIEW_ALL
    **Roles:** admin, manager
    """
    filters = {"is_active": False, "is_verified": False}
    skip = (page - 1) * page_size
    return await user_service.get_all_users(skip, page_size, filters, "created_at", "asc")


@router.get("/{user_id}", response_model=UserResponse, dependencies=[Depends(require_permission(Permission.USER_VIEW_ALL))])
async def get_user_by_id(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """
    Get user by ID.
    
    **Permission Required:** USER_VIEW_ALL
    **Roles:** admin, manager
    """
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/{user_id}/roles", response_model=UserWithRoles, dependencies=[Depends(require_permission(Permission.USER_VIEW_ALL))])
async def get_user_with_roles(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """
    Get user with their roles.
    
    **Permission Required:** USER_VIEW_ALL
    **Roles:** admin, manager
    """
    return await user_service.get_user_with_roles(user_id)


@router.get("/{user_id}/status", response_model=UserAccountStatus, dependencies=[Depends(require_permission(Permission.USER_VIEW_ALL))])
async def get_user_account_status(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """
    Get detailed user account status.
    
    **Permission Required:** USER_VIEW_ALL
    **Roles:** admin, manager
    """
    return await user_service.get_user_account_status(user_id)


# ============================================================================
# CREATE/UPDATE/DELETE ENDPOINTS - Admin only
# ============================================================================

@router.post("/", response_model=UserResponse, dependencies=[Depends(require_permission(Permission.USER_CREATE))])
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """
    Create a new user.
    
    **Permission Required:** USER_CREATE
    **Roles:** admin only
    """
    return await user_service.create_user(user_data)


@router.put("/{user_id}", response_model=UserResponse, dependencies=[Depends(require_permission(Permission.USER_UPDATE))])
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    user_service: UserService = Depends(get_user_service)
):
    """
    Update user information.
    
    **Permission Required:** USER_UPDATE
    **Roles:** admin only
    """
    return await user_service.update_user(user_id, user_data)


@router.put("/{user_id}/status", response_model=UserResponse, dependencies=[Depends(require_permission(Permission.USER_UPDATE))])
async def update_user_status(
    user_id: int,
    status_data: UserStatusUpdate,
    user_service: UserService = Depends(get_user_service)
):
    """
    Update user active status.
    
    **Permission Required:** USER_UPDATE
    **Roles:** admin only
    """
    return await user_service.update_user_status(user_id, status_data.is_active)


@router.put("/{user_id}/roles", response_model=UserResponse, dependencies=[Depends(require_permission(Permission.USER_UPDATE))])
async def update_user_roles(
    user_id: int,
    role_data: UserRoleUpdate,
    user_service: UserService = Depends(get_user_service)
):
    """
    Update user roles.
    
    **Permission Required:** USER_UPDATE
    **Roles:** admin only
    """
    user = await user_service.update_user_roles(user_id, role_data.role_ids)

    # Pastikan user aktif dan diverifikasi
    if not user.is_verified or not user.is_active:
        update_data = UserUpdate(
            is_active=True,
            is_verified=True,
            updated_at=datetime.utcnow()
        )
        user = await user_service.update_user(user_id, update_data)

    return user


@router.post("/{user_id}/unlock", response_model=UserResponse, dependencies=[Depends(require_permission(Permission.USER_UPDATE))])
async def unlock_user_account(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """
    Unlock user account.
    
    **Permission Required:** USER_UPDATE
    **Roles:** admin only
    """
    return await user_service.unlock_user_account(user_id)


@router.delete("/{user_id}", dependencies=[Depends(require_permission(Permission.USER_DELETE))])
async def delete_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """
    Delete user (soft delete).
    
    **Permission Required:** USER_DELETE
    **Roles:** admin only
    """
    success = await user_service.delete_user(user_id)
    return {"message": "User deleted successfully"}


# ============================================================================
# APPROVAL & REJECTION ENDPOINTS - Admin and Manager
# ============================================================================

@router.patch("/{user_id}/approve", response_model=UserResponse, dependencies=[Depends(require_permission(Permission.USER_APPROVE))])
async def approve_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """
    Approve user registration.
    
    **Permission Required:** USER_APPROVE
    **Roles:** admin, manager
    """
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_active and user.is_verified:
        raise HTTPException(status_code=400, detail="User already approved")

    # ✅ STEP 1: Update status user
    update_data = UserUpdate(
        is_active=True,
        is_verified=True,
        updated_at=datetime.utcnow()
    )
    updated_user = await user_service.update_user(user_id, update_data)
    
    # ✅ STEP 2: Assign default role "user" jika belum punya role
    user_with_roles = await user_service.get_user_with_roles(user_id)
    if not user_with_roles.roles or len(user_with_roles.roles) == 0:
        # Dapatkan role_id untuk "user"
        default_role = await user_service.get_role_by_name("user")
        if default_role:
            await user_service.update_user_roles(user_id, [default_role.id])
        else:
            # Jika role "user" tidak ada, buat error
            raise HTTPException(
                status_code=500, 
                detail="Default role 'user' not found. Please contact administrator."
            )
    
    return await user_service.get_user(user_id)


@router.patch("/{user_id}/reject", dependencies=[Depends(require_permission(Permission.USER_DELETE))])
async def reject_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """
    Reject user registration.
    Deletes the user permanently if still pending.
    
    **Permission Required:** USER_DELETE
    **Roles:** admin only
    """
    try:
        user = await user_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.is_active or user.is_verified:
            raise HTTPException(status_code=400, detail="User already approved")

        # Hapus user secara permanen (bukan soft delete)
        await user_service.hard_delete_user(user_id)

        return {"message": f"User {user.email} rejected and permanently deleted"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error rejecting user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to reject user")