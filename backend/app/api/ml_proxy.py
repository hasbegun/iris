"""
ML Service Proxy API
Proxies requests directly to the ML service for live camera streaming
and static image segmentation
"""
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional
import logging

from app.services.ml_client import ml_client

logger = logging.getLogger(__name__)

# Router for live camera streaming endpoints (/ml/api/...)
router = APIRouter(prefix="/ml/api", tags=["ml"])

# Router for static image endpoints (/api/...)
api_router = APIRouter(prefix="/api", tags=["ml-static"])


@router.post("/detect-stream")
async def detect_stream(
    image: UploadFile = File(..., description="Camera frame to analyze"),
    confidence: float = Form(0.5, ge=0.0, le=1.0, description="Detection confidence threshold"),
    classes: Optional[str] = Form(None, description="Comma-separated class names to detect"),
):
    """
    Real-time object detection for live camera streams.

    This endpoint proxies directly to the ML service's detect-stream endpoint
    optimized for low-latency live camera processing.

    **Parameters:**
    - **image**: Camera frame (JPEG)
    - **confidence**: Detection confidence threshold (0.0 - 1.0)
    - **classes**: Optional comma-separated list of object classes

    **Returns:**
    - Lightweight detection results with bounding boxes
    """
    try:
        # Read image bytes
        image_bytes = await image.read()

        # Parse classes if provided
        class_list = None
        if classes and classes.strip():
            class_list = [c.strip() for c in classes.split(',') if c.strip()]

        # Call ML service
        result = await ml_client.detect_stream(
            image_bytes=image_bytes,
            confidence=confidence,
            classes=class_list
        )

        return result

    except Exception as e:
        logger.error(f"Stream detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/segment-stream")
async def segment_stream(
    image: UploadFile = File(..., description="Camera frame to segment"),
    confidence: float = Form(0.5, ge=0.0, le=1.0, description="Segmentation confidence threshold"),
    classes: Optional[str] = Form(None, description="Comma-separated class names to segment"),
):
    """
    Real-time instance segmentation for live camera streams.

    This endpoint proxies directly to the ML service's segment-stream endpoint
    optimized for low-latency live camera segmentation.

    **Parameters:**
    - **image**: Camera frame (JPEG)
    - **confidence**: Segmentation confidence threshold (0.0 - 1.0)
    - **classes**: Optional comma-separated list of object classes

    **Returns:**
    - Lightweight segmentation results with polygon masks
    """
    try:
        # Read image bytes
        image_bytes = await image.read()

        # Parse classes if provided
        class_list = None
        if classes and classes.strip():
            class_list = [c.strip() for c in classes.split(',') if c.strip()]

        # Call ML service
        result = await ml_client.segment_stream(
            image_bytes=image_bytes,
            confidence=confidence,
            classes=class_list
        )

        return result

    except Exception as e:
        logger.error(f"Stream segmentation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/segment")
async def segment_image(
    image: UploadFile = File(..., description="Image to segment"),
    confidence: float = Form(0.5, ge=0.0, le=1.0, description="Segmentation confidence threshold"),
    classes: Optional[str] = Form(None, description="Comma-separated class names to segment"),
):
    """
    Instance segmentation for static images.

    This endpoint proxies to the ML service's /api/segment endpoint
    for processing static images with instance segmentation.

    **Parameters:**
    - **image**: Image file (JPEG, PNG, etc.)
    - **confidence**: Segmentation confidence threshold (0.0 - 1.0)
    - **classes**: Optional comma-separated list of object classes

    **Returns:**
    - Segmentation results with polygon masks, bounding boxes, and metadata
    """
    try:
        # Read image bytes
        image_bytes = await image.read()

        # Parse classes if provided
        class_list = None
        if classes and classes.strip():
            class_list = [c.strip() for c in classes.split(',') if c.strip()]

        # Call ML service segmentation endpoint
        result = await ml_client.segment_objects(
            image_bytes=image_bytes,
            confidence=confidence,
            classes=class_list
        )

        logger.info(f"Segmented {result.get('count', 0)} objects in image")
        return result

    except Exception as e:
        logger.error(f"Image segmentation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
