"""
ML Service Configuration
Manages settings for YOLO models and inference
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """ML Service Settings"""

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 9001
    environment: str = "development"
    auto_reload: bool = False  # Set to True for development auto-reload

    # YOLO Model Paths
    detection_model_path: str = "models/yolo11n.pt"
    segmentation_model_path: str = "models/yolo11n-seg.pt"
    face_model_path: str = "models/yolo11n-face.pt"

    # Inference Configuration
    device: str = "cpu"  # "cpu" or "cuda" for GPU
    batch_size: int = 1
    max_image_size: int = 1920

    # Performance
    num_workers: int = 4
    model_warmup: bool = True

    # Image Processing
    supported_formats: list = ["jpg", "jpeg", "png", "webp", "bmp"]
    max_file_size_mb: int = 10

    # Model Download (if not exists)
    auto_download_models: bool = True

    # Pydantic v2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        protected_namespaces=('settings_',)  # Fix Pydantic warning about 'model_' namespace
    )


settings = Settings()
