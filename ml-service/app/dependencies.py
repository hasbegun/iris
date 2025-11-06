"""
Dependency injection for FastAPI endpoints
Provides clean, testable access to services
"""
from typing import Optional, Annotated
from fastapi import Depends, HTTPException

from app.services.yolo_service import YOLOService
from app.services.video_yolo_service import VideoYOLOService

# Singleton instance - managed by main.py
_yolo_service_instance: Optional[YOLOService] = None
_video_yolo_service_instance: Optional[VideoYOLOService] = None


def get_yolo_service() -> YOLOService:
    """
    FastAPI dependency to get YOLOService instance

    Returns:
        YOLOService: The YOLO service singleton

    Raises:
        HTTPException: If service not initialized (503)

    Usage:
        @router.post("/endpoint")
        async def endpoint(service: YOLOServiceDep):
            result = await service.detect(...)
    """
    if _yolo_service_instance is None:
        raise HTTPException(
            status_code=503,
            detail="YOLO service not initialized. Please wait for models to load."
        )
    return _yolo_service_instance


def set_yolo_service_instance(service: YOLOService) -> None:
    """
    Set the YOLOService singleton instance

    Called once during application startup

    Args:
        service: Initialized YOLOService instance
    """
    global _yolo_service_instance
    _yolo_service_instance = service


def get_video_yolo_service() -> VideoYOLOService:
    """
    FastAPI dependency to get VideoYOLOService instance

    Returns:
        VideoYOLOService: The video YOLO service singleton

    Raises:
        HTTPException: If service not initialized (503)
    """
    if _video_yolo_service_instance is None:
        raise HTTPException(
            status_code=503,
            detail="Video YOLO service not initialized. Please wait for models to load."
        )
    return _video_yolo_service_instance


def set_video_yolo_service_instance(service: VideoYOLOService) -> None:
    """
    Set the VideoYOLOService singleton instance

    Called once during application startup

    Args:
        service: Initialized VideoYOLOService instance
    """
    global _video_yolo_service_instance
    _video_yolo_service_instance = service


# Type alias for cleaner endpoint signatures
YOLOServiceDep = Annotated[YOLOService, Depends(get_yolo_service)]
VideoYOLOServiceDep = Annotated[VideoYOLOService, Depends(get_video_yolo_service)]
