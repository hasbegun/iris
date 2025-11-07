"""
Video frame extraction service

Handles extraction of frames from video files for processing.
Consolidates video handling logic used across multiple endpoints.
"""
import cv2
import numpy as np
import tempfile
import os
import base64
import logging
from io import BytesIO
from PIL import Image
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class VideoInfo:
    """Video metadata"""
    total_frames: int
    fps: float
    duration: float
    width: int
    height: int


@dataclass
class FrameData:
    """Data for an extracted frame"""
    frame_bytes: bytes
    frame_index: int
    timestamp: float
    frame_base64: Optional[str] = None


class VideoFrameService:
    """
    Service for extracting frames from video files

    Provides methods for:
    - Getting video metadata
    - Extracting single frames
    - Extracting multiple frames at intervals
    - Converting frames to various formats
    """

    def __init__(self):
        """Initialize video frame service"""
        pass

    @staticmethod
    def _write_video_to_temp(video_bytes: bytes, suffix: str = '.mp4') -> str:
        """
        Write video bytes to a temporary file

        Args:
            video_bytes: Raw video data
            suffix: File extension for temp file

        Returns:
            Path to temporary file
        """
        fd, temp_path = tempfile.mkstemp(suffix=suffix)
        try:
            os.write(fd, video_bytes)
        finally:
            os.close(fd)
        return temp_path

    @staticmethod
    def _frame_to_jpeg_bytes(frame: np.ndarray, quality: int = 85) -> bytes:
        """
        Convert OpenCV frame (BGR) to JPEG bytes

        Args:
            frame: OpenCV frame array (BGR format)
            quality: JPEG quality (1-100)

        Returns:
            JPEG image as bytes
        """
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)

        # Convert to JPEG bytes
        img_byte_arr = BytesIO()
        pil_image.save(img_byte_arr, format='JPEG', quality=quality)
        return img_byte_arr.getvalue()

    @staticmethod
    def encode_bytes_to_base64(data: bytes) -> str:
        """
        Encode bytes to base64 string

        Args:
            data: Bytes to encode

        Returns:
            Base64-encoded string
        """
        return base64.b64encode(data).decode('utf-8')

    def get_video_info(self, video_bytes: bytes) -> VideoInfo:
        """
        Get metadata about a video

        Args:
            video_bytes: Raw video data

        Returns:
            VideoInfo object with metadata

        Raises:
            ValueError: If video cannot be opened or read
        """
        temp_path = self._write_video_to_temp(video_bytes)

        try:
            cap = cv2.VideoCapture(temp_path)
            if not cap.isOpened():
                raise ValueError("Failed to open video file")

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = total_frames / fps if fps > 0 else 0

            cap.release()

            return VideoInfo(
                total_frames=total_frames,
                fps=fps,
                duration=duration,
                width=width,
                height=height
            )

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def extract_single_frame(
        self,
        video_bytes: bytes,
        frame_index: Optional[int] = None,
        include_base64: bool = False,
        jpeg_quality: int = 85
    ) -> FrameData:
        """
        Extract a single frame from video

        Args:
            video_bytes: Raw video data
            frame_index: Frame index to extract (None = middle frame)
            include_base64: Whether to include base64-encoded image
            jpeg_quality: JPEG compression quality (1-100)

        Returns:
            FrameData object

        Raises:
            ValueError: If video cannot be opened or frame cannot be extracted
        """
        temp_path = self._write_video_to_temp(video_bytes)

        try:
            cap = cv2.VideoCapture(temp_path)
            if not cap.isOpened():
                raise ValueError("Failed to open video file")

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            # Use middle frame if not specified
            if frame_index is None:
                frame_index = total_frames // 2

            # Validate frame index
            if frame_index < 0 or frame_index >= total_frames:
                raise ValueError(f"Frame index {frame_index} out of range (0-{total_frames-1})")

            # Seek to frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ret, frame = cap.read()
            cap.release()

            if not ret:
                raise ValueError(f"Failed to extract frame {frame_index}")

            # Convert to JPEG bytes
            frame_bytes = self._frame_to_jpeg_bytes(frame, quality=jpeg_quality)

            # Calculate timestamp
            timestamp = frame_index / fps if fps > 0 else 0

            # Optionally encode to base64
            frame_base64 = None
            if include_base64:
                frame_base64 = self.encode_bytes_to_base64(frame_bytes)

            return FrameData(
                frame_bytes=frame_bytes,
                frame_index=frame_index,
                timestamp=timestamp,
                frame_base64=frame_base64
            )

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def extract_frames_by_interval(
        self,
        video_bytes: bytes,
        frame_interval: float = 2.0,
        max_frames: int = 10,
        include_base64: bool = False,
        jpeg_quality: int = 85
    ) -> Tuple[List[FrameData], VideoInfo]:
        """
        Extract multiple frames from video at regular time intervals

        Args:
            video_bytes: Raw video data
            frame_interval: Seconds between extracted frames
            max_frames: Maximum number of frames to extract
            include_base64: Whether to include base64-encoded images
            jpeg_quality: JPEG compression quality (1-100)

        Returns:
            Tuple of (list of FrameData objects, VideoInfo)

        Raises:
            ValueError: If video cannot be opened
        """
        temp_path = self._write_video_to_temp(video_bytes)

        try:
            cap = cv2.VideoCapture(temp_path)
            if not cap.isOpened():
                raise ValueError("Failed to open video file")

            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = total_frames / fps if fps > 0 else 0

            video_info = VideoInfo(
                total_frames=total_frames,
                fps=fps,
                duration=duration,
                width=width,
                height=height
            )

            logger.info(f"Video: {total_frames} frames, {fps:.2f} FPS, {duration:.2f}s duration")

            # Calculate frame indices to extract
            frames_to_extract = []
            current_time = 0.0

            while current_time < duration and len(frames_to_extract) < max_frames:
                frame_index = int(current_time * fps)
                if frame_index < total_frames:
                    frames_to_extract.append({
                        'index': frame_index,
                        'timestamp': current_time
                    })
                current_time += frame_interval

            logger.info(f"Extracting {len(frames_to_extract)} frames from video")

            # Extract frames
            extracted_frames = []

            for frame_info in frames_to_extract:
                frame_idx = frame_info['index']
                timestamp = frame_info['timestamp']

                # Seek to frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()

                if not ret:
                    logger.warning(f"Failed to extract frame {frame_idx}, skipping")
                    continue

                # Convert to JPEG bytes
                frame_bytes = self._frame_to_jpeg_bytes(frame, quality=jpeg_quality)

                # Optionally encode to base64
                frame_base64 = None
                if include_base64:
                    frame_base64 = self.encode_bytes_to_base64(frame_bytes)

                extracted_frames.append(FrameData(
                    frame_bytes=frame_bytes,
                    frame_index=frame_idx,
                    timestamp=timestamp,
                    frame_base64=frame_base64
                ))

            cap.release()

            logger.info(f"Successfully extracted {len(extracted_frames)} frames")

            return extracted_frames, video_info

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def extract_frames_by_indices(
        self,
        video_bytes: bytes,
        frame_indices: List[int],
        include_base64: bool = False,
        jpeg_quality: int = 85
    ) -> List[FrameData]:
        """
        Extract specific frames by their indices

        Args:
            video_bytes: Raw video data
            frame_indices: List of frame indices to extract
            include_base64: Whether to include base64-encoded images
            jpeg_quality: JPEG compression quality (1-100)

        Returns:
            List of FrameData objects

        Raises:
            ValueError: If video cannot be opened
        """
        temp_path = self._write_video_to_temp(video_bytes)

        try:
            cap = cv2.VideoCapture(temp_path)
            if not cap.isOpened():
                raise ValueError("Failed to open video file")

            fps = cap.get(cv2.CAP_PROP_FPS)
            extracted_frames = []

            for frame_idx in frame_indices:
                # Seek to frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()

                if not ret:
                    logger.warning(f"Failed to extract frame {frame_idx}, skipping")
                    continue

                # Convert to JPEG bytes
                frame_bytes = self._frame_to_jpeg_bytes(frame, quality=jpeg_quality)

                # Calculate timestamp
                timestamp = frame_idx / fps if fps > 0 else 0

                # Optionally encode to base64
                frame_base64 = None
                if include_base64:
                    frame_base64 = self.encode_bytes_to_base64(frame_bytes)

                extracted_frames.append(FrameData(
                    frame_bytes=frame_bytes,
                    frame_index=frame_idx,
                    timestamp=timestamp,
                    frame_base64=frame_base64
                ))

            cap.release()

            return extracted_frames

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
