"""
Tests for ImageProcessor utility class
"""
import pytest
from PIL import Image
import numpy as np
from app.utils.image_utils import ImageProcessor


class TestImageProcessor:
    """Test ImageProcessor class"""

    def test_bytes_to_image(self, sample_image_bytes):
        """Test converting bytes to PIL Image"""
        image = ImageProcessor.bytes_to_image(sample_image_bytes)
        assert isinstance(image, Image.Image)
        assert image.size == (100, 100)
        assert image.mode == 'RGB'

    def test_image_to_bytes_jpeg(self, sample_image_bytes):
        """Test converting PIL Image to JPEG bytes"""
        image = ImageProcessor.bytes_to_image(sample_image_bytes)
        result_bytes = ImageProcessor.image_to_bytes(image, format='JPEG', quality=85)

        assert isinstance(result_bytes, bytes)
        assert len(result_bytes) > 0

        # Verify we can read it back
        result_image = ImageProcessor.bytes_to_image(result_bytes)
        assert result_image.size == (100, 100)

    def test_image_to_bytes_png(self, sample_image_bytes):
        """Test converting PIL Image to PNG bytes"""
        image = ImageProcessor.bytes_to_image(sample_image_bytes)
        result_bytes = ImageProcessor.image_to_bytes(image, format='PNG')

        assert isinstance(result_bytes, bytes)
        assert len(result_bytes) > 0

    def test_resize_image_no_resize_needed(self, sample_image_bytes):
        """Test resize when image is already small enough"""
        image = ImageProcessor.bytes_to_image(sample_image_bytes)
        resized = ImageProcessor.resize_image(image, max_size=1920)

        # Should not be resized
        assert resized.size == image.size
        assert resized.size == (100, 100)

    def test_resize_image_width_larger(self, sample_large_image_bytes):
        """Test resize when width is the larger dimension"""
        image = ImageProcessor.bytes_to_image(sample_large_image_bytes)
        assert image.size == (2500, 2000)

        resized = ImageProcessor.resize_image(image, max_size=1920)

        # Width should be reduced to 1920, height proportionally
        assert resized.size[0] == 1920
        assert resized.size[1] == int(2000 * (1920 / 2500))

    def test_resize_image_maintains_aspect_ratio(self, sample_large_image_bytes):
        """Test that resize maintains aspect ratio"""
        image = ImageProcessor.bytes_to_image(sample_large_image_bytes)
        original_ratio = image.size[0] / image.size[1]

        resized = ImageProcessor.resize_image(image, max_size=1000)
        resized_ratio = resized.size[0] / resized.size[1]

        # Ratios should be very close (allowing for small rounding differences)
        assert abs(original_ratio - resized_ratio) < 0.01

    def test_validate_image_success(self, sample_image_bytes):
        """Test validating a valid image"""
        is_valid, error_msg = ImageProcessor.validate_image(sample_image_bytes)
        assert is_valid is True
        assert error_msg == ""

    def test_validate_image_too_large(self):
        """Test validating an image that's too large"""
        # Create a large byte array (15MB)
        large_bytes = b'x' * (15 * 1024 * 1024)

        is_valid, error_msg = ImageProcessor.validate_image(large_bytes, max_size_mb=10)
        assert is_valid is False
        assert "exceeds maximum" in error_msg

    def test_validate_image_invalid_format(self):
        """Test validating invalid image data"""
        invalid_bytes = b'not an image'

        is_valid, error_msg = ImageProcessor.validate_image(invalid_bytes)
        assert is_valid is False
        assert "Invalid image format" in error_msg

    def test_image_to_numpy(self, sample_image_bytes):
        """Test converting PIL Image to numpy array"""
        image = ImageProcessor.bytes_to_image(sample_image_bytes)
        array = ImageProcessor.image_to_numpy(image)

        assert isinstance(array, np.ndarray)
        assert array.shape == (100, 100, 3)  # Height, Width, Channels
        assert array.dtype == np.uint8

    def test_numpy_to_image(self, sample_numpy_array):
        """Test converting numpy array to PIL Image"""
        image = ImageProcessor.numpy_to_image(sample_numpy_array)

        assert isinstance(image, Image.Image)
        assert image.size == (100, 100)  # PIL uses (width, height)

    def test_roundtrip_numpy_conversion(self, sample_image_bytes):
        """Test converting image to numpy and back"""
        original_image = ImageProcessor.bytes_to_image(sample_image_bytes)

        # Convert to numpy and back
        array = ImageProcessor.image_to_numpy(original_image)
        result_image = ImageProcessor.numpy_to_image(array)

        assert result_image.size == original_image.size
        assert result_image.mode == original_image.mode


class TestBackwardCompatibility:
    """Test backward compatibility functions"""

    def test_bytes_to_image_compat(self, sample_image_bytes):
        """Test backward compatible bytes_to_image function"""
        from app.utils.image_utils import bytes_to_image

        image = bytes_to_image(sample_image_bytes)
        assert isinstance(image, Image.Image)
        assert image.size == (100, 100)

    def test_resize_image_compat(self, sample_large_image_bytes):
        """Test backward compatible resize_image function"""
        from app.utils.image_utils import resize_image, bytes_to_image

        image = bytes_to_image(sample_large_image_bytes)
        resized = resize_image(image, max_size=1000)

        assert resized.size[0] <= 1000
        assert resized.size[1] <= 1000

    def test_validate_image_compat(self, sample_image_bytes):
        """Test backward compatible validate_image function"""
        from app.utils.image_utils import validate_image

        is_valid, error_msg = validate_image(sample_image_bytes)
        assert is_valid is True

    def test_image_to_numpy_compat(self, sample_image_bytes):
        """Test backward compatible image_to_numpy function"""
        from app.utils.image_utils import image_to_numpy, bytes_to_image

        image = bytes_to_image(sample_image_bytes)
        array = image_to_numpy(image)

        assert isinstance(array, np.ndarray)
        assert array.shape == (100, 100, 3)
