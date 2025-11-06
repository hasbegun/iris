"""
YOLO API endpoints
Exposes object detection, segmentation, and face detection via REST API

Refactored to use:
- Dependency injection (no global variables)
- Handler classes (reduce code duplication)
- Type-safe responses
- Better async patterns
"""
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import Response
from typing import Optional
import logging
import asyncio

from app.models.schemas import (
    DetectionResponse,
    SegmentationResponse,
    FaceDetectionResponse,
    VideoDetectionResponse,
    TaskSubmitResponse,
    TaskStatusResponse
)
from app.dependencies import YOLOServiceDep, VideoYOLOServiceDep
from app.handlers import DetectionHandler, AnnotationHandler
from app.services.task_manager import get_task_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["yolo"])


@router.post("/detect", response_model=DetectionResponse)
async def detect_objects(
    image: UploadFile = File(..., description="Image file to analyze"),
    confidence: float = Form(0.5, ge=0.0, le=1.0, description="Detection confidence threshold"),
    classes: Optional[str] = Form(None, description="Comma-separated class names (e.g., 'car,person,dog')"),
    service: YOLOServiceDep = None
):
    """
    Detect objects in an image using YOLO

    **Parameters:**
    - **image**: Image file (JPEG, PNG, WebP, etc.)
    - **confidence**: Detection confidence threshold (0.0 - 1.0)
    - **classes**: Optional comma-separated list of object classes to detect

    **Returns:**
    - List of detected objects with bounding boxes and confidence scores

    **Example:**
    ```bash
    curl -X POST "http://localhost:9001/api/detect" \\
      -F "image=@photo.jpg" \\
      -F "confidence=0.5" \\
      -F "classes=car,person"
    ```
    """
    handler = DetectionHandler(service)
    return await handler.process(image, confidence, classes)


@router.post("/segment", response_model=SegmentationResponse)
async def segment_objects(
    image: UploadFile = File(..., description="Image file to segment"),
    confidence: float = Form(0.5, ge=0.0, le=1.0, description="Segmentation confidence threshold"),
    classes: Optional[str] = Form(None, description="Comma-separated class names (e.g., 'car,person,dog')"),
    service: YOLOServiceDep = None
):
    """
    Perform instance segmentation on an image using YOLO

    **Parameters:**
    - **image**: Image file (JPEG, PNG, WebP, etc.)
    - **confidence**: Segmentation confidence threshold (0.0 - 1.0)
    - **classes**: Optional comma-separated list of object classes to segment

    **Returns:**
    - List of segmented objects with masks and bounding boxes

    **Example:**
    ```bash
    curl -X POST "http://localhost:9001/api/segment" \\
      -F "image=@photo.jpg" \\
      -F "confidence=0.5" \\
      -F "classes=car,person"
    ```
    """
    handler = DetectionHandler(service)
    return await handler.process_segmentation(image, confidence, classes)


@router.post("/detect-faces", response_model=FaceDetectionResponse)
async def detect_faces(
    image: UploadFile = File(..., description="Image or video file to analyze"),
    confidence: float = Form(0.5, ge=0.0, le=1.0, description="Detection confidence threshold"),
    service: YOLOServiceDep = None
):
    """
    Detect human faces in an image or video

    **Parameters:**
    - **image**: Image file (JPEG, PNG, WebP) or video file (MP4, MOV, AVI) up to 50MB
    - **confidence**: Detection confidence threshold (0.0 - 1.0)

    **File Size Limits:**
    - Images: 10MB max
    - Videos: 50MB max

    **Returns:**
    - List of detected faces with bounding boxes

    **Example:**
    ```bash
    # Image
    curl -X POST "http://localhost:9001/api/detect-faces" \\
      -F "image=@photo.jpg" \\
      -F "confidence=0.5"

    # Video
    curl -X POST "http://localhost:9001/api/detect-faces" \\
      -F "image=@video.mp4" \\
      -F "confidence=0.5"
    ```
    """
    handler = DetectionHandler(service)
    return await handler.process_face_detection(image, confidence)


