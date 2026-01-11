"""Configuration management"""
import os
from pathlib import Path
from typing import Optional
import yaml
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # API Keys
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")

    # Instagram
    instagram_username: str = Field(default="", alias="INSTAGRAM_USERNAME")
    instagram_password: str = Field(default="", alias="INSTAGRAM_PASSWORD")

    # Facebook
    facebook_access_token: str = Field(default="", alias="FACEBOOK_ACCESS_TOKEN")

    # LinkedIn
    linkedin_email: str = Field(default="", alias="LINKEDIN_EMAIL")
    linkedin_password: str = Field(default="", alias="LINKEDIN_PASSWORD")

    # Beeper
    beeper_access_token: str = Field(default="", alias="BEEPER_ACCESS_TOKEN")

    # Database
    database_url: str = Field(default="sqlite:///./social_archive.db", alias="DATABASE_URL")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # Processing
    enable_transcription: bool = Field(default=True, alias="ENABLE_TRANSCRIPTION")
    enable_visual_analysis: bool = Field(default=True, alias="ENABLE_VISUAL_ANALYSIS")
    enable_auto_tagging: bool = Field(default=True, alias="ENABLE_AUTO_TAGGING")

    # Storage
    archive_path: Path = Field(default=Path("./archives"), alias="ARCHIVE_PATH")
    media_path: Path = Field(default=Path("./media"), alias="MEDIA_PATH")

    class Config:
        env_file = ".env"
        case_sensitive = False


def load_config(config_path: Optional[str] = None) -> dict:
    """Load configuration from YAML file"""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


# Global settings instance
settings = Settings()
config = load_config()
