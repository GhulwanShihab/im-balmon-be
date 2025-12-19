"""User service with password security features."""

from typing import Optional
from datetime import datetime
from fastapi import HTTPException, status

from src.models.user import User
from src.repositories.user import UserRepository
from src.schemas.user import UserCreate, UserUpdate, UserResponse, PasswordChange
from src.auth.jwt import get_password_hash, verify_password
from src.utils.validators import validate_password_history, validate_password_strength


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Register new user — requires admin approval before activation."""
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        hashed_password = get_password_hash(user_data.password)
        user = await self.user_repo.create(user_data, hashed_password)

        # pastikan user baru belum aktif dan belum diverifikasi
        user.is_active = False
        user.is_verified = False
        user.password_changed_at = datetime.utcnow()
        user.password_history = [hashed_password]
        await self.user_repo.session.commit()
        await self.user_repo.session.refresh(user)

        # ✅ kembalikan response, bukan raise (karena raise memutus flow)
        return UserResponse.model_validate(user)


    async def authenticate_user(self, email: str, password: str) -> Optional[UserResponse]:
        """Authenticate user with account lockout and admin approval checks."""
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None
        
        # Hanya user aktif & diverifikasi yang boleh login
        if not user.is_active or not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is not yet approved by admin."
            )

        if user.is_locked():
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked due to too many failed login attempts"
            )
        
        if not verify_password(password, user.hashed_password):
            updated_user = await self.user_repo.increment_failed_login_attempts(user.id)
            if updated_user and updated_user.is_locked():
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail=f"Account locked due to too many failed login attempts. Try again in {updated_user.lockout_duration_minutes} minutes."
                )
            return None
        
        await self.user_repo.reset_failed_login_attempts(user.id)
        return UserResponse.model_validate(user)

    async def get_user(self, user_id: int) -> Optional[UserResponse]:
        """Get user by ID."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None
        
        return UserResponse.model_validate(user)

    async def change_password(self, user_id: int, password_data: PasswordChange) -> UserResponse:
        """Change user password with validation."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify current password
        if not verify_password(password_data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # Check password history
        if not validate_password_history(password_data.new_password, user.password_history):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reuse any of your last 5 passwords"
            )

        # Hash new password
        new_hashed_password = get_password_hash(password_data.new_password)
        
        # Update password
        updated_user = await self.user_repo.update_password(user_id, new_hashed_password)
        
        return UserResponse.model_validate(updated_user)

    async def check_password_strength(self, password: str) -> dict:
        """Check password strength and provide feedback."""
        result = validate_password_strength(password)
        
        from src.utils.password import get_password_strength_feedback
        feedback = get_password_strength_feedback(password)
        
        return {
            "valid": result["valid"],
            "strength_score": result["strength_score"],
            "errors": result["errors"],
            "feedback": feedback
        }
    
    async def unlock_user_account(self, user_id: int) -> UserResponse:
        """Unlock user account (admin function)."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Unlock account
        await self.user_repo.unlock_account(user_id)
        
        # Get updated user
        updated_user = await self.user_repo.get_by_id(user_id)
        return UserResponse.model_validate(updated_user)
    
    async def get_all_users(self, skip: int = 0, limit: int = 10, filters: dict = None, sort_by: str = "created_at", sort_order: str = "desc"):
        """Get all users with pagination and filtering."""
        users = await self.user_repo.get_all_users(skip, limit, filters, sort_by, sort_order)
        total = await self.user_repo.count_users(filters)
        
        user_responses = [UserResponse.model_validate(user) for user in users]
        
        total_pages = (total + limit - 1) // limit
        page = (skip // limit) + 1
        
        from src.schemas.user import UserListResponse
        return UserListResponse(
            users=user_responses,
            total=total,
            page=page,
            page_size=limit,
            total_pages=total_pages
        )
    
    async def update_user(self, user_id: int, user_data) -> UserResponse:
        """Update user information."""
        user = await self.user_repo.update(user_id, user_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse.model_validate(user)
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete user (soft delete)."""
        success = await self.user_repo.delete_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return success
    
    async def get_user_stats(self) -> dict:
        """Get user statistics."""
        return await self.user_repo.get_user_stats()
    
    async def get_user_with_roles(self, user_id: int):
        """Get user with their roles."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        roles = await self.user_repo.get_user_roles(user_id)
        
        from src.schemas.user import UserWithRoles, RoleResponse
        role_responses = [RoleResponse.model_validate(role) for role in roles]
        
        user_response = UserResponse.model_validate(user)
        return UserWithRoles(
            **user_response.model_dump(),
            roles=role_responses
        )
    
    async def get_role_by_name(self, role_name: str):
        """Get role by name."""
        return await self.user_repo.get_role_by_name(role_name)

    async def update_user_roles(self, user_id: int, role_ids: list) -> UserResponse:
        """Update user roles."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        await self.user_repo.set_user_roles(user_id, role_ids)
        
        updated_user = await self.user_repo.get_by_id(user_id)
        return UserResponse.model_validate(updated_user)
    
    async def update_user_status(self, user_id: int, is_active: bool) -> UserResponse:
        """Update user active status."""
        from src.schemas.user import UserUpdate
        user_data = UserUpdate(is_active=is_active)
        return await self.update_user(user_id, user_data)
    
    async def get_user_account_status(self, user_id: int):
        """Get detailed user account status."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        from src.schemas.user import UserAccountStatus
        return UserAccountStatus(
            user_id=user.id,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_locked=user.is_locked(),
            failed_login_attempts=user.failed_login_attempts,
            locked_until=user.locked_until,
            last_login=user.last_login,
            mfa_enabled=user.mfa_enabled
        )
    
    async def get_all_roles(self):
        """Get all available roles."""
        roles = await self.user_repo.get_all_roles()
        from src.schemas.user import RoleResponse
        return [RoleResponse.model_validate(role) for role in roles]

    async def get_by_username(self, username: str) -> Optional[User]:
        query = select(User).where(
            and_(User.username == username, User.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def reject_user(self, user_id: int):
        user = await self.user_repo.get_by_id(user_id)  # 🔥 ganti ini
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        await self.user_repo.delete_user(user.id)
        return {"message": "User rejected and deleted permanently"}


    async def hard_delete_user(self, user_id: int) -> bool:
        """Permanently delete a user (used when rejecting pending users)."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return False

        await self.user_repo.session.delete(user)
        await self.user_repo.session.commit()
        return True

