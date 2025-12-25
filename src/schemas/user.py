"""User schemas with password security validation."""

from typing import List, Optional
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator, Field
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema."""
    username: str
    email: EmailStr
    is_active: bool = True
    

class UserCreate(UserBase):
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, password: str) -> str:
        from src.utils.validators import validate_password_strength
        
        result = validate_password_strength(password)
        if not result["valid"]:
            raise ValueError(f"Password validation failed: {', '.join(result['errors'])}")
        
        return password



class UserUpdate(BaseModel):
    """Schema for updating a user."""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    updated_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None  # opsional, untuk penolakan user



class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    is_verified: bool
    password_changed_at: Optional[datetime] = None
    force_password_change: bool
    last_login: Optional[datetime] = None
    mfa_enabled: Optional[bool]
    
    model_config = ConfigDict(from_attributes=True)


class UserResponseWithRoles(UserResponse):
    """Schema for user response with role names for list display."""
    role_names: List[str] = []


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str
    mfa_code: Optional[str] = Field(None, min_length=6, max_length=8, description="MFA TOTP code or backup code")


class PasswordChange(BaseModel):
    """Schema for password change."""
    current_password: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, password: str) -> str:
        from src.utils.validators import validate_password_strength
        
        result = validate_password_strength(password)
        if not result["valid"]:
            raise ValueError(f"Password validation failed: {', '.join(result['errors'])}")
        
        return password


class PasswordReset(BaseModel):
    """Schema for password reset request."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, password: str) -> str:
        from src.utils.validators import validate_password_strength
        
        result = validate_password_strength(password)
        if not result["valid"]:
            raise ValueError(f"Password validation failed: {', '.join(result['errors'])}")
        
        return password


class PasswordStrengthCheck(BaseModel):
    """Schema for password strength checking."""
    password: str


class PasswordStrengthResponse(BaseModel):
    """Schema for password strength response."""
    valid: bool
    strength_score: int
    errors: List[str]
    feedback: List[str]


class Token(BaseModel):
    """Schema for token response with session information."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    mfa_verified: bool = Field(default=False, description="Whether MFA was verified")
    requires_mfa: bool = Field(default=False, description="Whether MFA is required for this user")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")
    device_fingerprint: Optional[str] = Field(None, description="Device fingerprint for security")


class TokenData(BaseModel):
    """Schema for token data."""
    user_id: Optional[int] = None


class UserListResponse(BaseModel):
    """Schema for user list response with pagination."""
    users: List["UserResponseWithRoles"]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserSearchFilter(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    mfa_enabled: Optional[bool] = None
    role_id: Optional[int] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    sort_by: Optional[str] = Field(default="created_at", description="Field to sort by")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class UserStatusUpdate(BaseModel):
    """Schema for updating user status."""
    is_active: bool
    reason: Optional[str] = None


class UserRoleUpdate(BaseModel):
    """Schema for updating user roles."""
    role_ids: List[int]


class RoleResponse(BaseModel):
    """Schema for role response."""
    id: int
    name: str
    description: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserWithRoles(UserResponse):
    """Schema for user response with roles."""
    roles: List[RoleResponse] = []


class UserAccountStatus(BaseModel):
    """Schema for user account status."""
    user_id: int
    is_active: bool
    is_verified: bool
    is_locked: bool
    failed_login_attempts: int
    locked_until: Optional[datetime] = None
    last_login: Optional[datetime] = None
    mfa_enabled: bool


class UserStats(BaseModel):
    """Schema for user statistics."""
    total_users: int
    active_users: int
    verified_users: int
    locked_users: int
    mfa_enabled_users: int
    pending_users: int
    new_users_today: int
    new_users_this_week: int
    new_users_this_month: int
