"""
Tests for ImageValidator and VideoValidator
"""
import pytest
from app.validators.image_validator import ImageValidator
from app.validators.video_validator import VideoValidator
from app.models.validation import ValidationResult


class TestImageValidator:
    """Test ImageValidator class"""

    def test_initialization_default(self):
        """Test validator initialization with default values"""
        validator = ImageValidator()
        assert validator.max_file_size_mb == 10
        assert validator.max_file_size_bytes == 10 * 1024 * 1024

    def test_initialization_custom(self):
        """Test validator initialization with custom values"""
        validator = ImageValidator(max_file_size_mb=20)
        assert validator.max_file_size_mb == 20
        assert validator.max_file_size_bytes == 20 * 1024 * 1024

    @pytest.mark.asyncio
    async def test_validate_bytes_success(self, sample_image_bytes):
        """Test validating valid image bytes"""
        validator = ImageValidator()
        result = await validator.validate_bytes(sample_image_bytes)

        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert result.error_message is None

    @pytest.mark.asyncio
    async def test_validate_empty_bytes(self):
        """Test validating empty bytes"""
        validator = ImageValidator()
        result = await validator.validate_bytes(b'')

        assert result.is_valid is False
        assert "empty" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_validate_too_large(self):
        """Test validating oversized image"""
        validator = ImageValidator(max_file_size_mb=1)
        # Create 2MB of data
        large_bytes = b'x' * (2 * 1024 * 1024)
        result = await validator.validate_bytes(large_bytes)

        assert result.is_valid is False
        assert "too large" in result.error_message.lower()
        assert "2.0MB" in result.error_message
        assert "max: 1MB" in result.error_message

    @pytest.mark.asyncio
    async def test_validate_invalid_format(self):
        """Test validating invalid image format"""
        validator = ImageValidator()
        invalid_bytes = b'This is not an image'
        result = await validator.validate_bytes(invalid_bytes)

        assert result.is_valid is False
        assert "invalid image format" in result.error_message.lower()

    def test_validate_confidence_valid(self):
        """Test validating valid confidence values"""
        validator = ImageValidator()

        # Test boundary values
        assert validator.validate_confidence(0.0).is_valid is True
        assert validator.validate_confidence(0.5).is_valid is True
        assert validator.validate_confidence(1.0).is_valid is True

    def test_validate_confidence_invalid(self):
        """Test validating invalid confidence values"""
        validator = ImageValidator()

        # Test out of range values
        result_low = validator.validate_confidence(-0.1)
        assert result_low.is_valid is False
        assert "between 0.0 and 1.0" in result_low.error_message

        result_high = validator.validate_confidence(1.5)
        assert result_high.is_valid is False
        assert "between 0.0 and 1.0" in result_high.error_message

    @pytest.mark.asyncio
    async def test_validate_bytes_with_large_valid_image(self, sample_large_image_bytes):
        """Test validating a large but valid image"""
        # The large image is about 2.5MB, validator allows 10MB by default
        validator = ImageValidator()
        result = await validator.validate_bytes(sample_large_image_bytes)

        assert result.is_valid is True


class TestVideoValidator:
    """Test VideoValidator class"""

    def test_initialization_default(self):
        """Test validator initialization with default values"""
        validator = VideoValidator()
        assert validator.max_file_size_mb == 50
        assert validator.max_file_size_bytes == 50 * 1024 * 1024
        assert 'mp4' in validator.supported_formats
        assert 'avi' in validator.supported_formats

    def test_initialization_custom(self):
        """Test validator initialization with custom max size"""
        validator = VideoValidator(max_file_size_mb=100)
        assert validator.max_file_size_mb == 100
        assert validator.max_file_size_bytes == 100 * 1024 * 1024

    @pytest.mark.asyncio
    async def test_validate_bytes_success(self):
        """Test validating valid video bytes"""
        validator = VideoValidator()
        video_bytes = b'fake_video_data' * 100  # Small fake video
        result = await validator.validate_bytes(video_bytes, filename="test.mp4")

        assert isinstance(result, ValidationResult)
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_bytes_no_filename(self):
        """Test validating video without filename"""
        validator = VideoValidator()
        video_bytes = b'fake_video_data' * 100
        result = await validator.validate_bytes(video_bytes)

        # Should pass validation without filename (format check skipped)
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_too_large(self):
        """Test validating oversized video"""
        validator = VideoValidator(max_file_size_mb=1)
        # Create 2MB of data
        large_bytes = b'x' * (2 * 1024 * 1024)
        result = await validator.validate_bytes(large_bytes)

        assert result.is_valid is False
        assert "too large" in result.error_message.lower()
        assert "2.0MB" in result.error_message
        assert "max: 1MB" in result.error_message

    @pytest.mark.asyncio
    async def test_validate_supported_formats(self):
        """Test validating various supported video formats"""
        validator = VideoValidator()
        video_bytes = b'fake_video_data' * 100

        supported_formats = ['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'm4v']
        for fmt in supported_formats:
            result = await validator.validate_bytes(video_bytes, filename=f"test.{fmt}")
            assert result.is_valid is True, f"Format .{fmt} should be supported"

    @pytest.mark.asyncio
    async def test_validate_unsupported_format(self):
        """Test validating unsupported video format"""
        validator = VideoValidator()
        video_bytes = b'fake_video_data' * 100
        result = await validator.validate_bytes(video_bytes, filename="test.xyz")

        assert result.is_valid is False
        assert "unsupported video format" in result.error_message.lower()
        assert ".xyz" in result.error_message

    @pytest.mark.asyncio
    async def test_validate_format_case_insensitive(self):
        """Test that format validation is case insensitive"""
        validator = VideoValidator()
        video_bytes = b'fake_video_data' * 100

        # Test uppercase extension
        result_upper = await validator.validate_bytes(video_bytes, filename="test.MP4")
        assert result_upper.is_valid is True

        # Test mixed case extension
        result_mixed = await validator.validate_bytes(video_bytes, filename="test.MoV")
        assert result_mixed.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_filename_with_multiple_dots(self):
        """Test validating filename with multiple dots"""
        validator = VideoValidator()
        video_bytes = b'fake_video_data' * 100
        result = await validator.validate_bytes(video_bytes, filename="my.video.file.mp4")

        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_edge_case_size(self):
        """Test validating video at exactly the size limit"""
        validator = VideoValidator(max_file_size_mb=1)
        # Create exactly 1MB of data
        exact_size_bytes = b'x' * (1024 * 1024)
        result = await validator.validate_bytes(exact_size_bytes)

        # Should be valid at exactly the limit
        assert result.is_valid is True
