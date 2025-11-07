"""
Configuration management for the vision AI backend.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # Ollama configuration
    ollama_host: str = "http://localhost:11434"
    vision_model: str = "llava:latest"
    chat_model: str = "gemma3:latest"

    # API configuration
    api_host: str = "0.0.0.0"
    api_port: int = 9000

    # Context management
    max_context_messages: int = 10
    context_ttl_seconds: int = 3600  # 1 hour

    # Video processing
    video_frame_interval: float = 1.0  # Process one frame per second
    max_video_duration: int = 300  # 5 minutes max

    # ML Service configuration
    ml_service_url: str = "http://localhost:9001"
    ml_service_timeout: int = 30
    ml_service_retry_attempts: int = 3

    # Agent configuration (ReAct pattern)
    agent_llm_model: str = "qwen2.5-coder:32b"  # Best model for tool calling with ReAct
    agent_max_iterations: int = 5
    agent_verbose: bool = True
    yolo_default_confidence: float = 0.7  # Higher confidence for more accurate detections


settings = Settings()
