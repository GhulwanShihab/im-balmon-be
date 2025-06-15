"""User repository with password security features."""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_, update

from src.models.user import User, Role, UserRole, PasswordResetToken, MFABackupCode
from src.schemas.user import UserCreate, UserUpdate


class UserRepository:
    def __init__(self, session):
        self.session = session

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        query = select(User).where(
            and_(User.id == user_id, User.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        query = select(User).where(
            and_(User.email == email, User.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, user_data: UserCreate, hashed_password: str) -> User:
        """Create a new user."""
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            is_active=user_data.is_active,
            password_changed_at=datetime.utcnow(),
            password_history=[hashed_password]
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user."""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        update_data = user_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)

        user.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_password(self, user_id: int, new_hashed_password: str) -> Optional[User]:
        """Update user password with history tracking."""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        # Add current password to history
        user.add_password_to_history(user.hashed_password)
        
        # Update password
        user.hashed_password = new_hashed_password
        user.password_changed_at = datetime.utcnow()
        user.force_password_change = False
        user.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def increment_failed_login_attempts(self, user_id: int) -> User:
        """Increment failed login attempts counter with progressive lockout."""
        user = await self.get_by_id(user_id)
        if not user:
            return None
            
        user.increment_failed_attempts()
        user.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def reset_failed_login_attempts(self, user_id: int) -> None:
        """Reset failed login attempts counter."""
        query = (
            update(User)
            .where(User.id == user_id)
            .values(
                failed_login_attempts=0,
                last_login=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        await self.session.execute(query)
        await self.session.commit()

    async def unlock_account(self, user_id: int) -> None:
        """Unlock user account and reset failed attempts."""
        query = (
            update(User)
            .where(User.id == user_id)
            .values(
                failed_login_attempts=0,
                locked_until=None,
                lockout_duration_minutes=0,
                updated_at=datetime.utcnow()
            )
        )
        await self.session.execute(query)
        await self.session.commit()

    async def get_user_roles(self, user_id: int) -> List[Role]:
        """Get user roles."""
        query = (
            select(Role)
            .join(UserRole)
            .where(UserRole.user_id == user_id)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def add_role_to_user(self, user_id: int, role_id: int) -> UserRole:
        """Add role to user."""
        user_role = UserRole(user_id=user_id, role_id=role_id)
        self.session.add(user_role)
        await self.session.commit()
        await self.session.refresh(user_role)
        return user_role

    async def create_password_reset_token(self, user_id: int, token: str, expires_at: datetime) -> PasswordResetToken:
        """Create password reset token."""
        reset_token = PasswordResetToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        self.session.add(reset_token)
        await self.session.commit()
        await self.session.refresh(reset_token)
        return reset_token

    async def get_password_reset_token(self, token: str) -> Optional[PasswordResetToken]:
        """Get password reset token."""
        query = select(PasswordResetToken).where(PasswordResetToken.token == token)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def use_password_reset_token(self, token: str) -> bool:
        """Mark password reset token as used."""
        query = (
            update(PasswordResetToken)
            .where(PasswordResetToken.token == token)
            .values(used=True, updated_at=datetime.utcnow())
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    # MFA methods (Step 3)
    async def update_mfa_secret(self, user_id: int, secret: Optional[str], enabled: bool) -> None:
        """Update MFA secret and enabled status."""
        query = (
            update(User)
            .where(User.id == user_id)
            .values(
                mfa_secret=secret,
                mfa_enabled=enabled,
                updated_at=datetime.utcnow()
            )
        )
        await self.session.execute(query)
        await self.session.commit()
    
    async def save_backup_codes(self, user_id: int, codes: List[str]) -> None:
        """Save backup codes for user."""
        backup_codes = [
            MFABackupCode(user_id=user_id, code=code)
            for code in codes
        ]
        self.session.add_all(backup_codes)
        await self.session.commit()
    
    async def get_backup_codes(self, user_id: int) -> List[MFABackupCode]:
        """Get all backup codes for user."""
        query = select(MFABackupCode).where(MFABackupCode.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def use_backup_code(self, backup_code_id: int) -> None:
        """Mark backup code as used."""
        query = (
            update(MFABackupCode)
            .where(MFABackupCode.id == backup_code_id)
            .values(used=True, used_at=datetime.utcnow())
        )
        await self.session.execute(query)
        await self.session.commit()
    
    async def clear_backup_codes(self, user_id: int) -> None:
        """Clear all backup codes for user."""
        query = select(MFABackupCode).where(MFABackupCode.user_id == user_id)
        result = await self.session.execute(query)
        codes = result.scalars().all()
        
        for code in codes:
            await self.session.delete(code)
        
        await self.session.commit()
    
    async def get_mfa_stats(self) -> dict:
        """Get MFA statistics."""
        # Total users
        total_query = select(User).where(User.deleted_at.is_(None))
        total_result = await self.session.execute(total_query)
        total_users = len(total_result.scalars().all())
        
        # MFA enabled users
        mfa_query = select(User).where(
            and_(User.deleted_at.is_(None), User.mfa_enabled == True)
        )
        mfa_result = await self.session.execute(mfa_query)
        mfa_enabled_users = len(mfa_result.scalars().all())
        
        return {
            "total_users": total_users,
            "mfa_enabled_users": mfa_enabled_users
        }
    
    async def get_all_users(self, skip: int = 0, limit: int = 10, filters: dict = None, sort_by: str = "created_at", sort_order: str = "desc") -> List[User]:
        """Get all users with pagination and filtering."""
        query = select(User).where(User.deleted_at.is_(None))
        
        # Apply filters
        if filters:
            if filters.get("email"):
                query = query.where(User.email.ilike(f"%{filters['email']}%"))
            if filters.get("first_name"):
                query = query.where(User.first_name.ilike(f"%{filters['first_name']}%"))
            if filters.get("last_name"):
                query = query.where(User.last_name.ilike(f"%{filters['last_name']}%"))
            if filters.get("is_active") is not None:
                query = query.where(User.is_active == filters["is_active"])
            if filters.get("is_verified") is not None:
                query = query.where(User.is_verified == filters["is_verified"])
            if filters.get("mfa_enabled") is not None:
                query = query.where(User.mfa_enabled == filters["mfa_enabled"])
        
        # Apply sorting
        if hasattr(User, sort_by):
            if sort_order == "desc":
                query = query.order_by(getattr(User, sort_by).desc())
            else:
                query = query.order_by(getattr(User, sort_by))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count_users(self, filters: dict = None) -> int:
        """Count total users with filters."""
        from sqlalchemy import func
        query = select(func.count(User.id)).where(User.deleted_at.is_(None))
        
        # Apply filters
        if filters:
            if filters.get("email"):
                query = query.where(User.email.ilike(f"%{filters['email']}%"))
            if filters.get("first_name"):
                query = query.where(User.first_name.ilike(f"%{filters['first_name']}%"))
            if filters.get("last_name"):
                query = query.where(User.last_name.ilike(f"%{filters['last_name']}%"))
            if filters.get("is_active") is not None:
                query = query.where(User.is_active == filters["is_active"])
            if filters.get("is_verified") is not None:
                query = query.where(User.is_verified == filters["is_verified"])
            if filters.get("mfa_enabled") is not None:
                query = query.where(User.mfa_enabled == filters["mfa_enabled"])
        
        result = await self.session.execute(query)
        return result.scalar()
    
    async def delete_user(self, user_id: int) -> bool:
        """Soft delete user."""
        query = (
            update(User)
            .where(User.id == user_id)
            .values(deleted_at=datetime.utcnow(), updated_at=datetime.utcnow())
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def get_user_stats(self) -> dict:
        """Get comprehensive user statistics."""
        from sqlalchemy import func, and_
        
        # Total users
        total_query = select(func.count(User.id)).where(User.deleted_at.is_(None))
        total_result = await self.session.execute(total_query)
        total_users = total_result.scalar()
        
        # Active users
        active_query = select(func.count(User.id)).where(
            and_(User.deleted_at.is_(None), User.is_active == True)
        )
        active_result = await self.session.execute(active_query)
        active_users = active_result.scalar()
        
        # Verified users
        verified_query = select(func.count(User.id)).where(
            and_(User.deleted_at.is_(None), User.is_verified == True)
        )
        verified_result = await self.session.execute(verified_query)
        verified_users = verified_result.scalar()
        
        # Locked users
        locked_query = select(func.count(User.id)).where(
            and_(User.deleted_at.is_(None), User.locked_until > datetime.utcnow())
        )
        locked_result = await self.session.execute(locked_query)
        locked_users = locked_result.scalar()
        
        # MFA enabled users
        mfa_query = select(func.count(User.id)).where(
            and_(User.deleted_at.is_(None), User.mfa_enabled == True)
        )
        mfa_result = await self.session.execute(mfa_query)
        mfa_enabled_users = mfa_result.scalar()
        
        # New users statistics
        today = datetime.utcnow().date()
        week_ago = datetime.utcnow() - timedelta(days=7)
        month_ago = datetime.utcnow() - timedelta(days=30)
        
        # New users today
        today_query = select(func.count(User.id)).where(
            and_(User.deleted_at.is_(None), func.date(User.created_at) == today)
        )
        today_result = await self.session.execute(today_query)
        new_users_today = today_result.scalar()
        
        # New users this week
        week_query = select(func.count(User.id)).where(
            and_(User.deleted_at.is_(None), User.created_at >= week_ago)
        )
        week_result = await self.session.execute(week_query)
        new_users_this_week = week_result.scalar()
        
        # New users this month
        month_query = select(func.count(User.id)).where(
            and_(User.deleted_at.is_(None), User.created_at >= month_ago)
        )
        month_result = await self.session.execute(month_query)
        new_users_this_month = month_result.scalar()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "verified_users": verified_users,
            "locked_users": locked_users,
            "mfa_enabled_users": mfa_enabled_users,
            "new_users_today": new_users_today,
            "new_users_this_week": new_users_this_week,
            "new_users_this_month": new_users_this_month
        }
    
    async def remove_role_from_user(self, user_id: int, role_id: int) -> bool:
        """Remove role from user."""
        query = select(UserRole).where(
            and_(UserRole.user_id == user_id, UserRole.role_id == role_id)
        )
        result = await self.session.execute(query)
        user_role = result.scalar_one_or_none()
        
        if user_role:
            await self.session.delete(user_role)
            await self.session.commit()
            return True
        return False
    
    async def set_user_roles(self, user_id: int, role_ids: List[int]) -> None:
        """Set user roles (replace all existing roles)."""
        # Remove all existing roles
        query = select(UserRole).where(UserRole.user_id == user_id)
        result = await self.session.execute(query)
        existing_roles = result.scalars().all()
        
        for role in existing_roles:
            await self.session.delete(role)
        
        # Add new roles
        for role_id in role_ids:
            user_role = UserRole(user_id=user_id, role_id=role_id)
            self.session.add(user_role)
        
        await self.session.commit()
    
    async def get_all_roles(self) -> List[Role]:
        """Get all available roles."""
        query = select(Role).where(Role.deleted_at.is_(None))
        result = await self.session.execute(query)
        return result.scalars().all()
