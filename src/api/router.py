"""API router configuration."""

from fastapi import APIRouter

from src.api.endpoints import (
    auth, 
    users, 
    mfa, 
    devices, 
    device_child, 
    loans, 
    employees, 
    export, 
    device_group,
    device_export  # ✅ Import router baru
)

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(mfa.router, prefix="/mfa", tags=["multi-factor-authentication"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(device_child.router, prefix="/device-children", tags=["device-children"])
api_router.include_router(device_group.router, prefix="/device-groups", tags=["device-groups"])
api_router.include_router(loans.router, prefix="/loans", tags=["loans"])
api_router.include_router(employees.router, prefix="/employees", tags=["employees"])
api_router.include_router(export.router, prefix="/export", tags=["export"])  # PDF export
api_router.include_router(device_export.router, prefix="/devices/export", tags=["device-export"])  # ✅ Excel export