"""
Image utility functions for resizing and optimizing images
"""
from io import BytesIO
from PIL import Image
import logging

logger = logging.getLogger(__name__)


def is_video(file_bytes: bytes) -> bool:
    """
    Check if bytes represent a video file.

    Args:
        file_bytes: File bytes to check

    Returns:
        True if video, False otherwise
    """
    if len(file_bytes) < 12:
        return False

    # Check file signature
    # MP4/MOV: ftyp at bytes 4-8
    if file_bytes[4:8] == b'ftyp':
        return True
    # WebM/MKV
    if file_bytes[:3] == b'\x1a\x45\xdf':
        return True
    # AVI
    if file_bytes[:4] == b'RIFF' and file_bytes[8:12] == b'AVI ':
        return True
    # Check for video MIME patterns
    if file_bytes[:4] == b'\x00\x00\x00\x18' or file_bytes[:4] == b'\x00\x00\x00\x1c':  # MP4 variations
        return True

    return False


def extract_video_frame(video_bytes: bytes) -> bytes:
    """
    Extract a single representative frame from video.

    Args:
        video_bytes: Video file bytes

    Returns:
        Frame as JPEG bytes
    """
    import cv2
    import numpy as np
    import tempfile
    import os

    try:
        # Write to temp file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp.write(video_bytes)
            temp_path = tmp.name

        # Open video
        cap = cv2.VideoCapture(temp_path)

        if not cap.isOpened():
            raise ValueError("Failed to open video")

        # Get middle frame
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        middle_frame_idx = total_frames // 2

        cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame_idx)
        ret, frame = cap.read()
        cap.release()

        # Clean up temp file
        os.unlink(temp_path)

        if not ret:
            raise ValueError("Failed to read frame")

        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Convert to PIL Image
        pil_image = Image.fromarray(frame_rgb)

        # Convert to JPEG bytes
        output = BytesIO()
        pil_image.save(output, format='JPEG', quality=85)

        frame_bytes = output.getvalue()
        logger.info(f"Extracted frame from video: {len(frame_bytes) / (1024*1024):.2f}MB")

        return frame_bytes

    except Exception as e:
        logger.error(f"Failed to extract video frame: {e}", exc_info=True)
        raise


def resize_image(
    image_bytes: bytes,
    max_dimension: int = 1920,
    quality: int = 85,
    format: str = "JPEG"
) -> bytes:
    """
    Resize image to fit within max_dimension while maintaining aspect ratio.
    Automatically detects and handles video files by extracting a frame first.

    Args:
        image_bytes: Original image or video as bytes
        max_dimension: Maximum width or height in pixels
        quality: JPEG quality (1-100), 85 is good balance
        format: Output format (JPEG, PNG, etc.)

    Returns:
        Resized image as bytes

    Example:
        28.9MB video → extract frame → ~2-5MB resized image
        28.9MB image (4000x3000) → ~2-5MB (1920x1440)
    """
    try:
        # Check if this is a video file
        if is_video(image_bytes):
            logger.info("Detected video file, extracting frame first")
            # Extract frame from video
            image_bytes = extract_video_frame(image_bytes)
            logger.info(f"Frame extracted, size: {len(image_bytes) / (1024*1024):.2f}MB")

        # Open image from bytes
        img = Image.open(BytesIO(image_bytes))

        original_size = len(image_bytes) / (1024 * 1024)  # MB
        original_dimensions = img.size

        # Convert RGBA to RGB for JPEG
        if format.upper() == "JPEG" and img.mode in ("RGBA", "LA", "P"):
            # Create white background
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = background

        # Check if resizing is needed
        width, height = img.size
        if width <= max_dimension and height <= max_dimension:
            # No resizing needed, but still optimize
            logger.info(f"Image already within limits ({width}x{height}), optimizing only")
        else:
            # Calculate new dimensions maintaining aspect ratio
            if width > height:
                new_width = max_dimension
                new_height = int((max_dimension / width) * height)
            else:
                new_height = max_dimension
                new_width = int((max_dimension / height) * width)

            # Resize using high-quality algorithm
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(f"Resized image from {original_dimensions} to {img.size}")

        # Save to bytes with optimization
        output = BytesIO()

        if format.upper() == "JPEG":
            img.save(output, format="JPEG", quality=quality, optimize=True)
        else:
            img.save(output, format=format, optimize=True)

        resized_bytes = output.getvalue()
        new_size = len(resized_bytes) / (1024 * 1024)  # MB

        reduction_percent = ((original_size - new_size) / original_size) * 100
        logger.info(
            f"Image size reduced: {original_size:.2f}MB -> {new_size:.2f}MB "
            f"({reduction_percent:.1f}% reduction)"
        )

        return resized_bytes

    except Exception as e:
        logger.error(f"Failed to resize image: {e}", exc_info=True)
        # Return original if resize fails
        logger.warning("Returning original image due to resize failure")
        return image_bytes


def get_image_info(image_bytes: bytes) -> dict:
    """
    Get information about an image.

    Args:
        image_bytes: Image as bytes

    Returns:
        Dictionary with image info (size, dimensions, format)
    """
    try:
        img = Image.open(BytesIO(image_bytes))
        return {
            "size_mb": len(image_bytes) / (1024 * 1024),
            "size_bytes": len(image_bytes),
            "width": img.size[0],
            "height": img.size[1],
            "format": img.format,
            "mode": img.mode
        }
    except Exception as e:
        logger.error(f"Failed to get image info: {e}")
        return {
            "size_mb": len(image_bytes) / (1024 * 1024),
            "size_bytes": len(image_bytes),
            "error": str(e)
        }
