"""Application settings and configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, field_validator
from typing import Any, Dict, Optional, List


class Settings(BaseSettings):
    """Application settings with environment variable loading."""

    # API settings
    PROJECT_NAME: str
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    CORS_HEADERS: str = "*"
    CORS_METHODS: str = "*"

    # Database
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str = "5432"
    DATABASE_URI: Optional[PostgresDsn] = None
    SQL_ECHO: bool = False

    # Database connection pool settings
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # JWT Settings
    # ============================================
    # 🔐 TOKEN EXPIRATION CONFIGURATION
    # ============================================
    # Access Token: Short-lived token for API requests
    # - Too short: User needs to refresh frequently (poor UX)
    # - Too long: Security risk if token is compromised
    # Recommended: 15-60 minutes
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # ✅ 30 minutes (balanced)
    
    # Refresh Token: Long-lived token to get new access tokens
    # - Too short: User needs to login frequently (poor UX)
    # - Too long: Higher security risk
    # Recommended: 7-90 days depending on security requirements
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # ✅ 30 days (balanced)
    
    # JWT Secret Keys
    # CRITICAL: Use strong, unique keys for each environment
    # Generate with: openssl rand -hex 32
    JWT_SECRET_KEY: str
    JWT_REFRESH_SECRET_KEY: str  # Separate key for refresh tokens (more secure)
    ALGORITHM: str = "HS256"
    
    # ============================================
    # 📋 TOKEN DURATION GUIDELINES
    # ============================================
    # 
    # Scenario 1: High Security (Banking, Healthcare)
    # - ACCESS_TOKEN_EXPIRE_MINUTES: 15
    # - REFRESH_TOKEN_EXPIRE_DAYS: 7
    #
    # Scenario 2: Balanced (Web/Mobile Apps) ✅ CURRENT
    # - ACCESS_TOKEN_EXPIRE_MINUTES: 30
    # - REFRESH_TOKEN_EXPIRE_DAYS: 30
    #
    # Scenario 3: User Convenience (Internal Tools)
    # - ACCESS_TOKEN_EXPIRE_MINUTES: 60
    # - REFRESH_TOKEN_EXPIRE_DAYS: 90
    #
    # ============================================

    # Admin Seeder
    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = "admin123"

    # Redis - Required for token blacklist and session management
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_TTL: int = 3600

    # File handling
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_FILENAME_LENGTH: int = 50

    # Logging
    LOG_DIRECTORY: str = "logs"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    SERVICE_NAME: str

    # Password Security Settings
    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_MAX_LENGTH: int = 128
    PASSWORD_HISTORY_COUNT: int = 5
    PASSWORD_MAX_AGE_DAYS: int = 90
    ACCOUNT_LOCKOUT_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_DURATION_MINUTES: int = 15
    
    # Rate Limiting Settings
    RATE_LIMIT_CALLS: int = 100
    RATE_LIMIT_PERIOD: int = 60
    AUTH_RATE_LIMIT_CALLS: int = 5
    AUTH_RATE_LIMIT_PERIOD: int = 300
    
    # Session Management Settings
    MAX_SESSIONS_PER_USER: int = 5
    SESSION_EXPIRE_MINUTES: int = 1440  # 24 hours
    SESSION_CLEANUP_INTERVAL_HOURS: int = 24

    @field_validator("DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: Optional[str], info: Dict[str, Any]) -> Any:
        """Build PostgreSQL connection string from components."""
        if isinstance(v, str):
            return v

        values = info.data
        user = values.get("POSTGRES_USER", "")
        password = values.get("POSTGRES_PASSWORD", "")
        host = values.get("POSTGRES_SERVER", "")
        port = values.get("POSTGRES_PORT", "5432")
        db = values.get("POSTGRES_DB", "")

        auth = f"{user}:{password}" if password else user
        return f"postgresql://{auth}@{host}:{port}/{db}"

    @field_validator("API_V1_STR")
    def ensure_api_prefix_has_slash(cls, v: str) -> str:
        """Ensure API prefix starts with a slash."""
        if not v.startswith("/"):
            return f"/{v}"
        return v

    @property
    def CORS_ORIGINS_LIST(self) -> List[str]:
        """Convert CORS_ORIGINS string to list."""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def CORS_METHODS_LIST(self) -> List[str]:
        """Convert CORS_METHODS string to list."""
        if self.CORS_METHODS == "*":
            return ["*"]
        return [method.strip() for method in self.CORS_METHODS.split(",")]

    @property
    def CORS_HEADERS_LIST(self) -> List[str]:
        """Convert CORS_HEADERS string to list."""
        if self.CORS_HEADERS == "*":
            return ["*"]
        return [header.strip() for header in self.CORS_HEADERS.split(",")]

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


# Create global settings instance
settings = Settings()