"""Configuration management"""
import os
from pathlib import Path
from typing import Optional
import yaml
from pydantic_settings import BaseSettings
from pydantic import Field
import openai


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

    # LLM Provider: "openai" or "ollama"
    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    ollama_base_url: str = Field(default="http://localhost:11434/v1", alias="OLLAMA_BASE_URL")
    llm_chat_model: str = Field(default="", alias="LLM_CHAT_MODEL")
    llm_vision_model: str = Field(default="", alias="LLM_VISION_MODEL")

    # Transcription provider: "openai" or "faster-whisper"
    transcription_provider: str = Field(default="openai", alias="TRANSCRIPTION_PROVIDER")
    faster_whisper_model: str = Field(default="small", alias="FASTER_WHISPER_MODEL")
    faster_whisper_device: str = Field(default="cpu", alias="FASTER_WHISPER_DEVICE")
    faster_whisper_compute_type: str = Field(default="int8", alias="FASTER_WHISPER_COMPUTE_TYPE")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Default model mapping per provider
_MODEL_DEFAULTS = {
    "openai": {"chat": "gpt-4o-mini", "vision": "gpt-4o-mini"},
    "ollama": {"chat": "llama3.3", "vision": "llava"},
}


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


def get_llm_client() -> openai.OpenAI:
    """Create an OpenAI-compatible client for the active LLM provider.

    For 'openai': uses the real OpenAI API.
    For 'ollama': points the OpenAI SDK at the local Ollama server.
    """
    if settings.llm_provider == "ollama":
        return openai.OpenAI(
            base_url=settings.ollama_base_url,
            api_key="ollama",
        )
    return openai.OpenAI(api_key=settings.openai_api_key)


def get_chat_model() -> str:
    """Return the chat model name for the active provider."""
    if settings.llm_chat_model:
        return settings.llm_chat_model
    return _MODEL_DEFAULTS.get(settings.llm_provider, _MODEL_DEFAULTS["openai"])["chat"]


def get_vision_model() -> str:
    """Return the vision model name for the active provider."""
    if settings.llm_vision_model:
        return settings.llm_vision_model
    return _MODEL_DEFAULTS.get(settings.llm_provider, _MODEL_DEFAULTS["openai"])["vision"]
