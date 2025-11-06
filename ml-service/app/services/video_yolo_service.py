"""
Video YOLO Service for frame-by-frame object detection in videos
Processes videos with YOLO and returns detection data per frame
"""
import asyncio
import time
import logging
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Dict, Tuple
from collections import defaultdict
import numpy as np

from app.models.schemas import Detection, FrameDetection, VideoInfo, VideoDetectionResponse

# Lazy imports to avoid issues if packages not installed
try:
    import cv2
    from ultralytics import YOLO
    import torch
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logging.warning("OpenCV or Ultralytics not installed. Video features will be disabled.")

logger = logging.getLogger(__name__)


class VideoYOLOService:
    """
    Video YOLO inference service
    Processes videos frame-by-frame and returns detection data
    """

    def __init__(self, yolo_service):
        """
        Initialize video YOLO service

        Args:
            yolo_service: YOLOService instance (for accessing models)
        """
        if not CV2_AVAILABLE:
            raise ImportError(
                "OpenCV is required for video processing. "
                "Please install it with: pip install opencv-python"
            )

        self.yolo_service = yolo_service
        self.executor = ThreadPoolExecutor(max_workers=2)
        logger.info("VideoYOLOService initialized")

    async def detect_objects_in_video(
        self,
        video_bytes: bytes,
        confidence: float = 0.5,
        classes: Optional[List[str]] = None,
        frame_skip: int = 0
    ) -> Dict:
        """
        Detect objects in video frame-by-frame

        Args:
            video_bytes: Video data as bytes
            confidence: Detection confidence threshold (0.0-1.0)
            classes: List of class names to detect (None = all classes)
            frame_skip: Skip N frames between detections (0 = process all frames)

        Returns:
            Dictionary with video info, frame detections, and summary
        """
        start_time = time.time()

        # Write video to temporary file
        temp_video_path = None
        try:
            temp_video_path = await self._write_temp_video(video_bytes)

            # Load video and get metadata
            video_info = await self._get_video_info(temp_video_path)
            logger.info(
                f"Processing video: {video_info['total_frames']} frames, "
                f"{video_info['fps']:.2f} FPS, {video_info['duration_seconds']:.2f}s"
            )

            # Process video frames
            frame_detections = await self._process_video_frames(
                temp_video_path,
                confidence,
                classes,
                frame_skip,
                video_info
            )

            # Calculate processing time
            processing_time = time.time() - start_time

            # Generate summary
            summary = self._generate_summary(frame_detections, video_info)

            # Calculate average processing FPS
            frames_processed = len(frame_detections)
            avg_fps = frames_processed / processing_time if processing_time > 0 else 0

            logger.info(
                f"Video processing complete: {frames_processed} frames in "
                f"{processing_time:.2f}s ({avg_fps:.2f} FPS)"
            )

            return {
                "status": "success",
                "video_info": video_info,
                "frame_detections": frame_detections,
                "summary": summary,
                "processing_time_seconds": round(processing_time, 2),
                "avg_fps": round(avg_fps, 2)
            }

        except Exception as e:
            logger.error(f"Error processing video: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to process video: {str(e)}"
            }
        finally:
            # Clean up temporary file
            if temp_video_path and os.path.exists(temp_video_path):
                try:
                    os.remove(temp_video_path)
                except Exception as e:
                    logger.warning(f"Failed to remove temp video file: {e}")

    async def _write_temp_video(self, video_bytes: bytes) -> str:
        """
        Write video bytes to temporary file

        Args:
            video_bytes: Video data

        Returns:
            Path to temporary file
        """
        loop = asyncio.get_event_loop()

        def _write():
            # Create temporary file
            fd, path = tempfile.mkstemp(suffix='.mp4')
            try:
                os.write(fd, video_bytes)
            finally:
                os.close(fd)
            return path

        return await loop.run_in_executor(self.executor, _write)

    async def _get_video_info(self, video_path: str) -> Dict:
        """
        Extract video metadata

        Args:
            video_path: Path to video file

        Returns:
            Dictionary with video info
        """
        loop = asyncio.get_event_loop()

        def _extract_info():
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError("Failed to open video file")

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = total_frames / fps if fps > 0 else 0

            cap.release()

            return {
                "total_frames": total_frames,
                "fps": round(fps, 2),
                "duration_seconds": round(duration, 2),
                "resolution": (width, height)
            }

        return await loop.run_in_executor(self.executor, _extract_info)

    async def _process_video_frames(
        self,
        video_path: str,
        confidence: float,
        classes: Optional[List[str]],
        frame_skip: int,
        video_info: Dict
    ) -> List[Dict]:
        """
        Process video frames with YOLO detection

        Args:
            video_path: Path to video file
            confidence: Detection confidence threshold
            classes: List of class names to detect
            frame_skip: Number of frames to skip between detections
            video_info: Video metadata

        Returns:
            List of frame detection results
        """
        loop = asyncio.get_event_loop()
        frame_detections = []

        # Convert class names to IDs if needed
        class_ids = self.yolo_service._get_class_ids(classes) if classes else None

        def _process_frames():
            """Process frames in thread pool (CPU/GPU bound)"""
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError("Failed to open video file for processing")

            frame_results = []
            frame_number = 0
            fps = video_info["fps"]

            try:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    # Skip frames if configured
                    if frame_skip > 0 and frame_number % (frame_skip + 1) != 0:
                        frame_number += 1
                        continue

                    # Convert BGR to RGB (OpenCV uses BGR, YOLO expects RGB)
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    # Run YOLO detection on frame
                    results = self.yolo_service.detection_model.predict(
                        frame_rgb,
                        conf=confidence,
                        classes=class_ids,
                        verbose=False
                    )

                    # Parse detections
                    detections = self.yolo_service._parse_detection_results(results[0])

                    # Calculate timestamp
                    timestamp = frame_number / fps if fps > 0 else 0

                    # Store frame detection
                    frame_results.append({
                        "frame_number": frame_number,
                        "timestamp": round(timestamp, 3),
                        "detections": detections,
                        "count": len(detections)
                    })

                    frame_number += 1

                    # Log progress every 30 frames
                    if frame_number % 30 == 0:
                        logger.info(f"Processed {frame_number} frames...")

            finally:
                cap.release()

            return frame_results

        # Run frame processing in executor
        frame_detections = await loop.run_in_executor(
            self.executor,
            _process_frames
        )

        return frame_detections

    def _generate_summary(
        self,
        frame_detections: List[Dict],
        video_info: Dict
    ) -> Dict:
        """
        Generate summary statistics for video detections

        Args:
            frame_detections: List of frame detection results
            video_info: Video metadata

        Returns:
            Summary dictionary
        """
        # Count total detections
        total_detections = sum(fd["count"] for fd in frame_detections)

        # Count by class
        class_counts = defaultdict(int)
        for frame_det in frame_detections:
            for det in frame_det["detections"]:
                class_counts[det["class_name"]] += 1

        # Find frames with most detections
        frames_with_objects = [fd for fd in frame_detections if fd["count"] > 0]
        max_objects_frame = max(
            frames_with_objects,
            key=lambda x: x["count"]
        ) if frames_with_objects else None

        # Calculate statistics
        avg_objects_per_frame = (
            total_detections / len(frame_detections)
            if frame_detections else 0
        )

        return {
            "total_detections": total_detections,
            "unique_classes": list(class_counts.keys()),
            "detections_by_class": dict(class_counts),
            "frames_with_detections": len(frames_with_objects),
            "frames_without_detections": len(frame_detections) - len(frames_with_objects),
            "avg_detections_per_frame": round(avg_objects_per_frame, 2),
            "max_detections_in_frame": max_objects_frame["count"] if max_objects_frame else 0,
            "frame_with_most_objects": max_objects_frame["frame_number"] if max_objects_frame else None
        }

    async def segment_objects_in_video(
        self,
        video_bytes: bytes,
        confidence: float = 0.5,
        classes: Optional[List[str]] = None,
        frame_skip: int = 0
    ) -> Dict:
        """
        Segment objects in video frame-by-frame

        Args:
            video_bytes: Video data as bytes
            confidence: Segmentation confidence threshold (0.0-1.0)
            classes: List of class names to segment (None = all classes)
            frame_skip: Skip N frames between segmentations (0 = process all frames)

        Returns:
            Dictionary with video info, frame segmentations, and summary
        """
        start_time = time.time()

        # Write video to temporary file
        temp_video_path = None
        try:
            temp_video_path = await self._write_temp_video(video_bytes)

            # Load video and get metadata
            video_info = await self._get_video_info(temp_video_path)
            logger.info(
                f"Processing video for segmentation: {video_info['total_frames']} frames, "
                f"{video_info['fps']:.2f} FPS, {video_info['duration_seconds']:.2f}s"
            )

            # Process video frames with segmentation
            frame_segmentations = await self._process_video_frames_segmentation(
                temp_video_path,
                confidence,
                classes,
                frame_skip,
                video_info
            )

            # Calculate processing time
            processing_time = time.time() - start_time

            # Generate summary (reuse existing summary method, works for segments too)
            summary = self._generate_summary(frame_segmentations, video_info)

            # Calculate average processing FPS
            frames_processed = len(frame_segmentations)
            avg_fps = frames_processed / processing_time if processing_time > 0 else 0

            logger.info(
                f"Video segmentation complete: {frames_processed} frames in "
                f"{processing_time:.2f}s ({avg_fps:.2f} FPS)"
            )

            return {
                "status": "success",
                "video_info": video_info,
                "frame_segmentations": frame_segmentations,
                "summary": summary,
                "processing_time_seconds": round(processing_time, 2),
                "avg_fps": round(avg_fps, 2)
            }

        except Exception as e:
            logger.error(f"Error segmenting video: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to segment video: {str(e)}"
            }
        finally:
            # Clean up temporary file
            if temp_video_path and os.path.exists(temp_video_path):
                try:
                    os.remove(temp_video_path)
                except Exception as e:
                    logger.warning(f"Failed to remove temp video file: {e}")

    async def _process_video_frames_segmentation(
        self,
        video_path: str,
        confidence: float,
        classes: Optional[List[str]],
        frame_skip: int,
        video_info: Dict
    ) -> List[Dict]:
        """
        Process video frames with YOLO segmentation

        Args:
            video_path: Path to video file
            confidence: Segmentation confidence threshold
            classes: List of class names to segment
            frame_skip: Number of frames to skip between segmentations
            video_info: Video metadata

        Returns:
            List of frame segmentation results
        """
        loop = asyncio.get_event_loop()
        frame_segmentations = []

        # Convert class names to IDs if needed
        class_ids = self.yolo_service._get_class_ids(classes) if classes else None

        def _process_frames():
            """Process frames with segmentation in thread pool (CPU/GPU bound)"""
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError("Failed to open video file for segmentation")

            frame_results = []
            frame_number = 0
            fps = video_info["fps"]

            try:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    # Skip frames if configured
                    if frame_skip > 0 and frame_number % (frame_skip + 1) != 0:
                        frame_number += 1
                        continue

                    # Convert BGR to RGB (OpenCV uses BGR, YOLO expects RGB)
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    # Run YOLO segmentation on frame
                    results = self.yolo_service.segmentation_model.predict(
                        frame_rgb,
                        conf=confidence,
                        classes=class_ids,
                        verbose=False
                    )

                    # Parse segmentations
                    segments = self.yolo_service._parse_segmentation_results(results[0])

                    # Calculate timestamp
                    timestamp = frame_number / fps if fps > 0 else 0

                    # Store frame segmentation (using "detections" key for compatibility with summary)
                    frame_results.append({
                        "frame_number": frame_number,
                        "timestamp": round(timestamp, 3),
                        "segments": segments,
                        "detections": segments,  # For summary compatibility
                        "count": len(segments)
                    })

                    frame_number += 1

                    # Log progress every 30 frames
                    if frame_number % 30 == 0:
                        logger.info(f"Segmented {frame_number} frames...")

            finally:
                cap.release()

            return frame_results

        # Run frame processing in executor
        frame_segmentations = await loop.run_in_executor(
            self.executor,
            _process_frames
        )

        return frame_segmentations

    async def detect_faces_in_video(
        self,
        video_bytes: bytes,
        confidence: float = 0.5,
        frame_skip: int = 0
    ) -> Dict:
        """
        Detect faces in video frame-by-frame

        Args:
            video_bytes: Video data as bytes
            confidence: Detection confidence threshold
            frame_skip: Skip N frames between detections

        Returns:
            Dictionary with video info, frame detections, and summary
        """
        # Use person class (class ID 0 in COCO) for face detection
        # If dedicated face model is available, it will be used by the service
        return await self.detect_objects_in_video(
            video_bytes=video_bytes,
            confidence=confidence,
            classes=["person"] if self.yolo_service.face_model == self.yolo_service.detection_model else None,
            frame_skip=frame_skip
        )

    async def segment_objects_in_video(
        self,
        video_bytes: bytes,
        confidence: float = 0.5,
        frame_skip: int = 0
    ) -> Dict:
        """
        Segment objects in video frame-by-frame

        Args:
            video_bytes: Video data as bytes
            confidence: Segmentation confidence threshold
            frame_skip: Skip N frames between detections

        Returns:
            Dictionary with video info, frame segmentations, and summary
        """
        # Similar to detect_objects_in_video but uses segmentation model
        # For now, we'll return a not implemented response
        # This can be implemented later following the same pattern
        return {
            "status": "error",
            "message": "Video segmentation not yet implemented. Use detect_objects_in_video instead."
        }

    async def detect_and_annotate_video(
        self,
        video_bytes: bytes,
        confidence: float = 0.5,
        classes: Optional[List[str]] = None,
        frame_skip: int = 0,
        line_width: int = 2,
        font_scale: float = 0.6,
        progress_callback: Optional[callable] = None
    ) -> Tuple[bytes, Dict]:
        """
        Detect objects in video and return annotated video with bounding boxes

        Args:
            video_bytes: Video data as bytes
            confidence: Detection confidence threshold
            classes: List of class names to detect
            frame_skip: Skip N frames between detections
            line_width: Width of bounding box lines
            font_scale: Font scale for labels

        Returns:
            Tuple of (annotated_video_bytes, detection_summary)
        """
        start_time = time.time()

        # Write video to temporary file
        temp_input_path = None
        temp_output_path = None

        try:
            temp_input_path = await self._write_temp_video(video_bytes)

            # Load video and get metadata
            video_info = await self._get_video_info(temp_input_path)
            logger.info(
                f"Processing video for annotation: {video_info['total_frames']} frames, "
                f"{video_info['fps']:.2f} FPS"
            )

            # Create output video path
            import tempfile
            fd, temp_output_path = tempfile.mkstemp(suffix='.mp4')
            os.close(fd)

            # Process and annotate video
            detection_stats = await self._process_and_annotate_video(
                temp_input_path,
                temp_output_path,
                confidence,
                classes,
                frame_skip,
                video_info,
                line_width,
                font_scale,
                progress_callback
            )

            # Read output video
            with open(temp_output_path, 'rb') as f:
                output_video_bytes = f.read()

            processing_time = time.time() - start_time

            # Add processing info to stats
            detection_stats['processing_time_seconds'] = round(processing_time, 2)
            detection_stats['video_info'] = video_info

            logger.info(f"Annotated video generated: {len(output_video_bytes) / (1024*1024):.2f} MB")

            return output_video_bytes, detection_stats

        except Exception as e:
            logger.error(f"Error annotating video: {e}", exc_info=True)
            raise
        finally:
            # Clean up temporary files
            if temp_input_path and os.path.exists(temp_input_path):
                try:
                    os.remove(temp_input_path)
                except Exception as e:
                    logger.warning(f"Failed to remove temp input file: {e}")
            if temp_output_path and os.path.exists(temp_output_path):
                try:
                    os.remove(temp_output_path)
                except Exception as e:
                    logger.warning(f"Failed to remove temp output file: {e}")

    async def _process_and_annotate_video(
        self,
        input_path: str,
        output_path: str,
        confidence: float,
        classes: Optional[List[str]],
        frame_skip: int,
        video_info: Dict,
        line_width: int,
        font_scale: float,
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """
        Process video frames, detect objects, and write annotated video

        Args:
            input_path: Path to input video
            output_path: Path to output video
            confidence: Detection confidence
            classes: Class names to detect
            frame_skip: Frame skip value
            video_info: Video metadata
            line_width: Bounding box line width
            font_scale: Label font scale

        Returns:
            Detection statistics dictionary
        """
        loop = asyncio.get_event_loop()
        class_ids = self.yolo_service._get_class_ids(classes) if classes else None

        def _process():
            """Process and annotate frames in thread pool"""
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                raise ValueError("Failed to open input video")

            # Get video properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = video_info["fps"]

            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # MP4 codec
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

            if not out.isOpened():
                cap.release()
                raise ValueError("Failed to create output video writer")

            # Statistics
            total_detections = 0
            frames_with_detections = 0
            class_counts = defaultdict(int)
            frame_number = 0
            frames_processed = 0

            # Generate colors for classes (consistent across frames)
            np.random.seed(42)  # Consistent colors
            colors = {}

            try:
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    # Process every frame but only detect on non-skipped frames
                    should_detect = (frame_skip == 0) or (frame_number % (frame_skip + 1) == 0)

                    if should_detect:
                        # Convert BGR to RGB for YOLO
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                        # Run YOLO detection
                        results = self.yolo_service.detection_model.predict(
                            frame_rgb,
                            conf=confidence,
                            classes=class_ids,
                            verbose=False
                        )

                        # Parse detections
                        detections = self.yolo_service._parse_detection_results(results[0])

                        # Draw bounding boxes and labels
                        if len(detections) > 0:
                            frames_with_detections += 1
                            total_detections += len(detections)

                            for det in detections:
                                class_name = det["class_name"]
                                conf = det["confidence"]
                                bbox = det["bbox"]  # [x1, y1, x2, y2]

                                # Get or create color for this class
                                if class_name not in colors:
                                    colors[class_name] = tuple(
                                        int(c) for c in np.random.randint(0, 255, 3)
                                    )
                                color = colors[class_name]

                                # Update class counts
                                class_counts[class_name] += 1

                                # Draw bounding box
                                x1, y1, x2, y2 = map(int, bbox)
                                cv2.rectangle(frame, (x1, y1), (x2, y2), color, line_width)

                                # Draw label with background
                                label = f"{class_name} {conf:.2f}"
                                font = cv2.FONT_HERSHEY_SIMPLEX

                                # Get text size
                                (text_width, text_height), baseline = cv2.getTextSize(
                                    label, font, font_scale, 1
                                )

                                # Draw label background
                                cv2.rectangle(
                                    frame,
                                    (x1, y1 - text_height - baseline - 5),
                                    (x1 + text_width, y1),
                                    color,
                                    -1  # Filled
                                )

                                # Draw label text
                                cv2.putText(
                                    frame,
                                    label,
                                    (x1, y1 - baseline - 2),
                                    font,
                                    font_scale,
                                    (255, 255, 255),  # White text
                                    1,
                                    cv2.LINE_AA
                                )

                        frames_processed += 1

                    # Write frame to output video
                    out.write(frame)
                    frame_number += 1

                    # Report progress via callback
                    if progress_callback and frame_number % 10 == 0:
                        try:
                            progress_callback(frame_number, f"Processing frame {frame_number}/{video_info['total_frames']}")
                        except Exception as e:
                            logger.warning(f"Progress callback error: {e}")

                    # Log progress
                    if frame_number % 100 == 0:
                        logger.info(f"Annotated {frame_number} frames...")

            finally:
                cap.release()
                out.release()

            return {
                "total_detections": total_detections,
                "frames_with_detections": frames_with_detections,
                "frames_processed": frames_processed,
                "frames_total": frame_number,
                "detections_by_class": dict(class_counts),
                "unique_classes": list(class_counts.keys())
            }

        # Run in executor
        stats = await loop.run_in_executor(self.executor, _process)
        return stats
