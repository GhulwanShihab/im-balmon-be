"""API router configuration."""

from fastapi import APIRouter

from src.api.endpoints import auth, users, mfa, devices, loans, export

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(mfa.router, prefix="/mfa", tags=["multi-factor-authentication"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(loans.router, prefix="/loans", tags=["loans"])
api_router.include_router(export.router, prefix="/export", tags=["export"])