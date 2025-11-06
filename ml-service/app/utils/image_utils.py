"""
Image preprocessing utilities
"""
from PIL import Image
import io
import numpy as np
from typing import Tuple


def bytes_to_image(image_bytes: bytes) -> Image.Image:
    """
    Convert bytes to PIL Image

    Args:
        image_bytes: Image data as bytes

    Returns:
        PIL Image object
    """
    return Image.open(io.BytesIO(image_bytes))


def resize_image(image: Image.Image, max_size: int = 1920) -> Image.Image:
    """
    Resize image if larger than max_size while maintaining aspect ratio

    Args:
        image: PIL Image
        max_size: Maximum dimension size

    Returns:
        Resized PIL Image
    """
    width, height = image.size

    if width <= max_size and height <= max_size:
        return image

    # Calculate new dimensions maintaining aspect ratio
    if width > height:
        new_width = max_size
        new_height = int(height * (max_size / width))
    else:
        new_height = max_size
        new_width = int(width * (max_size / height))

    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def validate_image(image_bytes: bytes, max_size_mb: int = 10) -> Tuple[bool, str]:
    """
    Validate image data

    Args:
        image_bytes: Image data as bytes
        max_size_mb: Maximum file size in MB

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file size
    size_mb = len(image_bytes) / (1024 * 1024)
    if size_mb > max_size_mb:
        return False, f"Image size {size_mb:.2f}MB exceeds maximum {max_size_mb}MB"

    # Try to open image
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()  # Verify it's a valid image
        return True, ""
    except Exception as e:
        return False, f"Invalid image format: {str(e)}"


def image_to_numpy(image: Image.Image) -> np.ndarray:
    """
    Convert PIL Image to numpy array

    Args:
        image: PIL Image

    Returns:
        Numpy array (H, W, C)
    """
    return np.array(image)
