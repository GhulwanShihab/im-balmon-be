# tests/conftest.py
"""Pytest configuration and fixtures for testing."""

import sys
import os
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

# Add the project root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Pytest asyncio configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    from src.models.user import User
    
    user = User(
        id=1,
        nama="Test User",
        email="test@example.com",
        hashed_password="$2b$12$hashedpassword",
        is_active=True,
        is_verified=True,
        nip="12345",
        jabatan="Staff",
        password_changed_at=datetime.utcnow(),
        password_history=[],
        force_password_change=False,
        failed_login_attempts=0,
        locked_until=None,
        lockout_duration_minutes=0,
        last_login=None,
        mfa_enabled=False,
        mfa_secret=None,
    )
    return user


@pytest.fixture
def mock_device():
    """Create a mock device for testing."""
    return {
        "id": 1,
        "device_name": "Test Device",
        "device_code": "DEV-001",
        "nup_device": "NUP-001",
        "device_type": "Monitoring",
        "device_status": "TERSEDIA",
        "device_condition": "baik",
        "device_station": "Station 1",
        "device_room": "Room A",
        "device_year": 2024,
        "bmn_brand": "Brand X",
        "sample_brand": "Sample Y",
        "description": "Test device description",
    }


@pytest.fixture
def mock_loan():
    """Create a mock loan for testing."""
    return {
        "id": 1,
        "loan_number": "LOAN-001",
        "borrower_name": "John Doe",
        "borrower_user_id": 1,
        "activity_name": "Field Survey",
        "start_date": datetime.utcnow().date(),
        "end_date": datetime.utcnow().date(),
        "status": "DIPINJAM",
    }


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.rollback = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    return session
