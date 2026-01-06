from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    """Application settings"""
    APP_NAME: str = "ComplianceVault"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./compliance_vault.db"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Use Railway volume if available
        if "RAILWAY_VOLUME_MOUNT_PATH" in os.environ:
            volume_path = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
            self.DATABASE_URL = f"sqlite:///{volume_path}/compliance_vault.db"
    SQLALCHEMY_ECHO: bool = False
    
    # Security
    SECRET_KEY: str = "compliancevault-secret-key-change-in-production-2025"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # CORS
    # CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000"
    CORS_ORIGINS: str = "https://azharghafoor.github.io,https://compliance.azbers.com,https://compliancevault-production.up.railway.app"
    
    # File uploads (will be set in __init__ for Railway)
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    def __post_init__(self):
        # Override upload dir if Railway volume exists
        if "RAILWAY_VOLUME_MOUNT_PATH" in os.environ:
            volume_path = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
            self.UPLOAD_DIR = f"{volume_path}/uploads"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
