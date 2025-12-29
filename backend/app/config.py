"""Application configuration using Pydantic settings"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = "WebGST"
    app_env: str = "development"
    debug: bool = True
    version: str = "1.0.0"
    
    # Database
    database_url: str = "sqlite:///./webgst.db"
    
    # Security
    secret_key: str = "change-this-secret-key-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Admin Configuration
    admin_registration_enabled: bool = True

    # Compliance toggles (do NOT disable in production)
    gstin_checksum_enforced: bool = False
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()
