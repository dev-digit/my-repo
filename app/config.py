"""
Configuration management for Pombi AI Assistant
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application
    app_name: str = "Pombi AI Assistant"
    version: str = "1.0.0"
    debug: bool = False

    # API Configuration
    api_prefix: str = "/api/v1"
    host: str = "0.0.0.0"
    port: int = 8000

    # Security
    jwt_secret: str = "your-secret-key-change-in-production"
    cors_origins: List[str] = ["http://localhost:3000"]

    # Rate Limiting
    rate_limit_per_minute: int = 60

    # AI Model Configuration
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_model: str = "openai"
    enable_local_models: bool = False
    ollama_base_url: str = "http://localhost:11434"

    # Database Configuration
    redis_url: str = "redis://localhost:6379"
    postgres_url: str = "postgresql://user:pass@localhost/pombi"

    # Memory Configuration
    session_timeout_minutes: int = 120  # 2 hours
    max_conversation_length: int = 50

    # Monitoring
    enable_metrics: bool = False
    sentry_dsn: Optional[str] = None
    log_level: str = "INFO"

    # Content Safety
    enable_content_filter: bool = True
    max_message_length: int = 4000

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()