"""
Pydantic models for ML service requests and responses
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Tuple


class BoundingBox(BaseModel):
    """Bounding box coordinates [x1, y1, x2, y2]"""
    x1: float
    y1: float
    x2: float
    y2: float


class Detection(BaseModel):
    """Single object detection result"""
    class_name: str = Field(..., description="Detected object class")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    bbox: List[float] = Field(..., description="Bounding box [x1, y1, x2, y2]")


class Segment(BaseModel):
    """Single segmentation result"""
    class_name: str = Field(..., description="Segmented object class")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Segmentation confidence")
    bbox: List[float] = Field(..., description="Bounding box [x1, y1, x2, y2]")
    mask: List[List[float]] = Field(..., description="Polygon points [[x1,y1], [x2,y2], ...]")


class DetectionResponse(BaseModel):
    """Object detection response"""
    status: str = "success"
    detections: List[Detection]
    count: int
    image_shape: Tuple[int, int] = Field(..., description="(height, width)")
    inference_time_ms: float = Field(..., description="Inference time in milliseconds")


class SegmentationResponse(BaseModel):
    """Segmentation response"""
    status: str = "success"
    segments: List[Segment]
    count: int
    image_shape: Tuple[int, int] = Field(..., description="(height, width)")
    inference_time_ms: float = Field(..., description="Inference time in milliseconds")


class FaceDetectionResponse(BaseModel):
    """Face detection response"""
    status: str = "success"
    faces: List[Detection]
    count: int
    image_shape: Tuple[int, int] = Field(..., description="(height, width)")
    inference_time_ms: float = Field(..., description="Inference time in milliseconds")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    models_loaded: bool
    device: str
    memory_available: Optional[str] = None


class MetricsResponse(BaseModel):
    """Service metrics response"""
    total_requests: int
    avg_inference_time_ms: float
    memory_usage_mb: float
    device: str
    uptime_seconds: float


# Video-specific schemas

class FrameDetection(BaseModel):
    """Detection results for a single frame"""
    frame_number: int = Field(..., description="Frame number (0-indexed)")
    timestamp: float = Field(..., description="Timestamp in seconds")
    detections: List[Detection] = Field(..., description="Objects detected in this frame")
    count: int = Field(..., description="Number of objects in this frame")


class VideoInfo(BaseModel):
    """Video metadata"""
    total_frames: int
    fps: float
    duration_seconds: float
    resolution: Tuple[int, int] = Field(..., description="(width, height)")


class VideoDetectionResponse(BaseModel):
    """Video object detection response"""
    status: str = "success"
    video_info: VideoInfo
    frame_detections: List[FrameDetection]
    summary: dict = Field(..., description="Detection summary statistics")
    processing_time_seconds: float
    avg_fps: float = Field(..., description="Average processing FPS")


class TaskSubmitResponse(BaseModel):
    """Response when submitting an async task"""
    task_id: str
    status: str = "submitted"
    message: str = "Task submitted for processing"
    status_url: str


class TaskStatusResponse(BaseModel):
    """Task status response"""
    task_id: str
    status: str
    progress: float
    current_frame: int
    total_frames: int
    message: str
    elapsed_time: float
    result: Optional[dict] = None
    error: Optional[str] = None
