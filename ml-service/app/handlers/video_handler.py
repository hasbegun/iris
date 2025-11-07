"""
Video processing handler

Handles video-specific requests including frame extraction and processing.
"""
from typing import Optional, Dict, List
from fastapi import UploadFile
import logging

from app.handlers.base_handler import BaseImageHandler
from app.services.yolo_service import YOLOService
from app.services.video_frame_service import VideoFrameService


logger = logging.getLogger(__name__)


class VideoHandler(BaseImageHandler):
    """
    Handler for video processing requests

    Provides methods for:
    - Single frame extraction and detection
    - Multiple frame extraction and detection
    - Video metadata retrieval
    """

    def __init__(
        self,
        yolo_service: YOLOService,
        frame_service: Optional[VideoFrameService] = None
    ):
        """
        Initialize video handler

        Args:
            yolo_service: YOLO service instance
            frame_service: Video frame service (creates new if None)
        """
        super().__init__(yolo_service)
        self.frame_service = frame_service or VideoFrameService()

    async def process_single_frame_detection(
        self,
        video: UploadFile,
        confidence: float,
        classes: Optional[str] = None,
        frame_index: Optional[int] = None
    ) -> Dict:
        """
        Extract a single frame from video and run detection

        Args:
            video: Uploaded video file
            confidence: Detection confidence threshold
            classes: Comma-separated class names (optional)
            frame_index: Frame index to extract (None = middle frame)

        Returns:
            Dict with frame_base64, detections, and metadata
        """
        # Read and validate video
        video_bytes = await self.read_and_validate_media(video, allow_video=True)

        # Parse classes
        class_list = self.parse_classes(classes)

        # Extract frame
        frame_data = self.frame_service.extract_single_frame(
            video_bytes=video_bytes,
            frame_index=frame_index,
            include_base64=True,
            jpeg_quality=85
        )

        # Get video info for metadata
        video_info = self.frame_service.get_video_info(video_bytes)

        # Run detection on the extracted frame
        result = await self.yolo_service.detect(
            image_bytes=frame_data.frame_bytes,
            confidence=confidence,
            classes=class_list
        )

        # Return frame + detections
        return {
            "status": "success",
            "frame_base64": frame_data.frame_base64,
            "frame_index": frame_data.frame_index,
            "total_frames": video_info.total_frames,
            "detections": result.get("detections", []),
            "image_shape": result.get("image_shape", []),
            "count": result.get("count", 0)
        }

    async def process_multiple_frames_detection(
        self,
        video: UploadFile,
        confidence: float,
        classes: Optional[str] = None,
        frame_interval: float = 2.0,
        max_frames: int = 10
    ) -> Dict:
        """
        Extract multiple frames from video and run detection on each

        Args:
            video: Uploaded video file
            confidence: Detection confidence threshold
            classes: Comma-separated class names (optional)
            frame_interval: Seconds between extracted frames
            max_frames: Maximum number of frames to extract

        Returns:
            Dict with array of frames with detections
        """
        # Read and validate video
        video_bytes = await self.read_and_validate_media(video, allow_video=True)

        # Parse classes
        class_list = self.parse_classes(classes)

        # Extract frames
        frames, video_info = self.frame_service.extract_frames_by_interval(
            video_bytes=video_bytes,
            frame_interval=frame_interval,
            max_frames=max_frames,
            include_base64=True,
            jpeg_quality=85
        )

        logger.info(f"Extracted {len(frames)} frames, running detection on each")

        # Run detection on each frame
        results = []
        for frame_data in frames:
            # Run detection
            detection_result = await self.yolo_service.detect(
                image_bytes=frame_data.frame_bytes,
                confidence=confidence,
                classes=class_list
            )

            # Build result for this frame
            results.append({
                "frame_index": frame_data.frame_index,
                "timestamp": round(frame_data.timestamp, 2),
                "frame_base64": frame_data.frame_base64,
                "detections": detection_result.get("detections", []),
                "image_shape": detection_result.get("image_shape", []),
                "count": detection_result.get("count", 0)
            })

            logger.info(
                f"Frame {frame_data.frame_index} ({frame_data.timestamp:.2f}s): "
                f"{detection_result.get('count', 0)} detections"
            )

        # Calculate total detections
        total_detections = sum(f["count"] for f in results)

        logger.info(f"Processed {len(results)} frames, total {total_detections} detections")

        # Return results
        return {
            "status": "success",
            "video_info": {
                "total_frames": video_info.total_frames,
                "fps": video_info.fps,
                "duration": round(video_info.duration, 2),
                "width": video_info.width,
                "height": video_info.height
            },
            "frames": results,
            "total_frames_processed": len(results),
            "total_detections": total_detections
        }

    async def process_multiple_frames_segmentation(
        self,
        video: UploadFile,
        confidence: float,
        classes: Optional[str] = None,
        frame_interval: float = 2.0,
        max_frames: int = 10
    ) -> Dict:
        """
        Extract multiple frames from video and run segmentation on each

        Args:
            video: Uploaded video file
            confidence: Segmentation confidence threshold
            classes: Comma-separated class names (optional)
            frame_interval: Seconds between extracted frames
            max_frames: Maximum number of frames to extract

        Returns:
            Dict with array of frames with segmentations
        """
        # Read and validate video
        video_bytes = await self.read_and_validate_media(video, allow_video=True)

        # Parse classes
        class_list = self.parse_classes(classes)

        # Extract frames
        frames, video_info = self.frame_service.extract_frames_by_interval(
            video_bytes=video_bytes,
            frame_interval=frame_interval,
            max_frames=max_frames,
            include_base64=True,
            jpeg_quality=85
        )

        logger.info(f"Extracted {len(frames)} frames, running segmentation on each")

        # Run segmentation on each frame
        results = []
        for frame_data in frames:
            # Run segmentation
            segmentation_result = await self.yolo_service.segment(
                image_bytes=frame_data.frame_bytes,
                confidence=confidence,
                classes=class_list
            )

            # Build result for this frame
            results.append({
                "frame_index": frame_data.frame_index,
                "timestamp": round(frame_data.timestamp, 2),
                "frame_base64": frame_data.frame_base64,
                "segments": segmentation_result.get("segments", []),
                "image_shape": segmentation_result.get("image_shape", []),
                "count": segmentation_result.get("count", 0)
            })

            logger.info(
                f"Frame {frame_data.frame_index} ({frame_data.timestamp:.2f}s): "
                f"{segmentation_result.get('count', 0)} segments"
            )

        # Calculate total segments
        total_segments = sum(f["count"] for f in results)

        logger.info(f"Processed {len(results)} frames, total {total_segments} segments")

        # Return results
        return {
            "status": "success",
            "video_info": {
                "total_frames": video_info.total_frames,
                "fps": video_info.fps,
                "duration": round(video_info.duration, 2),
                "width": video_info.width,
                "height": video_info.height
            },
            "frames": results,
            "total_frames_processed": len(results),
            "total_segments": total_segments
        }

    async def process(self, *args, **kwargs):
        """
        Generic process method (required by base class)

        Video handler uses specific methods instead:
        - process_single_frame_detection()
        - process_multiple_frames_detection()
        - process_multiple_frames_segmentation()
        """
        raise NotImplementedError(
            "VideoHandler uses specific processing methods. "
            "Use process_single_frame_detection(), process_multiple_frames_detection(), "
            "or process_multiple_frames_segmentation() instead."
        )
