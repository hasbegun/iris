"""
Media type detection utilities
"""
import mimetypes
from typing import Literal, Optional

MediaType = Literal["image", "video"]


def detect_media_type(filename: Optional[str] = None, content_type: Optional[str] = None) -> MediaType:
    """
    Detect if file is image or video based on filename or content type

    Args:
        filename: Name of the file (optional)
        content_type: MIME content type (optional)

    Returns:
        "image" or "video"
    """
    # Check content_type first (more reliable)
    if content_type:
        if content_type.startswith('image/'):
            return "image"
        elif content_type.startswith('video/'):
            return "video"

    # Then check filename if available
    if filename:
        mime_type, _ = mimetypes.guess_type(filename)

        if mime_type:
            if mime_type.startswith('image/'):
                return "image"
            elif mime_type.startswith('video/'):
                return "video"

        # Fallback to extension-based detection
        extension = filename.lower().split('.')[-1]

        video_extensions = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'm4v'}
        if extension in video_extensions:
            return "video"

    # Default to image
    return "image"


def is_video_file(filename: Optional[str] = None, content_type: Optional[str] = None) -> bool:
    """Check if filename or content type represents a video file"""
    return detect_media_type(filename, content_type) == "video"


def is_image_file(filename: Optional[str] = None, content_type: Optional[str] = None) -> bool:
    """Check if filename or content type represents an image file"""
    return detect_media_type(filename, content_type) == "image"
