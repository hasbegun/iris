"""
Base handler for image processing requests
Provides common functionality for all handlers
"""
from abc import ABC, abstractmethod
from typing import Optional, List
from fastapi import UploadFile, HTTPException
import logging

from app.services.yolo_service import YOLOService
from app.validators.image_validator import ImageValidator
from app.validators.video_validator import VideoValidator
from app.utils.media_utils import detect_media_type


class BaseImageHandler(ABC):
    """
    Base class for image processing handlers

    Provides common functionality:
    - Image reading and validation
    - Class parsing
    - Error handling
    - Logging
    """

    def __init__(self, yolo_service: YOLOService):
        """
        Initialize handler

        Args:
            yolo_service: YOLO service instance (injected by FastAPI)
        """
        self.yolo_service = yolo_service
        self.image_validator = ImageValidator(max_file_size_mb=10)
        self.video_validator = VideoValidator(max_file_size_mb=50)
        # Keep validator for backward compatibility
        self.validator = self.image_validator
        self.logger = logging.getLogger(self.__class__.__name__)

    async def read_and_validate_media(
        self,
        file: UploadFile,
        allow_video: bool = True
    ) -> bytes:
        """
        Read and validate image or video file

        Args:
            file: Uploaded file
            allow_video: Whether to allow video files (default: True)

        Returns:
            File bytes

        Raises:
            HTTPException: If validation fails
        """
        try:
            # Read file data
            file_bytes = await file.read()

            # Debug logging
            self.logger.info(f"File upload - filename: {file.filename}, content_type: {file.content_type}")

            # Detect media type from both filename and content_type
            media_type = detect_media_type(
                filename=file.filename,
                content_type=file.content_type
            )

            self.logger.info(f"Detected media type: {media_type}")

            # Validate based on type
            if media_type == "video":
                if not allow_video:
                    raise HTTPException(
                        status_code=400,
                        detail="This endpoint only accepts image files"
                    )

                validation = await self.video_validator.validate_bytes(
                    file_bytes,
                    filename=file.filename
                )
            else:
                validation = await self.image_validator.validate_bytes(file_bytes)

            # Check validation result
            if not validation.is_valid:
                raise HTTPException(
                    status_code=400,
                    detail=validation.error_message
                )

            self.logger.info(
                f"Validated {media_type}: {file.filename} "
                f"({len(file_bytes) / (1024*1024):.1f}MB)"
            )

            return file_bytes

        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to read media file: {e}", exc_info=True)
            raise HTTPException(
                status_code=400,
                detail=f"Failed to read media file: {str(e)}"
            )

    async def read_and_validate_image(self, image: UploadFile) -> bytes:
        """
        Read and validate image from upload (backward compatibility)

        Args:
            image: Uploaded image file

        Returns:
            bytes: Image data

        Raises:
            HTTPException: If image is invalid
        """
        return await self.read_and_validate_media(image, allow_video=False)

    def parse_classes(self, classes: Optional[str]) -> Optional[List[str]]:
        """
        Parse comma-separated classes string

        Args:
            classes: Comma-separated class names or None

        Returns:
            List of class names or None
        """
        if not classes:
            return None

        # Parse and clean up class names
        return [
            c.strip() for c in classes.split(",")
            if c.strip()
        ]

    def validate_confidence(self, confidence: float) -> None:
        """
        Validate confidence threshold

        Args:
            confidence: Confidence value

        Raises:
            HTTPException: If confidence is invalid
        """
        validation = self.validator.validate_confidence(confidence)
        if not validation.is_valid:
            raise HTTPException(
                status_code=400,
                detail=validation.error_message
            )

    @abstractmethod
    async def process(self, *args, **kwargs):
        """
        Process the request - implemented by subclasses

        Returns:
            Response data appropriate for the endpoint
        """
        pass
