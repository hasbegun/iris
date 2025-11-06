"""
Annotation handler for annotated image requests
Handles detect-annotated and detect-faces-annotated endpoints
"""
from typing import Optional
from fastapi import UploadFile, HTTPException
from fastapi.responses import Response

from app.handlers.base_handler import BaseImageHandler
from app.utils.async_utils import timed_operation, error_context
from app.utils.image_annotator import draw_bounding_boxes, draw_faces, draw_segmentation_masks


class AnnotationHandler(BaseImageHandler):
    """Handler for annotated image requests"""

    async def process(self, *args, **kwargs):
        """
        Base process method - not used directly.
        Use specific methods like process_annotated_detection or process_annotated_segmentation
        """
        raise NotImplementedError(
            "Use process_annotated_detection, process_annotated_segmentation, "
            "or process_annotated_face_detection instead"
        )

    async def process_annotated_detection(
        self,
        image: UploadFile,
        confidence: float,
        classes: Optional[str] = None,
        line_width: int = 3,
        font_size: int = 20
    ) -> Response:
        """
        Process annotated object detection request (supports images and videos)

        Args:
            image: Uploaded image or video file
            confidence: Detection confidence threshold
            classes: Optional comma-separated class names
            line_width: Bounding box line width
            font_size: Label font size

        Returns:
            JPEG response with annotated image

        Raises:
            HTTPException: If processing fails
        """
        async with error_context("Annotated detection"):
            # Validate confidence
            self.validate_confidence(confidence)

            # Read and validate (allow video)
            media_bytes = await self.read_and_validate_media(
                image,
                allow_video=True
            )

            # Parse classes
            class_list = self.parse_classes(classes)

            # Perform detection
            async with timed_operation("YOLO detection") as timer:
                result = await self.yolo_service.detect(
                    image_bytes=media_bytes,
                    confidence=confidence,
                    classes=class_list
                )

            # Handle service errors
            if result.get("status") == "error":
                raise HTTPException(
                    status_code=400,
                    detail=result.get("message", "Detection failed")
                )

            # Get detections
            detections = result.get("detections", [])

            self.logger.info(
                f"Detected {len(detections)} objects "
                f"in {timer['elapsed_ms']}ms, drawing annotations"
            )

            # If no detections, return original image
            if len(detections) == 0:
                return Response(content=media_bytes, media_type="image/jpeg")

            # Draw bounding boxes
            try:
                annotated_image_bytes = draw_bounding_boxes(
                    image_bytes=media_bytes,
                    detections=detections,
                    line_width=line_width,
                    font_size=font_size
                )
                return Response(content=annotated_image_bytes, media_type="image/jpeg")

            except Exception as e:
                self.logger.error(f"Annotation failed: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to draw annotations: {str(e)}"
                )

    async def process_annotated_face_detection(
        self,
        image: UploadFile,
        confidence: float,
        line_width: int = 3,
        font_size: int = 20
    ) -> Response:
        """
        Process annotated face detection request (supports images and videos)

        Args:
            image: Uploaded image or video file
            confidence: Detection confidence threshold
            line_width: Bounding box line width
            font_size: Label font size

        Returns:
            JPEG response with annotated image

        Raises:
            HTTPException: If processing fails
        """
        async with error_context("Annotated face detection"):
            # Validate confidence
            self.validate_confidence(confidence)

            # Read and validate (allow video)
            media_bytes = await self.read_and_validate_media(
                image,
                allow_video=True
            )

            # Perform face detection
            async with timed_operation("YOLO face detection") as timer:
                result = await self.yolo_service.detect_faces(
                    image_bytes=media_bytes,
                    confidence=confidence
                )

            # Handle service errors
            if result.get("status") == "error":
                raise HTTPException(
                    status_code=400,
                    detail=result.get("message", "Face detection failed")
                )

            # Get faces
            faces = result.get("faces", [])

            self.logger.info(
                f"Detected {len(faces)} faces "
                f"in {timer['elapsed_ms']}ms, drawing annotations"
            )

            # If no faces, return original image
            if len(faces) == 0:
                return Response(content=media_bytes, media_type="image/jpeg")

            # Draw bounding boxes
            try:
                annotated_image_bytes = draw_faces(
                    image_bytes=media_bytes,
                    faces=faces,
                    line_width=line_width,
                    font_size=font_size
                )
                return Response(content=annotated_image_bytes, media_type="image/jpeg")

            except Exception as e:
                self.logger.error(f"Annotation failed: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to draw annotations: {str(e)}"
                )

    async def process_annotated_segmentation(
        self,
        image: UploadFile,
        confidence: float,
        classes: Optional[str] = None,
        opacity: float = 0.5,
        line_width: int = 2,
        font_size: int = 20
    ) -> Response:
        """
        Process annotated segmentation request (supports images and videos)

        Args:
            image: Uploaded image or video file
            confidence: Segmentation confidence threshold
            classes: Optional comma-separated class names
            opacity: Mask transparency (0.0-1.0)
            line_width: Polygon outline width
            font_size: Label font size

        Returns:
            JPEG response with annotated image showing segmentation masks

        Raises:
            HTTPException: If processing fails
        """
        async with error_context("Annotated segmentation"):
            # Validate confidence
            self.validate_confidence(confidence)

            # Validate opacity
            if not (0.0 <= opacity <= 1.0):
                raise HTTPException(
                    status_code=400,
                    detail="Opacity must be between 0.0 and 1.0"
                )

            # Read and validate (allow video)
            media_bytes = await self.read_and_validate_media(
                image,
                allow_video=True
            )

            # Parse classes
            class_list = self.parse_classes(classes)

            # Perform segmentation
            async with timed_operation("YOLO segmentation") as timer:
                result = await self.yolo_service.segment(
                    image_bytes=media_bytes,
                    confidence=confidence,
                    classes=class_list
                )

            # Handle service errors
            if result.get("status") == "error":
                raise HTTPException(
                    status_code=400,
                    detail=result.get("message", "Segmentation failed")
                )

            # Get segments
            segments = result.get("segments", [])

            self.logger.info(
                f"Segmented {len(segments)} objects "
                f"in {timer['elapsed_ms']}ms, drawing masks"
            )

            # If no segments, return original image
            if len(segments) == 0:
                return Response(content=media_bytes, media_type="image/jpeg")

            # Draw segmentation masks
            try:
                annotated_image_bytes = draw_segmentation_masks(
                    image_bytes=media_bytes,
                    segments=segments,
                    opacity=opacity,
                    line_width=line_width,
                    font_size=font_size
                )
                return Response(content=annotated_image_bytes, media_type="image/jpeg")

            except Exception as e:
                self.logger.error(f"Segmentation annotation failed: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to draw segmentation masks: {str(e)}"
                )
