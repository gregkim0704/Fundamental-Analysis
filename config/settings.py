"""Application settings and configuration."""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API Keys
    anthropic_api_key: str = Field(default="", description="Anthropic API key for Claude")
    opendart_api_key: str = Field(default="", description="OpenDART API key for Korean market data")
    fred_api_key: str = Field(default="", description="FRED API key for economic data")
    alpha_vantage_api_key: str = Field(default="", description="Alpha Vantage API key")

    # Database
    database_url: str = Field(
        default="sqlite:///./data/fundamental_analysis.db",
        description="Database connection URL"
    )
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")

    # Application
    debug: bool = Field(default=False, description="Debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level"
    )

    # Agent Settings
    debate_rounds: int = Field(default=3, description="Number of debate rounds")
    max_agent_iterations: int = Field(default=10, description="Max iterations per agent")
    agent_timeout_seconds: int = Field(default=300, description="Agent timeout in seconds")

    # Model Settings
    default_model: str = Field(
        default="claude-opus-4-5-20251101",
        description="Default LLM model"
    )
    temperature: float = Field(default=0.3, description="LLM temperature")

    # Cache Settings
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds")

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.debug


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
