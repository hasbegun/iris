"""
ML Service Client
HTTP client for communicating with the ML microservice (YOLO)
"""
import aiohttp
from typing import Optional, List, Dict
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class MLServiceClient:
    """
    Client for ML microservice communication
    Handles object detection, segmentation, and face detection requests
    """

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize ML service client

        Args:
            base_url: ML service base URL (defaults to settings)
        """
        self.base_url = base_url or settings.ml_service_url
        self.timeout = aiohttp.ClientTimeout(total=settings.ml_service_timeout)
        logger.info(f"MLServiceClient initialized with base URL: {self.base_url}")

    async def health_check(self) -> Dict:
        """
        Check if ML service is healthy

        Returns:
            Health status dictionary

        Raises:
            Exception if service is unavailable
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/health") as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logger.error(f"ML service health check failed: {e}")
            raise Exception(f"ML service unavailable: {e}")

    async def detect_objects(
        self,
        image_bytes: bytes,
        confidence: float = 0.5,
        classes: Optional[List[str]] = None
    ) -> Dict:
        """
        Detect objects in an image

        Args:
            image_bytes: Image data as bytes
            confidence: Detection confidence threshold (0.0-1.0)
            classes: Optional list of class names to detect

        Returns:
            Detection results dictionary

        Raises:
            Exception if detection fails
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Prepare form data
                form_data = aiohttp.FormData()
                form_data.add_field('image', image_bytes, filename='image.jpg', content_type='image/jpeg')
                form_data.add_field('confidence', str(confidence))

                if classes:
                    form_data.add_field('classes', ','.join(classes))

                # Make request
                async with session.post(
                    f"{self.base_url}/api/detect",
                    data=form_data
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    logger.info(f"Detected {result.get('count', 0)} objects")
                    return result

        except aiohttp.ClientError as e:
            logger.error(f"Object detection failed: {e}")
            raise Exception(f"Object detection failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in object detection: {e}")
            raise

    async def segment_objects(
        self,
        image_bytes: bytes,
        confidence: float = 0.5,
        classes: Optional[List[str]] = None
    ) -> Dict:
        """
        Perform instance segmentation on an image

        Args:
            image_bytes: Image data as bytes
            confidence: Segmentation confidence threshold (0.0-1.0)
            classes: Optional list of class names to segment

        Returns:
            Segmentation results dictionary

        Raises:
            Exception if segmentation fails
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Prepare form data
                form_data = aiohttp.FormData()
                form_data.add_field('image', image_bytes, filename='image.jpg', content_type='image/jpeg')
                form_data.add_field('confidence', str(confidence))

                if classes:
                    form_data.add_field('classes', ','.join(classes))

                # Make request
                async with session.post(
                    f"{self.base_url}/api/segment",
                    data=form_data
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    logger.info(f"Segmented {result.get('count', 0)} objects")
                    return result

        except aiohttp.ClientError as e:
            logger.error(f"Segmentation failed: {e}")
            raise Exception(f"Segmentation failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in segmentation: {e}")
            raise

    async def detect_faces(
        self,
        image_bytes: bytes,
        confidence: float = 0.5
    ) -> Dict:
        """
        Detect faces in an image

        Args:
            image_bytes: Image data as bytes
            confidence: Detection confidence threshold (0.0-1.0)

        Returns:
            Face detection results dictionary

        Raises:
            Exception if face detection fails
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Prepare form data
                form_data = aiohttp.FormData()
                form_data.add_field('image', image_bytes, filename='image.jpg', content_type='image/jpeg')
                form_data.add_field('confidence', str(confidence))

                # Make request
                async with session.post(
                    f"{self.base_url}/api/detect-faces",
                    data=form_data
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    logger.info(f"Detected {result.get('count', 0)} face(s)")
                    return result

        except aiohttp.ClientError as e:
            logger.error(f"Face detection failed: {e}")
            raise Exception(f"Face detection failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in face detection: {e}")
            raise

    async def detect_video_frame(
        self,
        video_bytes: bytes,
        confidence: float = 0.5,
        classes: Optional[List[str]] = None
    ) -> Dict:
        """
        Extract a frame from video and detect objects in it.
        Returns frame image + detections (for frontend display).

        Args:
            video_bytes: Video data as bytes
            confidence: Detection confidence threshold (0.0-1.0)
            classes: Optional list of class names to detect

        Returns:
            Dictionary with:
            - frame_base64: Extracted frame as base64 JPEG
            - detections: List of detected objects
            - image_shape: Frame dimensions
            - frame_index: Which frame was extracted

        Raises:
            Exception if detection fails
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Prepare form data
                form_data = aiohttp.FormData()
                form_data.add_field('video', video_bytes, filename='video.mp4', content_type='video/mp4')
                form_data.add_field('confidence', str(confidence))

                if classes:
                    form_data.add_field('classes', ','.join(classes))

                # Make request to video frame detection endpoint
                async with session.post(
                    f"{self.base_url}/api/detect-video-frame",
                    data=form_data
                ) as response:
                    response.raise_for_status()
                    result = await response.json()

                    count = result.get('count', 0)
                    frame_index = result.get('frame_index', 0)
                    logger.info(f"Detected {count} objects in video frame {frame_index}")

                    return result

        except aiohttp.ClientError as e:
            logger.error(f"Video frame detection failed: {e}")
            raise Exception(f"Video frame detection failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in video frame detection: {e}")
            raise

    async def detect_video_frames(
        self,
        video_bytes: bytes,
        confidence: float = 0.5,
        classes: Optional[List[str]] = None,
        frame_interval: float = 2.0,
        max_frames: int = 10
    ) -> Dict:
        """
        Extract multiple frames from video and detect objects in each.
        Returns array of frames with detection data for slideshow display.

        Args:
            video_bytes: Video data as bytes
            confidence: Detection confidence threshold (0.0-1.0)
            classes: Optional list of class names to detect
            frame_interval: Seconds between extracted frames
            max_frames: Maximum number of frames to extract

        Returns:
            Dictionary with:
            - frames: Array of frame data (frame_base64, detections, timestamp)
            - total_frames_in_video: Total frames in video
            - frames_analyzed: Number of frames extracted
            - total_detections: Total detections across all frames

        Raises:
            Exception if detection fails
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Prepare form data
                form_data = aiohttp.FormData()
                form_data.add_field('video', video_bytes, filename='video.mp4', content_type='video/mp4')
                form_data.add_field('confidence', str(confidence))
                form_data.add_field('frame_interval', str(frame_interval))
                form_data.add_field('max_frames', str(max_frames))

                if classes:
                    form_data.add_field('classes', ','.join(classes))

                # Make request to video frames detection endpoint
                async with session.post(
                    f"{self.base_url}/api/detect-video-frames",
                    data=form_data
                ) as response:
                    response.raise_for_status()
                    result = await response.json()

                    frames_analyzed = result.get('frames_analyzed', 0)
                    total_detections = result.get('total_detections', 0)
                    logger.info(f"Extracted {frames_analyzed} frames with {total_detections} total detections")

                    return result

        except aiohttp.ClientError as e:
            logger.error(f"Video frames detection failed: {e}")
            raise Exception(f"Video frames detection failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in video frames detection: {e}")
            raise

    async def segment_video_frames(
        self,
        video_bytes: bytes,
        confidence: float = 0.5,
        classes: Optional[List[str]] = None,
        frame_interval: float = 2.0,
        max_frames: int = 10
    ) -> Dict:
        """
        Extract multiple frames from video and segment objects in each.
        Returns array of frames with segmentation data (polygon masks) for slideshow display.

        Args:
            video_bytes: Video data as bytes
            confidence: Segmentation confidence threshold (0.0-1.0)
            classes: Optional list of class names to segment
            frame_interval: Seconds between extracted frames
            max_frames: Maximum number of frames to extract

        Returns:
            Dictionary with:
            - frames: Array of frame data (frame_base64, segments, timestamp)
            - total_frames_in_video: Total frames in video
            - frames_analyzed: Number of frames extracted
            - total_segments: Total segments across all frames

        Raises:
            Exception if segmentation fails
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Prepare form data
                form_data = aiohttp.FormData()
                form_data.add_field('video', video_bytes, filename='video.mp4', content_type='video/mp4')
                form_data.add_field('confidence', str(confidence))
                form_data.add_field('frame_interval', str(frame_interval))
                form_data.add_field('max_frames', str(max_frames))

                if classes:
                    form_data.add_field('classes', ','.join(classes))

                # Make request to video frames segmentation endpoint
                async with session.post(
                    f"{self.base_url}/api/segment-video-frames",
                    data=form_data
                ) as response:
                    response.raise_for_status()
                    result = await response.json()

                    frames_analyzed = result.get('frames_analyzed', 0)
                    total_segments = result.get('total_segments', 0)
                    logger.info(f"Extracted {frames_analyzed} frames with {total_segments} total segments")

                    return result

        except aiohttp.ClientError as e:
            logger.error(f"Video frames segmentation failed: {e}")
            raise Exception(f"Video frames segmentation failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in video frames segmentation: {e}")
            raise

    async def detect_objects_in_video(
        self,
        video_bytes: bytes,
        confidence: float = 0.5,
        classes: Optional[List[str]] = None,
        frame_skip: int = 2
    ) -> Dict:
        """
        Detect objects in a video using frame-by-frame YOLO detection

        Args:
            video_bytes: Video data as bytes
            confidence: Detection confidence threshold (0.0-1.0)
            classes: Optional list of class names to detect
            frame_skip: Number of frames to skip between detections (0 = process all frames)

        Returns:
            Video detection results dictionary with summary and frame detections

        Raises:
            Exception if detection fails
        """
        try:
            # Use longer timeout for video processing
            video_timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes

            async with aiohttp.ClientSession(timeout=video_timeout) as session:
                # Prepare form data
                form_data = aiohttp.FormData()
                form_data.add_field('video', video_bytes, filename='video.mp4', content_type='video/mp4')
                form_data.add_field('confidence', str(confidence))
                form_data.add_field('frame_skip', str(frame_skip))

                if classes:
                    form_data.add_field('classes', ','.join(classes))

                # Make request to video detection endpoint
                async with session.post(
                    f"{self.base_url}/api/detect-video",
                    data=form_data
                ) as response:
                    response.raise_for_status()
                    result = await response.json()

                    summary = result.get('summary', {})
                    total_detections = summary.get('total_detections', 0)
                    logger.info(f"Detected {total_detections} objects in video")

                    return result

        except aiohttp.ClientError as e:
            logger.error(f"Video detection failed: {e}")
            return {
                "status": "error",
                "message": f"Video detection failed: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error in video detection: {e}")
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}"
            }

    async def detect_stream(
        self,
        image_bytes: bytes,
        confidence: float = 0.5,
        classes: Optional[List[str]] = None
    ) -> Dict:
        """
        Real-time object detection for camera streams (optimized for low latency)

        Args:
            image_bytes: Camera frame data as bytes
            confidence: Detection confidence threshold (0.0-1.0)
            classes: Optional list of object classes to detect

        Returns:
            Detection results dictionary

        Raises:
            Exception if detection fails
        """
        try:
            # Create shorter timeout for streaming (5 seconds max)
            stream_timeout = aiohttp.ClientTimeout(total=5)

            async with aiohttp.ClientSession(timeout=stream_timeout) as session:
                # Prepare form data
                data = aiohttp.FormData()
                data.add_field('image', image_bytes, filename='frame.jpg', content_type='image/jpeg')
                data.add_field('confidence', str(confidence))

                if classes:
                    data.add_field('classes', ','.join(classes))

                # Send request
                async with session.post(f"{self.base_url}/api/detect-stream", data=data) as response:
                    response.raise_for_status()
                    result = await response.json()

                    detections_count = len(result.get('detections', []))
                    inference_time = result.get('inference_time', 0)
                    logger.debug(f"Stream: {detections_count} objects detected in {inference_time:.3f}s")

                    return result

        except aiohttp.ClientError as e:
            logger.error(f"Stream detection failed: {e}")
            raise Exception(f"Stream detection failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in stream detection: {e}")
            raise Exception(f"Unexpected error: {str(e)}")

    async def segment_stream(
        self,
        image_bytes: bytes,
        confidence: float = 0.5,
        classes: Optional[List[str]] = None
    ) -> Dict:
        """
        Real-time instance segmentation for camera streams (optimized for low latency)

        Args:
            image_bytes: Camera frame data as bytes
            confidence: Segmentation confidence threshold (0.0-1.0)
            classes: Optional list of object classes to segment

        Returns:
            Segmentation results dictionary with polygon masks

        Raises:
            Exception if segmentation fails
        """
        try:
            # Create shorter timeout for streaming (5 seconds max)
            stream_timeout = aiohttp.ClientTimeout(total=5)

            async with aiohttp.ClientSession(timeout=stream_timeout) as session:
                # Prepare form data
                data = aiohttp.FormData()
                data.add_field('image', image_bytes, filename='frame.jpg', content_type='image/jpeg')
                data.add_field('confidence', str(confidence))

                if classes:
                    data.add_field('classes', ','.join(classes))

                # Send request
                async with session.post(f"{self.base_url}/api/segment-stream", data=data) as response:
                    response.raise_for_status()
                    result = await response.json()

                    segments_count = len(result.get('segments', []))
                    inference_time = result.get('inference_time', 0)
                    logger.debug(f"SegmentStream: {segments_count} objects segmented in {inference_time:.3f}s")

                    return result

        except aiohttp.ClientError as e:
            logger.error(f"Stream segmentation failed: {e}")
            raise Exception(f"Stream segmentation failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in stream segmentation: {e}")
            raise Exception(f"Unexpected error: {str(e)}")

    async def get_metrics(self) -> Dict:
        """
        Get ML service metrics

        Returns:
            Metrics dictionary

        Raises:
            Exception if request fails
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/metrics") as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logger.error(f"Failed to get ML service metrics: {e}")
            raise Exception(f"Failed to get ML service metrics: {e}")


# Global instance for reuse
ml_client = MLServiceClient()