@router.post("/detect-annotated")
async def detect_objects_annotated(
    image: UploadFile = File(..., description="Image or video file to analyze"),
    confidence: float = Form(0.7, ge=0.0, le=1.0, description="Detection confidence threshold"),
    classes: Optional[str] = Form(None, description="Comma-separated class names"),
    line_width: int = Form(3, ge=1, le=10, description="Bounding box line width"),
    font_size: int = Form(20, ge=10, le=50, description="Label font size"),
    service: YOLOServiceDep = None
):
    """
    Detect objects and return annotated image with bounding boxes

    **Parameters:**
    - **image**: Image file (JPEG, PNG, WebP) or video file (MP4, MOV, AVI) up to 50MB
    - **confidence**: Detection confidence threshold (0.0 - 1.0)
    - **classes**: Optional comma-separated list of object classes to detect
    - **line_width**: Width of bounding box lines (1-10)
    - **font_size**: Size of label text (10-50)

    **File Size Limits:**
    - Images: 10MB max
    - Videos: 50MB max

    **Returns:**
    - JPEG image with bounding boxes and labels drawn

    **Example:**
    ```bash
    curl -X POST "http://localhost:9001/api/detect-annotated" \\
      -F "image=@photo.jpg" \\
      -F "confidence=0.7" \\
      -F "classes=car,person" \\
      -o annotated.jpg
    ```
    """
    handler = AnnotationHandler(service)
    return await handler.process_annotated_detection(
        image, confidence, classes, line_width, font_size
    )


@router.post("/segment-annotated")
async def segment_objects_annotated(
    image: UploadFile = File(..., description="Image or video file to segment"),
    confidence: float = Form(0.7, ge=0.0, le=1.0, description="Segmentation confidence threshold"),
    classes: Optional[str] = Form(None, description="Comma-separated class names"),
    opacity: float = Form(0.5, ge=0.0, le=1.0, description="Mask transparency (0.0-1.0)"),
    line_width: int = Form(2, ge=1, le=10, description="Polygon outline width"),
    font_size: int = Form(20, ge=10, le=50, description="Label font size"),
    service: YOLOServiceDep = None
):
    """
    Segment objects and return annotated image with colored masks

    **Parameters:**
    - **image**: Image file (JPEG, PNG, WebP) or video file (MP4, MOV, AVI) up to 50MB
    - **confidence**: Segmentation confidence threshold (0.0 - 1.0)
    - **classes**: Optional comma-separated list of object classes to segment
    - **opacity**: Mask transparency (0.0 = transparent, 1.0 = opaque)
    - **line_width**: Width of polygon outline (1-10)
    - **font_size**: Size of label text (10-50)

    **File Size Limits:**
    - Images: 10MB max
    - Videos: 50MB max

    **Returns:**
    - JPEG image with segmentation masks and labels drawn

    **Example:**
    ```bash
    curl -X POST "http://localhost:9001/api/segment-annotated" \\
      -F "image=@photo.jpg" \\
      -F "confidence=0.7" \\
      -F "classes=car,person" \\
      -F "opacity=0.5" \\
      -o segmented.jpg
    ```
    """
    handler = AnnotationHandler(service)
    return await handler.process_annotated_segmentation(
        image, confidence, classes, opacity, line_width, font_size
    )


@router.post("/detect-faces-annotated")
async def detect_faces_annotated(
    image: UploadFile = File(..., description="Image or video file to analyze"),
    confidence: float = Form(0.7, ge=0.0, le=1.0, description="Detection confidence threshold"),
    line_width: int = Form(3, ge=1, le=10, description="Bounding box line width"),
    font_size: int = Form(20, ge=10, le=50, description="Label font size"),
    service: YOLOServiceDep = None
):
    """
    Detect faces and return annotated image with bounding boxes

    **Parameters:**
    - **image**: Image file (JPEG, PNG, WebP) or video file (MP4, MOV, AVI) up to 50MB
    - **confidence**: Detection confidence threshold (0.0 - 1.0)
    - **line_width**: Width of bounding box lines (1-10)
    - **font_size**: Size of label text (10-50)

    **File Size Limits:**
    - Images: 10MB max
    - Videos: 50MB max

    **Returns:**
    - JPEG image with bounding boxes and labels drawn

    **Example:**
    ```bash
    curl -X POST "http://localhost:9001/api/detect-faces-annotated" \\
      -F "image=@photo.jpg" \\
      -F "confidence=0.7" \\
      -o annotated.jpg
    ```
    """
    handler = AnnotationHandler(service)
    return await handler.process_annotated_face_detection(
        image, confidence, line_width, font_size
    )


# Video Detection Endpoints

