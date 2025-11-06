"""
Video processing utilities for frame extraction.
"""
import cv2
import numpy as np
import logging
from io import BytesIO
from typing import List, Tuple
from PIL import Image

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Service for processing video files and extracting frames."""

    def __init__(self, max_frames: int = 5):
        """
        Initialize the video processor.

        Args:
            max_frames: Maximum number of frames to extract from video
        """
        self.max_frames = max_frames

    async def extract_frames(
        self,
        video_data: bytes,
        num_frames: int = None
    ) -> List[bytes]:
        """
        Extract frames from video data.

        Extracts frames evenly distributed throughout the video duration.

        Args:
            video_data: Video file bytes
            num_frames: Number of frames to extract (defaults to max_frames)

        Returns:
            List of frame images as JPEG bytes

        Raises:
            ValueError: If video cannot be processed
        """
        if num_frames is None:
            num_frames = self.max_frames

        try:
            # Write video data to temporary buffer
            video_array = np.frombuffer(video_data, dtype=np.uint8)

            # Decode video
            temp_video_path = "/tmp/temp_video.mp4"
            with open(temp_video_path, "wb") as f:
                f.write(video_data)

            # Open video with OpenCV
            cap = cv2.VideoCapture(temp_video_path)

            if not cap.isOpened():
                raise ValueError("Failed to open video file")

            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0

            logger.info(f"Video info: {total_frames} frames, {fps} fps, {duration:.2f}s duration")

            if total_frames == 0:
                raise ValueError("Video has no frames")

            # Calculate frame indices to extract (evenly distributed)
            frame_indices = self._get_frame_indices(total_frames, num_frames)

            frames = []
            for idx in frame_indices:
                # Set frame position
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)

                # Read frame
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"Failed to read frame at index {idx}")
                    continue

                # Convert BGR to RGB (OpenCV uses BGR)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Convert to PIL Image
                pil_image = Image.fromarray(frame_rgb)

                # Resize if too large (max 1920x1080)
                pil_image = self._resize_if_needed(pil_image)

                # Convert to JPEG bytes
                img_byte_arr = BytesIO()
                pil_image.save(img_byte_arr, format='JPEG', quality=85)
                frame_bytes = img_byte_arr.getvalue()

                frames.append(frame_bytes)
                logger.info(f"Extracted frame {idx}/{total_frames} ({len(frame_bytes)} bytes)")

            cap.release()

            if not frames:
                raise ValueError("No frames could be extracted from video")

            logger.info(f"Successfully extracted {len(frames)} frames from video")
            return frames

        except Exception as e:
            logger.error(f"Error extracting frames from video: {e}", exc_info=True)
            raise ValueError(f"Failed to process video: {str(e)}")

    def _get_frame_indices(self, total_frames: int, num_frames: int) -> List[int]:
        """
        Calculate evenly distributed frame indices.

        Args:
            total_frames: Total number of frames in video
            num_frames: Number of frames to extract

        Returns:
            List of frame indices
        """
        if num_frames >= total_frames:
            return list(range(total_frames))

        # Calculate step size for even distribution
        step = total_frames / num_frames
        indices = [int(i * step) for i in range(num_frames)]

        return indices

    def _resize_if_needed(self, image: Image.Image, max_size: Tuple[int, int] = (1920, 1080)) -> Image.Image:
        """
        Resize image if it exceeds max dimensions while maintaining aspect ratio.

        Args:
            image: PIL Image
            max_size: Maximum (width, height)

        Returns:
            Resized PIL Image
        """
        if image.width <= max_size[0] and image.height <= max_size[1]:
            return image

        # Calculate new size maintaining aspect ratio
        ratio = min(max_size[0] / image.width, max_size[1] / image.height)
        new_size = (int(image.width * ratio), int(image.height * ratio))

        return image.resize(new_size, Image.Resampling.LANCZOS)


# Global instance
video_processor = VideoProcessor(max_frames=5)
