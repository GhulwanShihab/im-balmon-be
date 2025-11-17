"""Role-based permissions configuration."""

from enum import Enum
from typing import Set, Dict

class Permission(str, Enum):
    """Permission types for the application."""
    
    # ========================================================================
    # USER PERMISSIONS
    # ========================================================================
    USER_VIEW = "user:view"
    USER_VIEW_ALL = "user:view_all"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_APPROVE = "user:approve"
    USER_STATS = "user:stats"
    
    # ========================================================================
    # DEVICE PERMISSIONS
    # ========================================================================
    DEVICE_VIEW = "device:view"
    DEVICE_CREATE = "device:create"
    DEVICE_UPDATE = "device:update"
    DEVICE_DELETE = "device:delete"
    DEVICE_STATS = "device:stats"
    DEVICE_USAGE_STATS = "device:usage_stats"
    
    # ========================================================================
    # DEVICE CHILD PERMISSIONS
    # ========================================================================
    DEVICE_CHILD_VIEW = "device_child:view"
    DEVICE_CHILD_CREATE = "device_child:create"
    DEVICE_CHILD_UPDATE = "device_child:update"
    DEVICE_CHILD_DELETE = "device_child:delete"
    
    # ========================================================================
    # DEVICE GROUP PERMISSIONS
    # ========================================================================
    DEVICE_GROUP_VIEW = "device_group:view"
    DEVICE_GROUP_CREATE = "device_group:create"
    DEVICE_GROUP_UPDATE = "device_group:update"
    DEVICE_GROUP_DELETE = "device_group:delete"
    DEVICE_GROUP_BORROW = "device_group:borrow"
    
    # ========================================================================
    # LOAN PERMISSIONS
    # ========================================================================
    LOAN_VIEW = "loan:view"  # View own loans
    LOAN_VIEW_ALL = "loan:view_all"  # View all loans
    LOAN_CREATE = "loan:create"
    LOAN_UPDATE = "loan:update"
    LOAN_DELETE = "loan:delete"
    LOAN_RETURN = "loan:return"
    LOAN_CANCEL = "loan:cancel"
    LOAN_APPROVE = "loan:approve"
    LOAN_STATS = "loan:stats"
    LOAN_CONDITION_APPROVE = "loan:condition_approve"
    
    # ========================================================================
    # EMPLOYEE PERMISSIONS
    # ========================================================================
    EMPLOYEE_VIEW = "employee:view"
    EMPLOYEE_CREATE = "employee:create"
    EMPLOYEE_UPDATE = "employee:update"
    EMPLOYEE_DELETE = "employee:delete"
    
    # ========================================================================
    # EXPORT PERMISSIONS
    # ========================================================================
    EXPORT_PDF = "export:pdf"
    EXPORT_EXCEL = "export:excel"
    EXPORT_DEVICE_USAGE = "export:device_usage"
    EXPORT_LOAN_REPORT = "export:loan_report"
    
    # ========================================================================
    # MFA PERMISSIONS
    # ========================================================================
    MFA_MANAGE = "mfa:manage"  # Manage own MFA
    MFA_ADMIN = "mfa:admin"  # Admin MFA operations


# ============================================================================
# ROLE PERMISSIONS MAPPING
# ============================================================================