@router.post("/detect-video", response_model=VideoDetectionResponse)
async def detect_objects_in_video(
    video: UploadFile = File(..., description="Video file to analyze"),
    confidence: float = Form(0.5, ge=0.0, le=1.0, description="Detection confidence threshold"),
    classes: Optional[str] = Form(None, description="Comma-separated class names (e.g., 'car,person,dog')"),
    frame_skip: int = Form(0, ge=0, le=10, description="Skip N frames between detections (0 = process all)"),
    video_service: VideoYOLOServiceDep = None
):
    """
    Detect objects in video frame-by-frame using YOLO

    **Parameters:**
    - **video**: Video file (MP4, MOV, AVI, etc.) up to 50MB
    - **confidence**: Detection confidence threshold (0.0 - 1.0)
    - **classes**: Optional comma-separated list of object classes to detect
    - **frame_skip**: Skip frames to speed up processing (0 = process all frames, 1 = every other frame, etc.)

    **Returns:**
    - Video metadata (resolution, FPS, duration)
    - Detection results for each processed frame
    - Summary statistics (total detections, unique classes, etc.)

    **Example:**
    ```bash
    curl -X POST "http://localhost:9001/api/detect-video" \\
      -F "video=@sample.mp4" \\
      -F "confidence=0.5" \\
      -F "classes=car,person,truck" \\
      -F "frame_skip=0"
    ```
    """
    try:
        # Read video file
        video_bytes = await video.read()

        # Parse classes
        class_list = None
        if classes:
            class_list = [c.strip() for c in classes.split(",") if c.strip()]

        # Process video
        result = await video_service.detect_objects_in_video(
            video_bytes=video_bytes,
            confidence=confidence,
            classes=class_list,
            frame_skip=frame_skip
        )

        # Handle errors
        if result.get("status") == "error":
            raise HTTPException(
                status_code=400,
                detail=result.get("message", "Video processing failed")
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in detect_objects_in_video endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process video: {str(e)}"
        )


@router.post("/segment-video")
async def segment_objects_in_video(
    video: UploadFile = File(..., description="Video file to segment"),
    confidence: float = Form(0.5, ge=0.0, le=1.0, description="Segmentation confidence threshold"),
    classes: Optional[str] = Form(None, description="Comma-separated class names (e.g., 'car,person,dog')"),
    frame_skip: int = Form(0, ge=0, le=10, description="Skip N frames between segmentations (0 = process all)"),
    video_service: VideoYOLOServiceDep = None
):
    """
    Segment objects in video frame-by-frame using YOLO

    **Parameters:**
    - **video**: Video file (MP4, MOV, AVI, etc.) up to 50MB
    - **confidence**: Segmentation confidence threshold (0.0 - 1.0)
    - **classes**: Optional comma-separated list of object classes to segment
    - **frame_skip**: Skip frames to speed up processing (0 = process all frames, 1 = every other frame, etc.)

    **Returns:**
    - Video metadata (resolution, FPS, duration)
    - Segmentation results with polygon masks for each processed frame
    - Summary statistics (total segmentations, unique classes, etc.)

    **Example:**
    ```bash
    curl -X POST "http://localhost:9001/api/segment-video" \\
      -F "video=@sample.mp4" \\
      -F "confidence=0.5" \\
      -F "classes=car,person,truck" \\
      -F "frame_skip=0"
    ```
    """
    try:
        # Read video file
        video_bytes = await video.read()

        # Parse classes
        class_list = None
        if classes:
            class_list = [c.strip() for c in classes.split(",") if c.strip()]

        # Process video with segmentation
        result = await video_service.segment_objects_in_video(
            video_bytes=video_bytes,
            confidence=confidence,
            classes=class_list,
            frame_skip=frame_skip
        )

        # Handle errors
        if result.get("status") == "error":
            raise HTTPException(
                status_code=400,
                detail=result.get("message", "Video segmentation failed")
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in segment_objects_in_video endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to segment video: {str(e)}"
        )


@router.post("/detect-faces-video", response_model=VideoDetectionResponse)
async def detect_faces_in_video(
    video: UploadFile = File(..., description="Video file to analyze"),
    confidence: float = Form(0.5, ge=0.0, le=1.0, description="Detection confidence threshold"),
    frame_skip: int = Form(0, ge=0, le=10, description="Skip N frames between detections (0 = process all)"),
    video_service: VideoYOLOServiceDep = None
):
    """
    Detect faces in video frame-by-frame

    **Parameters:**
    - **video**: Video file (MP4, MOV, AVI, etc.) up to 50MB
    - **confidence**: Detection confidence threshold (0.0 - 1.0)
    - **frame_skip**: Skip frames to speed up processing (0 = process all frames)

    **Returns:**
    - Video metadata and face detection results per frame

    **Example:**
    ```bash
    curl -X POST "http://localhost:9001/api/detect-faces-video" \\
      -F "video=@sample.mp4" \\
      -F "confidence=0.5" \\
      -F "frame_skip=0"
    ```
    """
    try:
        # Read video file
        video_bytes = await video.read()

        # Process video
        result = await video_service.detect_faces_in_video(
            video_bytes=video_bytes,
            confidence=confidence,
            frame_skip=frame_skip
        )

        # Handle errors
        if result.get("status") == "error":
            raise HTTPException(
                status_code=400,
                detail=result.get("message", "Video processing failed")
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in detect_faces_in_video endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process video: {str(e)}"
        )


