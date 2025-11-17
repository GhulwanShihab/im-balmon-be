"""Enhanced authorization and permission checking with JWT Bearer."""

from typing import List, Dict, Union
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.jwt import verify_token, is_user_blacklisted
from src.core.database import get_db
from src.repositories.user import UserRepository
from src.auth.role_permissions import Permission, has_permission, get_user_permissions


class JWTBearer(HTTPBearer):
    """Custom JWT Bearer authentication handler."""
    
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearer, self
        ).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme.",
                )
            return credentials.credentials
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization code.",
            )


jwt_bearer = JWTBearer()


async def get_current_user(
    token: str = Depends(jwt_bearer), 
    session: AsyncSession = Depends(get_db)
) -> Dict:
    """
    Get the current authenticated user from the token.
    
    Returns user dict with: id, email, username, roles, is_active, permissions
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Verify JWT token
        payload = await verify_token(token)
        
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception

        # Check if user is blacklisted (logout all devices)
        if await is_user_blacklisted(int(user_id)):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has been terminated. Please login again."
            )

        # Get user from database
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(int(user_id))

        if not user:
            raise credentials_exception

        # Get user roles
        user_roles = await user_repo.get_user_roles(user.id)
        roles = [role.name for role in user_roles]

        # Get user permissions based on roles
        permissions = get_user_permissions(roles)

        user_data = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "roles": roles,
            "permissions": [perm.value for perm in permissions],  # List of permission strings
            "is_active": user.is_active,
        }

        return user_data

    except JWTError:
        raise credentials_exception
    except ValueError:
        raise credentials_exception


async def get_current_active_user(
    current_user: Dict = Depends(get_current_user),
) -> Dict:
    """Check if the current user is active."""
    if not current_user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Inactive user"
        )
    return current_user


# ============================================================================
# ROLE-BASED AUTHORIZATION
# ============================================================================

def require_roles(required_roles: List[str]):
    """
    Dependency to require specific roles.
    
    Usage:
        @router.get("/", dependencies=[Depends(require_roles(["admin", "manager"]))])
    
    Args:
        required_roles: List of role names that are allowed
    """
    async def _check_roles(
        current_user: Dict = Depends(get_current_active_user),
    ) -> Dict:
        user_roles = current_user.get("roles", [])
        
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {', '.join(required_roles)}",
            )
        
        return current_user
    
    return _check_roles


# Common role dependencies (legacy compatibility)
admin_required = require_roles(["admin"])
user_required = require_roles(["user", "admin"])


async def require_admin(
    current_user: Dict = Depends(get_current_active_user),
) -> Dict:
    """
    Require admin role (legacy compatibility).
    
    Usage:
        @router.post("/", dependencies=[Depends(require_admin)])
    """
    user_roles = current_user.get("roles", [])
    
    if "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    
    return current_user


# ============================================================================
# PERMISSION-BASED AUTHORIZATION (NEW)
# ============================================================================

def require_permission(required_permission: Permission):
    """
    Dependency to require specific permission.
    
    Usage:
        @router.post("/", dependencies=[Depends(require_permission(Permission.DEVICE_CREATE))])
    
    Args:
        required_permission: Required permission to check
    """
    async def permission_checker(
        current_user: Dict = Depends(get_current_active_user)
    ) -> Dict:
        user_roles = current_user.get("roles", [])
        
        if not has_permission(user_roles, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {required_permission.value} required"
            )
        
        return current_user
    
    return permission_checker


def require_any_permission(*permissions: Permission):
    """
    Dependency to require ANY of the specified permissions.
    
    Usage:
        @router.get("/", dependencies=[Depends(require_any_permission(
            Permission.DEVICE_VIEW, 
            Permission.LOAN_VIEW
        ))])
    
    Args:
        *permissions: Variable number of permissions, user needs at least one
    """
    async def permission_checker(
        current_user: Dict = Depends(get_current_active_user)
    ) -> Dict:
        user_roles = current_user.get("roles", [])
        
        for perm in permissions:
            if has_permission(user_roles, perm):
                return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: One of {[p.value for p in permissions]} required"
        )
    
    return permission_checker


def require_all_permissions(*permissions: Permission):
    """
    Dependency to require ALL of the specified permissions.
    
    Usage:
        @router.post("/", dependencies=[Depends(require_all_permissions(
            Permission.DEVICE_CREATE, 
            Permission.LOAN_CREATE
        ))])
    
    Args:
        *permissions: Variable number of permissions, user needs all of them
    """
    async def permission_checker(
        current_user: Dict = Depends(get_current_active_user)
    ) -> Dict:
        user_roles = current_user.get("roles", [])
        
        for perm in permissions:
            if not has_permission(user_roles, perm):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {perm.value} required"
                )
        
        return current_user
    
    return permission_checker


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def check_user_permission(current_user: Dict, permission: Permission) -> bool:
    """
    Check if user has specific permission (without raising exception).
    
    Useful for conditional logic in endpoint handlers.
    
    Args:
        current_user: User dict from get_current_active_user
        permission: Permission to check
    
    Returns:
        True if user has permission, False otherwise
    """
    user_roles = current_user.get("roles", [])
    return has_permission(user_roles, permission)


def get_user_permission_list(current_user: Dict) -> List[str]:
    """
    Get list of all permissions user has.
    
    Args:
        current_user: User dict from get_current_active_user
    
    Returns:
        List of permission strings
    """
    return current_user.get("permissions", [])