ROLE_PERMISSIONS: Dict[str, Set[Permission]] = {
    # ========================================================================
    # ADMIN - Full access to everything
    # ========================================================================
    "admin": {
        # Users
        Permission.USER_VIEW,
        Permission.USER_VIEW_ALL,
        Permission.USER_CREATE,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.USER_APPROVE,
        Permission.USER_STATS,
        
        # Devices
        Permission.DEVICE_VIEW,
        Permission.DEVICE_CREATE,
        Permission.DEVICE_UPDATE,
        Permission.DEVICE_DELETE,
        Permission.DEVICE_STATS,
        Permission.DEVICE_USAGE_STATS,
        
        # Device Children
        Permission.DEVICE_CHILD_VIEW,
        Permission.DEVICE_CHILD_CREATE,
        Permission.DEVICE_CHILD_UPDATE,
        Permission.DEVICE_CHILD_DELETE,
        
        # Device Groups
        Permission.DEVICE_GROUP_VIEW,
        Permission.DEVICE_GROUP_CREATE,
        Permission.DEVICE_GROUP_UPDATE,
        Permission.DEVICE_GROUP_DELETE,
        Permission.DEVICE_GROUP_BORROW,
        
        # Loans
        Permission.LOAN_VIEW,
        Permission.LOAN_VIEW_ALL,
        Permission.LOAN_CREATE,
        Permission.LOAN_UPDATE,
        Permission.LOAN_DELETE,
        Permission.LOAN_RETURN,
        Permission.LOAN_CANCEL,
        Permission.LOAN_APPROVE,
        Permission.LOAN_STATS,
        Permission.LOAN_CONDITION_APPROVE,
        
        # Employees
        Permission.EMPLOYEE_VIEW,
        Permission.EMPLOYEE_CREATE,
        Permission.EMPLOYEE_UPDATE,
        Permission.EMPLOYEE_DELETE,
        
        # Export
        Permission.EXPORT_PDF,
        Permission.EXPORT_EXCEL,
        Permission.EXPORT_DEVICE_USAGE,
        Permission.EXPORT_LOAN_REPORT,
        
        # MFA
        Permission.MFA_MANAGE,
        Permission.MFA_ADMIN,
    },
    
    # ========================================================================
    # MANAGER - Read access + limited actions (NO create/update/delete)
    # ========================================================================
    "manager": {
        # Users - View only + approve
        Permission.USER_VIEW,
        Permission.USER_VIEW_ALL,
        Permission.USER_APPROVE,  # Can approve pending users
        Permission.USER_STATS,
        
        # Devices - View only + stats
        Permission.DEVICE_VIEW,
        Permission.DEVICE_STATS,
        Permission.DEVICE_USAGE_STATS,
        
        # Device Children - View only
        Permission.DEVICE_CHILD_VIEW,
        
        # Device Groups - View only
        Permission.DEVICE_GROUP_VIEW,
        
        # Loans - View all + approve/cancel (but NO create/update/delete)
        Permission.LOAN_VIEW,
        Permission.LOAN_VIEW_ALL,
        Permission.LOAN_APPROVE,  # Can approve loan requests
        Permission.LOAN_CANCEL,   # Can cancel active loans
        Permission.LOAN_STATS,
        Permission.LOAN_CONDITION_APPROVE,  # Can approve condition changes
        
        # Employees - View only
        Permission.EMPLOYEE_VIEW,
        
        # Export - Can export reports
        Permission.EXPORT_PDF,
        Permission.EXPORT_EXCEL,
        Permission.EXPORT_DEVICE_USAGE,
        Permission.EXPORT_LOAN_REPORT,
        
        # MFA - Can manage own MFA
        Permission.MFA_MANAGE,
    },
    
    # ========================================================================
    # USER - Limited access (own data + basic operations)
    # ========================================================================
    "user": {
        # Users - Can only view and update self
        Permission.USER_VIEW,  # View own profile
        
        # Devices - View only
        Permission.DEVICE_VIEW,
        
        # Device Children - View only
        Permission.DEVICE_CHILD_VIEW,
        
        # Device Groups - Full access to own groups
        Permission.DEVICE_GROUP_VIEW,
        Permission.DEVICE_GROUP_CREATE,
        Permission.DEVICE_GROUP_UPDATE,
        Permission.DEVICE_GROUP_DELETE,
        Permission.DEVICE_GROUP_BORROW,
        
        # Loans - Can create and view own loans
        Permission.LOAN_VIEW,  # View own loans only
        Permission.LOAN_CREATE,
        Permission.LOAN_UPDATE,  # Update own loans only
        Permission.LOAN_RETURN,  # Return own loans
        
        # Employees - View only
        Permission.EMPLOYEE_VIEW,
        
        # Export - Can export own data
        Permission.EXPORT_PDF,  # Export own loan documents
        
        # MFA - Can manage own MFA
        Permission.MFA_MANAGE,
    }
}


