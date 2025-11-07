"""
Image validation utilities
Validates image data before processing
"""
import io
from PIL import Image
from app.models.validation import ValidationResult


class ImageValidator:
    """
    Validates image data

    Checks:
    - File size limits
    - Image format validity
    - Image can be opened by PIL
    """

    def __init__(self, max_file_size_mb: int = 10):
        """
        Initialize image validator

        Args:
            max_file_size_mb: Maximum allowed file size in megabytes
        """
        self.max_file_size_mb = max_file_size_mb
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024

    async def validate_bytes(self, image_bytes: bytes) -> ValidationResult:
        """
        Validate image bytes

        Args:
            image_bytes: Raw image data

        Returns:
            ValidationResult with validation status and error message if failed
        """
        # Check if empty
        if not image_bytes:
            return ValidationResult.failure("Image data is empty")

        # Check size
        size_bytes = len(image_bytes)
        if size_bytes > self.max_file_size_bytes:
            size_mb = size_bytes / (1024 * 1024)
            return ValidationResult.failure(
                f"Image too large: {size_mb:.1f}MB (max: {self.max_file_size_mb}MB)"
            )

        # Check format and validity
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.verify()  # Verify it's a valid image
            return ValidationResult.success()
        except Exception as e:
            return ValidationResult.failure(
                f"Invalid image format: {str(e)}"
            )

    def validate_confidence(self, confidence: float) -> ValidationResult:
        """
        Validate confidence threshold

        Args:
            confidence: Confidence value to validate

        Returns:
            ValidationResult
        """
        if not 0.0 <= confidence <= 1.0:
            return ValidationResult.failure(
                f"Confidence must be between 0.0 and 1.0, got {confidence}"
            )
        return ValidationResult.success()
