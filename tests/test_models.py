# tests/test_models.py
"""Unit tests for database models."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

# Use checking valid imports
try:
    from src.models.user import User, PasswordResetToken
except ImportError:
    # Fallback/Mock for valid collection if src not found
    User = MagicMock()
    PasswordResetToken = MagicMock()


class TestUserModel:
    """Test cases for User model."""

    def test_user_creation(self, mock_user):
        """Test user object creation with required fields."""
        assert mock_user.nama == "Test User"
        assert mock_user.email == "test@example.com"
        assert mock_user.is_active is True
        assert mock_user.is_verified is True

    def test_is_locked_when_not_locked(self, mock_user):
        """Test is_locked returns False when account is not locked."""
        mock_user.locked_until = None
        assert mock_user.is_locked() is False

    def test_is_locked_when_locked(self, mock_user):
        """Test is_locked returns True when account is locked."""
        mock_user.locked_until = datetime.utcnow() + timedelta(hours=1)
        assert mock_user.is_locked() is True

    def test_is_locked_when_lock_expired(self, mock_user):
        """Test is_locked returns False when lock has expired."""
        mock_user.locked_until = datetime.utcnow() - timedelta(hours=1)
        assert mock_user.is_locked() is False

    def test_lock_account(self, mock_user):
        """Test lock_account sets correct lockout duration."""
        mock_user.failed_login_attempts = 1  # Index 0 = 5 minutes
        mock_user.lock_account()
        
        assert mock_user.locked_until is not None
        assert mock_user.lockout_duration_minutes == 5  # First lockout = 5 minutes

    def test_progressive_lockout(self, mock_user):
        """Test progressive lockout increases duration."""
        # First lockout (5 minutes) - index 0
        mock_user.failed_login_attempts = 1
        mock_user.lock_account()
        assert mock_user.lockout_duration_minutes == 5

        # Second lockout (15 minutes) - index 1
        mock_user.failed_login_attempts = 2
        mock_user.lock_account()
        assert mock_user.lockout_duration_minutes == 15

        # Third lockout (60 minutes) - index 2
        mock_user.failed_login_attempts = 3
        mock_user.lock_account()
        assert mock_user.lockout_duration_minutes == 60

        # Fourth+ lockout (24 hours) - index 3 or more
        mock_user.failed_login_attempts = 4
        mock_user.lock_account()
        assert mock_user.lockout_duration_minutes == 1440  # 24 hours

    def test_unlock_account(self, mock_user):
        """Test unlock_account resets all lock-related fields."""
        mock_user.failed_login_attempts = 5
        mock_user.locked_until = datetime.utcnow() + timedelta(hours=1)
        mock_user.lockout_duration_minutes = 60
        
        mock_user.unlock_account()
        
        assert mock_user.failed_login_attempts == 0
        assert mock_user.locked_until is None
        assert mock_user.lockout_duration_minutes == 0

    def test_increment_failed_attempts(self, mock_user):
        """Test increment_failed_attempts increases counter."""
        mock_user.failed_login_attempts = 0
        
        mock_user.increment_failed_attempts()
        assert mock_user.failed_login_attempts == 1
        
        mock_user.increment_failed_attempts()
        assert mock_user.failed_login_attempts == 2

    def test_auto_lock_after_5_failed_attempts(self, mock_user):
        """Test account automatically locks after 5 failed attempts."""
        mock_user.failed_login_attempts = 4
        mock_user.locked_until = None
        
        mock_user.increment_failed_attempts()
        
        assert mock_user.failed_login_attempts == 5
        assert mock_user.locked_until is not None

    def test_reset_failed_attempts(self, mock_user):
        """Test reset_failed_attempts resets counter to 0."""
        mock_user.failed_login_attempts = 3
        
        mock_user.reset_failed_attempts()
        
        assert mock_user.failed_login_attempts == 0

    def test_add_password_to_history(self, mock_user):
        """Test adding password to history."""
        mock_user.password_history = []
        
        mock_user.add_password_to_history("hash1")
        assert len(mock_user.password_history) == 1
        assert "hash1" in mock_user.password_history
        
        mock_user.add_password_to_history("hash2")
        assert len(mock_user.password_history) == 2

    def test_password_history_limit(self, mock_user):
        """Test password history keeps only last 5 passwords."""
        mock_user.password_history = []
        
        for i in range(7):
            mock_user.add_password_to_history(f"hash{i}")
        
        assert len(mock_user.password_history) == 5
        assert "hash6" in mock_user.password_history
        assert "hash0" not in mock_user.password_history  # Should be removed


class TestPasswordResetToken:
    """Test cases for PasswordResetToken model."""

    def test_token_is_valid(self):
        """Test is_valid returns True for valid token."""
        token = PasswordResetToken(
            id=1,
            user_id=1,
            token="valid_token",
            expires_at=datetime.utcnow() + timedelta(hours=1),
            used=False
        )
        assert token.is_valid() is True

    def test_token_is_invalid_when_used(self):
        """Test is_valid returns False for used token."""
        token = PasswordResetToken(
            id=1,
            user_id=1,
            token="used_token",
            expires_at=datetime.utcnow() + timedelta(hours=1),
            used=True
        )
        assert token.is_valid() is False

    def test_token_is_invalid_when_expired(self):
        """Test is_valid returns False for expired token."""
        token = PasswordResetToken(
            id=1,
            user_id=1,
            token="expired_token",
            expires_at=datetime.utcnow() - timedelta(hours=1),
            used=False
        )
        assert token.is_valid() is False