@router.post("/detect-video-frame", response_model=dict)
async def detect_video_frame(
    video: UploadFile = File(..., description="Video file to analyze"),
    confidence: float = Form(0.5, ge=0.0, le=1.0, description="Detection confidence threshold"),
    classes: Optional[str] = Form(None, description="Comma-separated class names"),
    service: YOLOServiceDep = None
):
    """
    Extract a representative frame from video and run object detection on it.
    Returns the frame image + detection JSON (for frontend display).

    This is faster than processing the entire video - extracts middle frame,
    runs detection, and returns results suitable for frontend visualization.

    **Returns:**
    - frame_base64: The extracted frame as base64 JPEG
    - detections: List of detected objects with bounding boxes
    - image_shape: Frame dimensions [height, width]
    - frame_index: Which frame was extracted
    """
    try:
        import cv2
        import numpy as np
        import tempfile
        import os
        import base64
        from io import BytesIO
        from PIL import Image

        # Read video
        video_bytes = await video.read()

        # Write to temp file
        fd, temp_path = tempfile.mkstemp(suffix='.mp4')
        try:
            os.write(fd, video_bytes)
            os.close(fd)

            # Open video and extract middle frame
            cap = cv2.VideoCapture(temp_path)
            if not cap.isOpened():
                raise HTTPException(status_code=400, detail="Failed to open video file")

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            middle_frame_idx = total_frames // 2

            # Seek to middle frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame_idx)
            ret, frame = cap.read()
            cap.release()

            if not ret:
                raise HTTPException(status_code=400, detail="Failed to extract frame from video")

            # Convert frame to RGB and then to JPEG bytes
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)

            # Convert to JPEG bytes
            img_byte_arr = BytesIO()
            pil_image.save(img_byte_arr, format='JPEG', quality=85)
            frame_bytes = img_byte_arr.getvalue()

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        # Run detection on the extracted frame
        # Parse classes
        class_list = None
        if classes:
            class_list = [c.strip() for c in classes.split(",") if c.strip()]

        # Detect objects in the frame
        result = await service.detect_objects(
            image_bytes=frame_bytes,
            confidence=confidence,
            classes=class_list
        )

        # Encode frame as base64 for JSON response
        frame_base64 = base64.b64encode(frame_bytes).decode('utf-8')

        # Return frame + detections
        return {
            "status": "success",
            "frame_base64": frame_base64,
            "frame_index": middle_frame_idx,
            "total_frames": total_frames,
            "detections": result.get("detections", []),
            "image_shape": result.get("image_shape", []),
            "count": result.get("count", 0)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in detect_video_frame: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process video frame: {str(e)}"
        )


