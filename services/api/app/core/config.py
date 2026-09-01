"""
Application Configuration Settings.
Loads configuration from environment variables or .env file with production and development profiles.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "Smart Transit Intelligence System"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"  # "development" or "production"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "transit-secret-key-change-in-production-2026-secure"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    CORS_ORIGINS: List[str] = ["*"]
    
    # Database (Defaults to SQLite for local zero-dependency run, Postgres for docker/prod)
    DATABASE_URL: str = "sqlite:///./transit.db"
    
    # Cache / Redis
    REDIS_URL: Optional[str] = None  # e.g. "redis://localhost:6379/0"
    USE_IN_MEMORY_CACHE: bool = True
    
    # MQTT Broker
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: Optional[str] = None
    MQTT_PASSWORD: Optional[str] = None
    MQTT_TOPIC_PREFIX: str = "transit"
    
    # Stale Thresholds
    STALE_LOCATION_SECONDS: int = 30
    STALE_CROWD_SECONDS: int = 60
    
    # ML Models
    ML_MODELS_DIR: str = "./ml/models"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
