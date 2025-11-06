"""
Typed result classes for service layer
Provides type-safe return values instead of dictionaries
"""
from dataclasses import dataclass
from typing import List, Optional
from app.models.schemas import Detection, Segment


@dataclass
class DetectionResult:
    """
    Type-safe detection result

    Replaces dict returns from YOLOService.detect()
    """
    status: str
    detections: List[Detection]
    count: int
    inference_time_ms: float
    message: Optional[str] = None

    @property
    def is_success(self) -> bool:
        """Check if detection was successful"""
        return self.status == "success"

    @property
    def is_error(self) -> bool:
        """Check if there was an error"""
        return self.status == "error"

    @classmethod
    def success(
        cls,
        detections: List[Detection],
        inference_time_ms: float
    ) -> 'DetectionResult':
        """Create successful detection result"""
        return cls(
            status="success",
            detections=detections,
            count=len(detections),
            inference_time_ms=inference_time_ms
        )

    @classmethod
    def error(cls, message: str) -> 'DetectionResult':
        """Create error detection result"""
        return cls(
            status="error",
            detections=[],
            count=0,
            inference_time_ms=0.0,
            message=message
        )

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization"""
        result = {
            "status": self.status,
            "detections": [
                {
                    "class_name": d.class_name,
                    "confidence": d.confidence,
                    "bbox": d.bbox
                }
                for d in self.detections
            ],
            "count": self.count,
            "inference_time_ms": self.inference_time_ms
        }
        if self.message:
            result["message"] = self.message
        return result


@dataclass
class SegmentationResult:
    """
    Type-safe segmentation result

    Replaces dict returns from YOLOService.segment()
    """
    status: str
    segments: List[Segment]
    count: int
    inference_time_ms: float
    message: Optional[str] = None

    @property
    def is_success(self) -> bool:
        """Check if segmentation was successful"""
        return self.status == "success"

    @property
    def is_error(self) -> bool:
        """Check if there was an error"""
        return self.status == "error"

    @classmethod
    def success(
        cls,
        segments: List[Segment],
        inference_time_ms: float
    ) -> 'SegmentationResult':
        """Create successful segmentation result"""
        return cls(
            status="success",
            segments=segments,
            count=len(segments),
            inference_time_ms=inference_time_ms
        )

    @classmethod
    def error(cls, message: str) -> 'SegmentationResult':
        """Create error segmentation result"""
        return cls(
            status="error",
            segments=[],
            count=0,
            inference_time_ms=0.0,
            message=message
        )

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization"""
        result = {
            "status": self.status,
            "segments": [
                {
                    "class_name": s.class_name,
                    "confidence": s.confidence,
                    "bbox": s.bbox,
                    "mask": s.mask
                }
                for s in self.segments
            ],
            "count": self.count,
            "inference_time_ms": self.inference_time_ms
        }
        if self.message:
            result["message"] = self.message
        return result


@dataclass
class FaceDetectionResult:
    """
    Type-safe face detection result

    Replaces dict returns from YOLOService.detect_faces()
    """
    status: str
    faces: List[Detection]
    count: int
    inference_time_ms: float
    message: Optional[str] = None

    @property
    def is_success(self) -> bool:
        """Check if face detection was successful"""
        return self.status == "success"

    @property
    def is_error(self) -> bool:
        """Check if there was an error"""
        return self.status == "error"

    @classmethod
    def success(
        cls,
        faces: List[Detection],
        inference_time_ms: float
    ) -> 'FaceDetectionResult':
        """Create successful face detection result"""
        return cls(
            status="success",
            faces=faces,
            count=len(faces),
            inference_time_ms=inference_time_ms
        )

    @classmethod
    def error(cls, message: str) -> 'FaceDetectionResult':
        """Create error face detection result"""
        return cls(
            status="error",
            faces=[],
            count=0,
            inference_time_ms=0.0,
            message=message
        )

    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization"""
        result = {
            "status": self.status,
            "faces": [
                {
                    "class_name": f.class_name,
                    "confidence": f.confidence,
                    "bbox": f.bbox
                }
                for f in self.faces
            ],
            "count": self.count,
            "inference_time_ms": self.inference_time_ms
        }
        if self.message:
            result["message"] = self.message
        return result
