"""
Detection handler for object detection requests
Handles detect, segment, and detect-faces endpoints
"""
from typing import Optional
from fastapi import UploadFile, HTTPException

from app.handlers.base_handler import BaseImageHandler
from app.utils.async_utils import timed_operation, error_context


class DetectionHandler(BaseImageHandler):
    """Handler for object detection requests"""

    async def process(
        self,
        image: UploadFile,
        confidence: float,
        classes: Optional[str] = None
    ) -> dict:
        """
        Process object detection request (supports images and videos)

        Args:
            image: Uploaded image or video file
            confidence: Detection confidence threshold
            classes: Optional comma-separated class names

        Returns:
            Detection result dictionary

        Raises:
            HTTPException: If processing fails
        """
        async with error_context("Object detection"):
            # Validate confidence
            self.validate_confidence(confidence)

            # Read and validate (allow video for object detection)
            image_bytes = await self.read_and_validate_media(
                image,
                allow_video=True  # Object detection works on video frames
            )

            # Parse classes
            class_list = self.parse_classes(classes)

            # Perform detection with timing
            async with timed_operation("YOLO detection") as timer:
                result = await self.yolo_service.detect(
                    image_bytes=image_bytes,
                    confidence=confidence,
                    classes=class_list
                )

            # Handle service errors
            if result.get("status") == "error":
                raise HTTPException(
                    status_code=400,
                    detail=result.get("message", "Detection failed")
                )

            self.logger.info(
                f"Detected {result.get('count', 0)} objects "
                f"in {timer['elapsed_ms']}ms"
            )

            return result

    async def process_segmentation(
        self,
        image: UploadFile,
        confidence: float,
        classes: Optional[str] = None
    ) -> dict:
        """
        Process segmentation request (supports images and videos)

        Args:
            image: Uploaded image or video file
            confidence: Segmentation confidence threshold
            classes: Optional comma-separated class names

        Returns:
            Segmentation result dictionary

        Raises:
            HTTPException: If processing fails
        """
        async with error_context("Segmentation"):
            # Validate confidence
            self.validate_confidence(confidence)

            # Read and validate (allow video for segmentation)
            image_bytes = await self.read_and_validate_media(
                image,
                allow_video=True  # Segmentation works on video frames
            )

            # Parse classes
            class_list = self.parse_classes(classes)

            # Perform segmentation with timing
            async with timed_operation("YOLO segmentation") as timer:
                result = await self.yolo_service.segment(
                    image_bytes=image_bytes,
                    confidence=confidence,
                    classes=class_list
                )

            # Handle service errors
            if result.get("status") == "error":
                raise HTTPException(
                    status_code=400,
                    detail=result.get("message", "Segmentation failed")
                )

            self.logger.info(
                f"Segmented {result.get('count', 0)} objects "
                f"in {timer['elapsed_ms']}ms"
            )

            return result

    async def process_face_detection(
        self,
        image: UploadFile,
        confidence: float
    ) -> dict:
        """
        Process face detection request (supports images and videos)

        Args:
            image: Uploaded image or video file
            confidence: Detection confidence threshold

        Returns:
            Face detection result dictionary

        Raises:
            HTTPException: If processing fails
        """
        async with error_context("Face detection"):
            # Validate confidence
            self.validate_confidence(confidence)

            # Read and validate (allow video for face detection)
            media_bytes = await self.read_and_validate_media(
                image,
                allow_video=True  # Face detection works on video frames
            )

            # Perform face detection with timing
            async with timed_operation("YOLO face detection") as timer:
                result = await self.yolo_service.detect_faces(
                    image_bytes=media_bytes,  # Works for both image and video
                    confidence=confidence
                )

            # Handle service errors
            if result.get("status") == "error":
                raise HTTPException(
                    status_code=400,
                    detail=result.get("message", "Face detection failed")
                )

            self.logger.info(
                f"Detected {result.get('count', 0)} faces "
                f"in {timer['elapsed_ms']}ms"
            )

            return result