@router.post("/detect-video-frames", response_model=dict)
async def detect_video_frames(
    video: UploadFile = File(..., description="Video file to analyze"),
    confidence: float = Form(0.5, ge=0.0, le=1.0, description="Detection confidence threshold"),
    classes: Optional[str] = Form(None, description="Comma-separated class names"),
    frame_interval: float = Form(2.0, ge=0.5, le=10.0, description="Seconds between frames"),
    max_frames: int = Form(10, ge=1, le=20, description="Maximum frames to extract"),
    service: YOLOServiceDep = None
):
    """
    Extract multiple frames from video at intervals and run object detection on each.
    Returns array of frames with detection data for slideshow display.

    **Parameters:**
    - **video**: Video file (MP4, MOV, AVI, etc.)
    - **confidence**: Detection confidence threshold (0.0 - 1.0)
    - **classes**: Optional comma-separated list of object classes to detect
    - **frame_interval**: Seconds between extracted frames (0.5 - 10.0)
    - **max_frames**: Maximum number of frames to extract (1 - 20)

    **Returns:**
    - Array of frames with detections, timestamps, and image data

    **Example:**
    ```bash
    curl -X POST "http://localhost:9001/api/detect-video-frames" \\
      -F "video=@sample.mp4" \\
      -F "confidence=0.5" \\
      -F "frame_interval=2.0" \\
      -F "max_frames=10"
    ```
    """
    try:
        import cv2
        import numpy as np
        import tempfile
        import os
        import base64
        from io import BytesIO
        from PIL import Image

        # Read video
        video_bytes = await video.read()

        # Write to temp file
        fd, temp_path = tempfile.mkstemp(suffix='.mp4')
        try:
            os.write(fd, video_bytes)
            os.close(fd)

            # Open video
            cap = cv2.VideoCapture(temp_path)
            if not cap.isOpened():
                raise HTTPException(status_code=400, detail="Failed to open video file")

            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0

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

            # Parse classes
            class_list = None
            if classes:
                class_list = [c.strip() for c in classes.split(",") if c.strip()]

            # Extract frames and run detection
            results = []

            for frame_info in frames_to_extract:
                frame_idx = frame_info['index']
                timestamp = frame_info['timestamp']

                # Seek to frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()

                if not ret:
                    logger.warning(f"Failed to extract frame {frame_idx}, skipping")
                    continue

                # Convert frame to RGB and then to JPEG bytes
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)

                # Convert to JPEG bytes
                img_byte_arr = BytesIO()
                pil_image.save(img_byte_arr, format='JPEG', quality=85)
                frame_bytes = img_byte_arr.getvalue()

                # Run detection on this frame
                detection_result = await service.detect(
                    image_bytes=frame_bytes,
                    confidence=confidence,
                    classes=class_list
                )

                # Encode frame as base64
                frame_base64 = base64.b64encode(frame_bytes).decode('utf-8')

                # Build result for this frame
                results.append({
                    "frame_index": frame_idx,
                    "timestamp": round(timestamp, 2),
                    "frame_base64": frame_base64,
                    "detections": detection_result.get("detections", []),
                    "image_shape": detection_result.get("image_shape", []),
                    "count": detection_result.get("count", 0)
                })

                logger.info(f"Frame {frame_idx} ({timestamp:.2f}s): {detection_result.get('count', 0)} detections")

            cap.release()

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        # Calculate total detections across all frames
        total_detections = sum(f["count"] for f in results)

        logger.info(f"Processed {len(results)} frames, total {total_detections} detections")

        # Return results
        return {
            "status": "success",
            "total_frames_in_video": total_frames,
            "video_duration": round(duration, 2),
            "frames_analyzed": len(results),
            "total_detections": total_detections,
            "frames": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in detect_video_frames: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process video frames: {str(e)}"
        )


@router.post("/segment-video-frames", response_model=dict)
async def segment_video_frames(
    video: UploadFile = File(..., description="Video file to segment"),
    confidence: float = Form(0.5, ge=0.0, le=1.0, description="Segmentation confidence threshold"),
    classes: Optional[str] = Form(None, description="Comma-separated class names"),
    frame_interval: float = Form(2.0, ge=0.5, le=10.0, description="Seconds between frames"),
    max_frames: int = Form(10, ge=1, le=20, description="Maximum frames to extract"),
    service: YOLOServiceDep = None
):
    """
    Extract multiple frames from video at intervals and run instance segmentation on each.
    Returns array of frames with segmentation data (polygon masks) for slideshow display.

    **Parameters:**
    - **video**: Video file (MP4, MOV, AVI, etc.)
    - **confidence**: Segmentation confidence threshold (0.0 - 1.0)
    - **classes**: Optional comma-separated list of object classes to segment
    - **frame_interval**: Seconds between extracted frames (0.5 - 10.0)
    - **max_frames**: Maximum number of frames to extract (1 - 20)

    **Returns:**
    - Array of frames with segmentation masks, timestamps, and image data

    **Example:**
    ```bash
    curl -X POST "http://localhost:9001/api/segment-video-frames" \\
      -F "video=@sample.mp4" \\
      -F "confidence=0.5" \\
      -F "frame_interval=2.0" \\
      -F "max_frames=10"
    ```
    """
    try:
        import cv2
        import numpy as np
        import tempfile
        import os
        import base64
        from io import BytesIO
        from PIL import Image

        # Read video
        video_bytes = await video.read()

        # Write to temp file
        fd, temp_path = tempfile.mkstemp(suffix='.mp4')
        try:
            os.write(fd, video_bytes)
            os.close(fd)

            # Open video
            cap = cv2.VideoCapture(temp_path)
            if not cap.isOpened():
                raise HTTPException(status_code=400, detail="Failed to open video file")

            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0

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

            logger.info(f"Extracting {len(frames_to_extract)} frames for segmentation")

            # Parse classes
            class_list = None
            if classes:
                class_list = [c.strip() for c in classes.split(",") if c.strip()]

            # Extract frames and run segmentation
            results = []

            for frame_info in frames_to_extract:
                frame_idx = frame_info['index']
                timestamp = frame_info['timestamp']

                # Seek to frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()

                if not ret:
                    logger.warning(f"Failed to extract frame {frame_idx}, skipping")
                    continue

                # Convert frame to RGB and then to JPEG bytes
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)

                # Convert to JPEG bytes
                img_byte_arr = BytesIO()
                pil_image.save(img_byte_arr, format='JPEG', quality=85)
                frame_bytes = img_byte_arr.getvalue()

                # Run segmentation on this frame
                segmentation_result = await service.segment(
                    image_bytes=frame_bytes,
                    confidence=confidence,
                    classes=class_list
                )

                # Encode frame as base64
                frame_base64 = base64.b64encode(frame_bytes).decode('utf-8')

                # Build result for this frame
                results.append({
                    "frame_index": frame_idx,
                    "timestamp": round(timestamp, 2),
                    "frame_base64": frame_base64,
                    "segments": segmentation_result.get("segments", []),
                    "image_shape": segmentation_result.get("image_shape", []),
                    "count": segmentation_result.get("count", 0)
                })

                logger.info(f"Frame {frame_idx} ({timestamp:.2f}s): {segmentation_result.get('count', 0)} segments")

            cap.release()

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        # Calculate total segments across all frames
        total_segments = sum(f["count"] for f in results)

        logger.info(f"Segmented {len(results)} frames, total {total_segments} segments")

        # Return results
        return {
            "status": "success",
            "total_frames_in_video": total_frames,
            "video_duration": round(duration, 2),
            "frames_analyzed": len(results),
            "total_segments": total_segments,
            "frames": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in segment_video_frames: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to segment video frames: {str(e)}"
        )


