from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from functools import lru_cache
import os

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Cloud Bot"
    DEBUG: bool = False
    ENV: str = "dev"  # dev or prod
    
    @field_validator('DEBUG', mode='before')
    @classmethod
    def parse_debug(cls, v):
        """Handle DEBUG field - ignore non-boolean values from environment"""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            # If it's a string that's not a valid boolean, use default
            v_lower = v.lower().strip()
            if v_lower in ('true', '1', 'yes', 'on'):
                return True
            elif v_lower in ('false', '0', 'no', 'off'):
                return False
            # For invalid values like 'WARN', return default (False)
            return False
        return bool(v) if v is not None else False
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./bot.db"  # Default to SQLite, override with POSTGRES_URL for PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5433
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "1122"
    POSTGRES_DB: str = "bot_db"
    POSTGRES_POOL_SIZE: int = 10
    POSTGRES_MAX_OVERFLOW: int = 20
    
    # Redis (for FSM storage and caching)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[str] = None  # Override with full Redis URL if needed
    
    # Task Queue (RQ - Redis Queue)
    RQ_REDIS_URL: Optional[str] = None  # Uses REDIS_URL if not set
    RQ_QUEUE_NAME: str = "default"
    
    # Telegram
    BOT_TOKEN: str
    ADMIN_ID: int
    WEBHOOK_URL: Optional[str] = None
    WEBHOOK_PATH: str = "/webhook"
    
    # Long Polling Configuration (aiogram 3.x)
    POLLING_TIMEOUT: int = 20  # Seconds to wait for updates (Telegram default: 0, max: 50)
    POLLING_LIMIT: int = 100  # Max updates per request (1-100, default: 100)
    POLLING_ALLOWED_UPDATES: Optional[list] = None  # None = all updates, or specify list
    POLLING_CLOSE_TIMEOUT: int = 10  # Seconds to wait for graceful shutdown
    
    # Bot API Request Configuration
    API_REQUEST_TIMEOUT: int = 30  # Timeout for API requests (seconds)
    API_CONNECT_TIMEOUT: int = 10  # Connection timeout (seconds)
    API_READ_TIMEOUT: int = 30  # Read timeout (seconds)
    API_RETRIES: int = 3  # Number of retries for failed requests
    API_RETRY_DELAY: float = 1.0  # Initial delay between retries (seconds)
    API_MAX_RETRY_DELAY: float = 60.0  # Maximum delay between retries (seconds)
    
    # Network Resilience
    POLLING_RECONNECT_DELAY: float = 5.0  # Delay before reconnecting after error (seconds)
    POLLING_MAX_RECONNECT_DELAY: float = 60.0  # Maximum reconnection delay (exponential backoff)
    POLLING_BACKOFF_MULTIPLIER: float = 2.0  # Exponential backoff multiplier
    
    # Security
    SECRET_KEY: str = "supersecretkey"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin"
    
    # Admin Panel
    ADMIN_PANEL_HOST: str = "0.0.0.0"
    ADMIN_PANEL_PORT: int = 8000
    ADMIN_PANEL_USERNAME: str = "admin"  # For help display
    
    # Pagination
    FILES_PER_PAGE: int = 5
    USERS_PER_PAGE: int = 10
    
    # Timeouts and Retries
    REQUEST_TIMEOUT: int = 30  # seconds
    FILE_DOWNLOAD_TIMEOUT: int = 300  # 5 minutes for large files
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_BASE: float = 2.0  # Exponential backoff base
    
    # Broadcast Settings
    BROADCAST_BATCH_SIZE: int = 30  # Messages per batch (Telegram limit is ~30/sec)
    BROADCAST_DELAY: float = 0.05  # Delay between batches in seconds

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore",
        env_ignore_empty=True
    )

@lru_cache
def get_settings():
    return Settings()

settings = get_settings()
