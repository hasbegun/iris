"""
Pydantic models for API requests and responses.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class VisionAnalysisRequest(BaseModel):
    """Request for vision analysis."""

    prompt: str = Field(..., description="User's question or instruction about the image")
    session_id: Optional[str] = Field(None, description="Session ID for context tracking")


class ChatRequest(BaseModel):
    """Request for follow-up chat."""

    message: str = Field(..., description="User's follow-up question")
    session_id: str = Field(..., description="Session ID to maintain context")


class VisionAnalysisResponse(BaseModel):
    """Response from vision analysis."""

    model_config = ConfigDict(protected_namespaces=())

    session_id: str = Field(..., description="Session ID for future reference")
    response: str = Field(..., description="AI's response to the prompt")
    model_used: str = Field(..., description="Model used for analysis")
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatResponse(BaseModel):
    """Response from chat."""

    model_config = ConfigDict(protected_namespaces=())

    session_id: str = Field(..., description="Session ID")
    response: str = Field(..., description="AI's response")
    model_used: str = Field(..., description="Model used for chat")
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    ollama_connected: bool
    available_models: List[str]
    timestamp: datetime = Field(default_factory=datetime.now)


class StreamFrameMetadata(BaseModel):
    """Metadata for video stream frames."""

    frame_number: int
    timestamp_ms: float
    is_keyframe: bool = False


class AgentQueryRequest(BaseModel):
    """Request for agent-based image analysis."""

    query: str = Field(..., description="Natural language query about the image")
    session_id: str = Field(..., description="Session ID to retrieve the image")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Detection confidence threshold")
    annotate: bool = Field(False, description="Return annotated image with bounding boxes")


class AgentQueryResponse(BaseModel):
    """Response from agent-based analysis."""

    model_config = ConfigDict(protected_namespaces=())

    session_id: str = Field(..., description="Session ID")
    query: str = Field(..., description="Original query")
    response: str = Field(..., description="Agent's response")
    status: str = Field(..., description="Status of the request")
    timestamp: datetime = Field(default_factory=datetime.now)
    annotated_image_url: Optional[str] = Field(None, description="URL to annotated image (if annotate=True)")


class Detection(BaseModel):
    """Single object detection result."""

    class_name: str = Field(..., description="Detected object class name")
    confidence: float = Field(..., description="Detection confidence (0.0-1.0)")
    bbox: List[float] = Field(..., description="Bounding box [x1, y1, x2, y2] in pixels")


class ImageMetadata(BaseModel):
    """Image dimensions metadata."""

    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")


class AgentAnalyzeResponse(BaseModel):
    """Response from unified agent analysis (image + query in one request)."""

    model_config = ConfigDict(protected_namespaces=())

    session_id: str = Field(..., description="Session ID for future reference")
    response: str = Field(..., description="Agent's response to the prompt")
    model_used: str = Field(..., description="Model used for analysis")
    processing_time: float = Field(..., description="Processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.now)
    annotated_image_url: Optional[str] = Field(None, description="URL to annotated image if available")
    has_annotated_image: bool = Field(False, description="Whether annotated image is available")
    detections: Optional[List[Detection]] = Field(None, description="Raw detection results with bounding boxes")
    image_metadata: Optional[ImageMetadata] = Field(None, description="Original image dimensions")


class DetectionRequest(BaseModel):
    """Direct detection request (without agent)."""

    session_id: str = Field(..., description="Session ID to retrieve the image")
    object_types: Optional[str] = Field(None, description="Comma-separated object types")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Detection confidence threshold")


class DetectionResponse(BaseModel):
    """Direct detection response."""

    status: str
    detections: List[dict]
    total_count: int
    summary: str
    inference_time_ms: Optional[float] = None
