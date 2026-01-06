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
    SQLALCHEMY_ECHO: bool = False
    
    # Security
    SECRET_KEY: str = "compliancevault-secret-key-change-in-production-2025"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # CORS
    # CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000"
    CORS_ORIGINS: str = "https://azharghafoor.github.io,https://compliance.azbers.com,https://compliancevault-production.up.railway.app"
    
    # File uploads
    UPLOAD_DIR: str = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "uploads") + "/uploads" if "RAILWAY_VOLUME_MOUNT_PATH" in os.environ else "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
