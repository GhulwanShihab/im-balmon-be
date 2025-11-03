"""Models package - FIXED import order."""

# Base model first
from .base import BaseModel

# Independent models (no dependencies on other models)
from .user import User, Role, UserRole, PasswordResetToken, MFABackupCode
from .perangkat import Device, DeviceStatus
from .device_child import DeviceChild
from .employee import Employee

# Models with dependencies (after all their dependencies)
from .loan import (
    DeviceLoan, 
    DeviceLoanItem, 
    LoanHistory, 
    DeviceConditionChangeRequest,
    LoanStatus, 
    DeviceCondition,
    ConditionChangeStatus
)

# Device groups (depends on User, Device, DeviceChild) - LAST
from .device_group import DeviceGroup, DeviceGroupItem

__all__ = [
    # Base
    "BaseModel",
    
    # User
    "User",
    "Role",
    "UserRole",
    "PasswordResetToken",
    "MFABackupCode",
    
    # Device
    "Device",
    "DeviceStatus",
    "DeviceChild",
    
    # Employee
    "Employee",
    
    # Loan
    "DeviceLoan",
    "DeviceLoanItem",
    "LoanHistory",
    "DeviceConditionChangeRequest",
    "LoanStatus",
    "DeviceCondition",
    "ConditionChangeStatus",
    
    # Device Group
    "DeviceGroup",
    "DeviceGroupItem",
]