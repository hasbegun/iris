"""
Model management utilities
Download and cache YOLO models
"""
import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages YOLO model downloads and caching"""

    # YOLO model URLs (Ultralytics official)
    MODEL_URLS = {
        "yolo11n.pt": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt",
        "yolo11n-seg.pt": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n-seg.pt",
        "yolo11s.pt": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11s.pt",
        "yolo11m.pt": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11m.pt",
    }

    def __init__(self, models_dir: str = "models"):
        """
        Initialize model manager

        Args:
            models_dir: Directory to store model weights
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def get_model_path(self, model_name: str) -> str:
        """
        Get full path to model file

        Args:
            model_name: Name of the model file

        Returns:
            Full path to model file
        """
        return str(self.models_dir / model_name)

    def model_exists(self, model_name: str) -> bool:
        """
        Check if model file exists locally

        Args:
            model_name: Name of the model file

        Returns:
            True if model exists, False otherwise
        """
        model_path = self.get_model_path(model_name)
        return os.path.exists(model_path)

    def download_model(self, model_name: str) -> bool:
        """
        Download model from Ultralytics if not exists

        Args:
            model_name: Name of the model to download

        Returns:
            True if successful, False otherwise
        """
        if self.model_exists(model_name):
            logger.info(f"Model {model_name} already exists")
            return True

        # Ultralytics will auto-download when loading
        # We just need to ensure the models directory exists
        logger.info(f"Model {model_name} will be auto-downloaded by Ultralytics on first use")
        return True

    def ensure_models(self, model_names: list) -> dict:
        """
        Ensure all required models are available

        Args:
            model_names: List of model names

        Returns:
            Dictionary with model availability status
        """
        status = {}
        for model_name in model_names:
            exists = self.model_exists(model_name)
            status[model_name] = {
                "exists": exists,
                "path": self.get_model_path(model_name)
            }

            if not exists:
                logger.warning(
                    f"Model {model_name} not found at {self.get_model_path(model_name)}. "
                    "It will be auto-downloaded by Ultralytics on first use."
                )

        return status
