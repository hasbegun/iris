"""
Video validation for ML service
"""
from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validation operation"""
    is_valid: bool
    error_message: Optional[str] = None

    @classmethod
    def success(cls):
        """Create successful validation result"""
        return cls(is_valid=True)

    @classmethod
    def failure(cls, message: str):
        """Create failed validation result"""
        return cls(is_valid=False, error_message=message)


class VideoValidator:
    """Validates video files for ML processing"""

    def __init__(self, max_file_size_mb: int = 50):
        """
        Initialize video validator

        Args:
            max_file_size_mb: Maximum file size in megabytes (default: 50MB)
        """
        self.max_file_size_mb = max_file_size_mb
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024

        # Supported video formats
        self.supported_formats = {
            'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'm4v'
        }

    async def validate_bytes(self, video_bytes: bytes, filename: Optional[str] = None) -> ValidationResult:
        """
        Validate video data

        Args:
            video_bytes: Raw video data
            filename: Optional filename for format detection

        Returns:
            ValidationResult indicating success or failure
        """
        # Check size
        size_bytes = len(video_bytes)
        size_mb = size_bytes / (1024 * 1024)

        if size_bytes > self.max_file_size_bytes:
            return ValidationResult.failure(
                f"Video too large: {size_mb:.1f}MB (max: {self.max_file_size_mb}MB)"
            )

        # Check format if filename provided
        if filename:
            extension = filename.lower().split('.')[-1]
            if extension not in self.supported_formats:
                return ValidationResult.failure(
                    f"Unsupported video format: .{extension} "
                    f"(supported: {', '.join(sorted(self.supported_formats))})"
                )

        logger.info(f"Video validation passed: {size_mb:.1f}MB")
        return ValidationResult.success()