@router.post("/detect-video-annotated")
async def detect_objects_in_video_annotated(
    video: UploadFile = File(..., description="Video file to analyze"),
    confidence: float = Form(0.5, ge=0.0, le=1.0, description="Detection confidence threshold"),
    classes: Optional[str] = Form(None, description="Comma-separated class names (e.g., 'car,person,dog')"),
    frame_skip: int = Form(0, ge=0, le=10, description="Skip N frames between detections (0 = process all)"),
    line_width: int = Form(2, ge=1, le=10, description="Bounding box line width"),
    font_scale: float = Form(0.6, ge=0.3, le=2.0, description="Label font scale"),
    video_service: VideoYOLOServiceDep = None
):
    """
    Detect objects in video and return annotated video with bounding boxes

    **Parameters:**
    - **video**: Video file (MP4, MOV, AVI, etc.) up to 50MB
    - **confidence**: Detection confidence threshold (0.0 - 1.0)
    - **classes**: Optional comma-separated list of object classes to detect
    - **frame_skip**: Skip frames to speed up processing (0 = process all frames)
    - **line_width**: Width of bounding box lines (1-10)
    - **font_scale**: Size of label text (0.3-2.0)

    **Returns:**
    - MP4 video file with bounding boxes and labels drawn on detected objects

    **Example:**
    ```bash
    curl -X POST "http://localhost:9001/api/detect-video-annotated" \\
      -F "video=@sample.mp4" \\
      -F "confidence=0.5" \\
      -F "classes=car,person,truck" \\
      -F "frame_skip=0" \\
      -F "line_width=2" \\
      -o annotated_output.mp4
    ```
    """
    try:
        # Read video file
        video_bytes = await video.read()

        # Parse classes
        class_list = None
        if classes:
            class_list = [c.strip() for c in classes.split(",") if c.strip()]

        logger.info(f"Processing video annotation: {video.filename}")

        # Process and annotate video
        annotated_video_bytes, stats = await video_service.detect_and_annotate_video(
            video_bytes=video_bytes,
            confidence=confidence,
            classes=class_list,
            frame_skip=frame_skip,
            line_width=line_width,
            font_scale=font_scale
        )

        logger.info(
            f"Video annotation complete: {stats['total_detections']} detections, "
            f"{stats['processing_time_seconds']}s"
        )

        # Return annotated video as MP4
        from fastapi.responses import Response
        return Response(
            content=annotated_video_bytes,
            media_type="video/mp4",
            headers={
                "Content-Disposition": f'attachment; filename="annotated_{video.filename}"',
                "X-Total-Detections": str(stats['total_detections']),
                "X-Frames-Processed": str(stats['frames_processed']),
                "X-Processing-Time": str(stats['processing_time_seconds'])
            }
        )

    except Exception as e:
        logger.error(f"Error in detect_objects_in_video_annotated endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to annotate video: {str(e)}"
        )