# ============================================================================
# PERMISSION CHECKING FUNCTIONS
# ============================================================================

def has_permission(user_roles: list[str], required_permission: Permission) -> bool:
    """
    Check if user has required permission based on their roles.
    
    Args:
        user_roles: List of role names (e.g., ["admin", "manager"])
        required_permission: Required permission to check
    
    Returns:
        True if user has permission, False otherwise
    
    Example:
        >>> has_permission(["manager"], Permission.DEVICE_VIEW)
        True
        >>> has_permission(["manager"], Permission.DEVICE_CREATE)
        False
    """
    for role in user_roles:
        role_perms = ROLE_PERMISSIONS.get(role, set())
        if required_permission in role_perms:
            return True
    return False


def get_user_permissions(user_roles: list[str]) -> Set[Permission]:
    """
    Get all permissions for given user roles.
    
    Args:
        user_roles: List of role names
    
    Returns:
        Set of all permissions user has
    
    Example:
        >>> perms = get_user_permissions(["user"])
        >>> Permission.DEVICE_VIEW in perms
        True
    """
    permissions = set()
    for role in user_roles:
        permissions.update(ROLE_PERMISSIONS.get(role, set()))
    return permissions


def get_role_permissions(role_name: str) -> Set[Permission]:
    """
    Get all permissions for a specific role.
    
    Args:
        role_name: Name of the role
    
    Returns:
        Set of permissions for that role
    
    Example:
        >>> perms = get_role_permissions("manager")
        >>> len(perms)
        15
    """
    return ROLE_PERMISSIONS.get(role_name, set())


def can_user_perform_action(user_roles: list[str], action: str) -> bool:
    """
    Check if user can perform a specific action (by permission value string).
    
    Args:
        user_roles: List of role names
        action: Permission value string (e.g., "device:create")
    
    Returns:
        True if user has permission, False otherwise
    
    Example:
        >>> can_user_perform_action(["manager"], "device:view")
        True
        >>> can_user_perform_action(["manager"], "device:create")
        False
    """
    try:
        permission = Permission(action)
        return has_permission(user_roles, permission)
    except ValueError:
        return False


# ============================================================================
# PERMISSION GROUPS (for easier checking)
# ============================================================================

class PermissionGroups:
    """Grouped permissions for common use cases."""
    
    DEVICE_MANAGEMENT = {
        Permission.DEVICE_CREATE,
        Permission.DEVICE_UPDATE,
        Permission.DEVICE_DELETE,
    }
    
    LOAN_MANAGEMENT = {
        Permission.LOAN_CREATE,
        Permission.LOAN_UPDATE,
        Permission.LOAN_DELETE,
    }
    
    USER_MANAGEMENT = {
        Permission.USER_CREATE,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
    }
    
    READ_ONLY = {
        Permission.DEVICE_VIEW,
        Permission.LOAN_VIEW,
        Permission.USER_VIEW,
        Permission.EMPLOYEE_VIEW,
    }
    
    ADMIN_ONLY = {
        Permission.USER_DELETE,
        Permission.DEVICE_DELETE,
        Permission.LOAN_DELETE,
        Permission.MFA_ADMIN,
    }


def has_any_permission_in_group(user_roles: list[str], permission_group: Set[Permission]) -> bool:
    """
    Check if user has any permission from a group.
    
    Args:
        user_roles: List of role names
        permission_group: Set of permissions to check
    
    Returns:
        True if user has at least one permission from the group
    """
    user_perms = get_user_permissions(user_roles)
    return bool(user_perms & permission_group)


def has_all_permissions_in_group(user_roles: list[str], permission_group: Set[Permission]) -> bool:
    """
    Check if user has all permissions from a group.
    
    Args:
        user_roles: List of role names
        permission_group: Set of permissions to check
    
    Returns:
        True if user has all permissions from the group
    """
    user_perms = get_user_permissions(user_roles)
    return permission_group.issubset(user_perms)