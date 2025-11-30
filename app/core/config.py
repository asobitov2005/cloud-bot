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
    DATABASE_URL: str = "sqlite+aiosqlite:///./bot.db"
    
    # Telegram
    BOT_TOKEN: str
    ADMIN_ID: int
    WEBHOOK_URL: Optional[str] = None
    WEBHOOK_PATH: str = "/webhook"
    
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