# Async Processing with Progress Tracking

async def _process_video_task(
    task_id: str,
    video_bytes: bytes,
    video_service,
    confidence: float,
    classes: Optional[list],
    frame_skip: int,
    line_width: int,
    font_scale: float
):
    """Background task to process video with progress tracking"""
    task_manager = get_task_manager()

    try:
        # Create progress callback
        def progress_callback(current_frame: int, message: str):
            task_manager.update_progress(task_id, current_frame, message)

        # Process video with progress tracking
        video_bytes_result, stats = await video_service.detect_and_annotate_video(
            video_bytes=video_bytes,
            confidence=confidence,
            classes=classes,
            frame_skip=frame_skip,
            line_width=line_width,
            font_scale=font_scale,
            progress_callback=progress_callback
        )

        # Store result (for now, just stats; video file would need file storage)
        result = {
            "status": "success",
            "stats": stats,
            "output_size_mb": len(video_bytes_result) / (1024*1024)
        }

        task_manager.complete_task(task_id, result)
        logger.info(f"Task {task_id} completed successfully")

    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}", exc_info=True)
        task_manager.fail_task(task_id, str(e))


@router.post("/detect-video-async", response_model=TaskSubmitResponse)
async def detect_video_async(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(..., description="Video file to analyze"),
    confidence: float = Form(0.5, ge=0.0, le=1.0),
    classes: Optional[str] = Form(None),
    frame_skip: int = Form(0, ge=0, le=10),
    line_width: int = Form(2, ge=1, le=10),
    font_scale: float = Form(0.6, ge=0.3, le=2.0),
    video_service: VideoYOLOServiceDep = None
):
    """
    Submit video for async processing with progress tracking

    Returns task ID that can be used to check progress

    **Example:**
    ```bash
    # Submit task
    curl -X POST "http://localhost:9001/api/detect-video-async" \\
      -F "video=@sample.mp4" \\
      -F "confidence=0.5"

    # Returns: {"task_id": "...", "status_url": "/api/task/{task_id}/status"}

    # Check progress
    curl "http://localhost:9001/api/task/{task_id}/status"
    ```
    """
    try:
        # Read video
        video_bytes = await video.read()

        # Parse classes
        class_list = None
        if classes:
            class_list = [c.strip() for c in classes.split(",") if c.strip()]

        # Get video info to know total frames
        import tempfile
        import os
        fd, temp_path = tempfile.mkstemp(suffix='.mp4')
        try:
            os.write(fd, video_bytes)
            os.close(fd)

            video_info = await video_service._get_video_info(temp_path)
            total_frames = video_info.get('total_frames', 0)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        # Create task
        task_manager = get_task_manager()
        task_id = task_manager.create_task(total_frames=total_frames)

        # Submit background task
        background_tasks.add_task(
            _process_video_task,
            task_id,
            video_bytes,
            video_service,
            confidence,
            class_list,
            frame_skip,
            line_width,
            font_scale
        )

        logger.info(f"Submitted async task {task_id} ({total_frames} frames)")

        return {
            "task_id": task_id,
            "status": "submitted",
            "message": f"Video processing started ({total_frames} frames)",
            "status_url": f"/api/task/{task_id}/status"
        }

    except Exception as e:
        logger.error(f"Error submitting async task: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit task: {str(e)}"
        )


