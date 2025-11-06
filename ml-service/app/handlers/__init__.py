"""Request handlers for YOLO API endpoints"""
from app.handlers.base_handler import BaseImageHandler
from app.handlers.detection_handler import DetectionHandler
from app.handlers.annotation_handler import AnnotationHandler

__all__ = [
    "BaseImageHandler",
    "DetectionHandler",
    "AnnotationHandler",
]
