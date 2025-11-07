"""
Pytest configuration and fixtures for ML Service tests
"""
import pytest
import io
from PIL import Image
import numpy as np


@pytest.fixture
def sample_image_bytes():
    """Create a sample RGB image as bytes"""
    # Create a 100x100 RGB image with some colors
    img = Image.new('RGB', (100, 100), color=(255, 0, 0))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()


@pytest.fixture
def sample_large_image_bytes():
    """Create a large sample RGB image as bytes (for resize testing)"""
    # Create a 2500x2000 RGB image
    img = Image.new('RGB', (2500, 2000), color=(0, 255, 0))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()


@pytest.fixture
def sample_detections():
    """Sample detection results"""
    return [
        {
            "bbox": [10, 20, 50, 80],
            "class_name": "person",
            "class_id": 0,
            "confidence": 0.95
        },
        {
            "bbox": [60, 30, 90, 70],
            "class_name": "dog",
            "class_id": 1,
            "confidence": 0.87
        }
    ]


@pytest.fixture
def sample_segments():
    """Sample segmentation results"""
    return [
        {
            "mask": [[10, 20], [50, 20], [50, 80], [10, 80]],
            "bbox": [10, 20, 50, 80],
            "class_name": "person",
            "class_id": 0,
            "confidence": 0.95
        },
        {
            "mask": [[60, 30], [90, 30], [90, 70], [60, 70]],
            "bbox": [60, 30, 90, 70],
            "class_name": "car",
            "class_id": 2,
            "confidence": 0.88
        }
    ]


@pytest.fixture
def sample_faces():
    """Sample face detection results"""
    return [
        {
            "bbox": [20, 30, 60, 80],
            "confidence": 0.92
        },
        {
            "bbox": [70, 25, 95, 75],
            "confidence": 0.89
        }
    ]


@pytest.fixture
def sample_numpy_array():
    """Create a sample numpy array representing an image"""
    return np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