@router.get("/task/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get status of a video processing task

    **Example:**
    ```bash
    curl "http://localhost:9001/api/task/{task_id}/status"
    ```

    **Response:**
    ```json
    {
      "task_id": "...",
      "status": "processing",
      "progress": 0.45,
      "current_frame": 330,
      "total_frames": 735,
      "message": "Processing frame 330/735",
      "elapsed_time": 3.2
    }
    ```
    """
    task_manager = get_task_manager()
    task = task_manager.get_task(task_id)

    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    return task.to_dict()


@router.get("/tasks")
async def list_tasks():
    """
    List all tasks (for debugging/admin)

    **Example:**
    ```bash
    curl "http://localhost:9001/api/tasks"
    ```
    """
    task_manager = get_task_manager()
    return {
        "tasks": task_manager.get_all_tasks(),
        "stats": task_manager.get_stats()
    }


@router.post("/detect-stream", response_model=DetectionResponse)
async def detect_stream(
    image: UploadFile = File(..., description="Camera frame to analyze"),
    confidence: float = Form(0.5, ge=0.0, le=1.0, description="Detection confidence threshold"),
    classes: Optional[str] = Form(None, description="Comma-separated class names to detect"),
    service: YOLOServiceDep = None
):
    """
    Real-time object detection optimized for live camera streams.

    This endpoint is optimized for low-latency processing of camera frames:
    - Fast inference with minimal overhead
    - Lightweight response format
    - No annotations generated (client-side rendering)
    - Suitable for 5+ FPS processing

    **Parameters:**
    - **image**: Camera frame (JPEG, PNG)
    - **confidence**: Detection confidence threshold (0.0 - 1.0)
    - **classes**: Optional comma-separated list of object classes

    **Returns:**
    - Lightweight detection results with bounding boxes only

    **Example:**
    ```bash
    curl -X POST "http://localhost:9001/api/detect-stream" \\
      -F "image=@frame.jpg" \\
      -F "confidence=0.5" \\
      -F "classes=car,person"
    ```

    **Performance Tips:**
    - Use JPEG format for frames (faster upload)
    - Keep resolution reasonable (640x480 or 1280x720)
    - Specify classes to reduce processing time
    - Use confidence >= 0.5 to reduce false positives
    """
    try:
        # Parse class filter
        class_list = None
        if classes and classes.strip():
            class_list = [c.strip() for c in classes.split(',') if c.strip()]
            logger.info(f"[Stream] Filtering for classes: {class_list}")

        # Read image bytes
        image_bytes = await image.read()

        # Log for debugging
        logger.info(f"[Stream] Processing frame: {len(image_bytes)} bytes, confidence={confidence}")

        # Run detection (fast path - no annotations)
        result = await service.detect(
            image_bytes=image_bytes,
            confidence=confidence,
            classes=class_list
        )

        # Convert dict result to DetectionResponse
        response = DetectionResponse(**result)

        # Log result
        logger.info(f"[Stream] Detected {len(response.detections)} objects in {response.inference_time_ms:.1f}ms")

        return response

    except Exception as e:
        logger.error(f"[Stream] Error processing frame: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process camera frame: {str(e)}"
        )


@router.post("/segment-stream", response_model=SegmentationResponse)
async def segment_stream(
    image: UploadFile = File(..., description="Camera frame to segment"),
    confidence: float = Form(0.5, ge=0.0, le=1.0, description="Segmentation confidence threshold"),
    classes: Optional[str] = Form(None, description="Comma-separated class names to segment"),
    service: YOLOServiceDep = None
):
    """
    Real-time instance segmentation optimized for live camera streams.

    This endpoint is optimized for low-latency segmentation of camera frames:
    - Fast inference with minimal overhead
    - Returns polygon masks for precise object boundaries
    - Lightweight response format
    - No annotations generated (client-side rendering)
    - Suitable for 3-5+ FPS processing

    **Parameters:**
    - **image**: Camera frame (JPEG, PNG)
    - **confidence**: Segmentation confidence threshold (0.0 - 1.0)
    - **classes**: Optional comma-separated list of object classes

    **Returns:**
    - Lightweight segmentation results with polygon masks

    **Example:**
    ```bash
    curl -X POST "http://localhost:9001/api/segment-stream" \\
      -F "image=@frame.jpg" \\
      -F "confidence=0.5" \\
      -F "classes=car,person"
    ```

    **Performance Tips:**
    - Use JPEG format for frames (faster upload)
    - Keep resolution reasonable (640x480 or 1280x720)
    - Specify classes to reduce processing time
    - Use confidence >= 0.5 to reduce false positives
    - Segmentation is ~10-20% slower than detection
    """
    try:
        # Parse class filter
        class_list = None
        if classes and classes.strip():
            class_list = [c.strip() for c in classes.split(',') if c.strip()]
            logger.info(f"[SegmentStream] Filtering for classes: {class_list}")

        # Read image bytes
        image_bytes = await image.read()

        # Log for debugging
        logger.info(f"[SegmentStream] Processing frame: {len(image_bytes)} bytes, confidence={confidence}")

        # Run segmentation (fast path - no annotations)
        result = await service.segment(
            image_bytes=image_bytes,
            confidence=confidence,
            classes=class_list
        )

        # Convert dict result to SegmentationResponse
        response = SegmentationResponse(**result)

        # Log result
        logger.info(f"[SegmentStream] Segmented {len(response.segments)} objects in {response.inference_time_ms:.1f}ms")

        return response

    except Exception as e:
        logger.error(f"[SegmentStream] Error processing frame: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to segment camera frame: {str(e)}"
        )
