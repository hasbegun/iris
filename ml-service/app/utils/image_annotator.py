"""
Image annotation utilities for drawing bounding boxes and labels
"""
import io
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Tuple
import random


# Color palette for different classes (BGR format)
COLORS = [
    (255, 0, 0),      # Red
    (0, 255, 0),      # Green
    (0, 0, 255),      # Blue
    (255, 255, 0),    # Yellow
    (255, 0, 255),    # Magenta
    (0, 255, 255),    # Cyan
    (255, 128, 0),    # Orange
    (128, 0, 255),    # Purple
    (0, 255, 128),    # Spring green
    (255, 0, 128),    # Rose
]


def get_color_for_class(class_id: int) -> Tuple[int, int, int]:
    """
    Get a consistent color for a class ID

    Args:
        class_id: Class ID

    Returns:
        RGB color tuple
    """
    return COLORS[class_id % len(COLORS)]


def draw_bounding_boxes(
    image_bytes: bytes,
    detections: List[Dict],
    line_width: int = 3,
    font_size: int = 20
) -> bytes:
    """
    Draw bounding boxes and labels on an image

    Args:
        image_bytes: Original image as bytes
        detections: List of detection dictionaries with bbox, class_name, confidence
        line_width: Width of bounding box lines
        font_size: Size of label text

    Returns:
        Annotated image as bytes (JPEG)
    """
    # Load image
    image = Image.open(io.BytesIO(image_bytes))

    # Create drawing context
    draw = ImageDraw.Draw(image)

    # Try to load a nice font, fall back to default if not available
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            font = ImageFont.load_default()

    # Draw each detection
    for detection in detections:
        # Handle both list format [x1, y1, x2, y2] and dict format
        bbox = detection.get("bbox", [])
        if isinstance(bbox, list) and len(bbox) == 4:
            x1, y1, x2, y2 = bbox
        elif isinstance(bbox, dict):
            x1 = bbox.get("x1", 0)
            y1 = bbox.get("y1", 0)
            x2 = bbox.get("x2", 0)
            y2 = bbox.get("y2", 0)
        else:
            continue  # Skip invalid bbox

        class_name = detection.get("class_name", "unknown")
        confidence = detection.get("confidence", 0.0)
        class_id = detection.get("class_id", 0)

        # Get color for this class
        color = get_color_for_class(class_id)

        # Draw bounding box
        draw.rectangle(
            [(x1, y1), (x2, y2)],
            outline=color,
            width=line_width
        )

        # Prepare label text
        label = f"{class_name} {confidence:.2f}"

        # Get text size for background
        try:
            bbox_text = draw.textbbox((x1, y1), label, font=font)
            text_width = bbox_text[2] - bbox_text[0]
            text_height = bbox_text[3] - bbox_text[1]
        except:
            # Fallback for older PIL versions
            text_width, text_height = draw.textsize(label, font=font)

        # Draw background for label
        label_bg_y1 = max(0, y1 - text_height - 10)
        draw.rectangle(
            [(x1, label_bg_y1), (x1 + text_width + 10, y1)],
            fill=color
        )

        # Draw label text
        draw.text(
            (x1 + 5, label_bg_y1 + 2),
            label,
            fill=(255, 255, 255),  # White text
            font=font
        )

    # Convert back to bytes
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=95)
    output.seek(0)

    return output.read()


def draw_segmentation_masks(
    image_bytes: bytes,
    segments: List[Dict],
    opacity: float = 0.5,
    line_width: int = 2,
    font_size: int = 20
) -> bytes:
    """
    Draw segmentation masks as filled polygons with transparency

    Args:
        image_bytes: Original image as bytes
        segments: List of segmentation dictionaries with mask (polygon points), class_name, confidence
        opacity: Mask transparency (0.0 = fully transparent, 1.0 = fully opaque)
        line_width: Width of polygon outline
        font_size: Size of label text

    Returns:
        Annotated image as bytes (JPEG)
    """
    # Load image
    image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

    # Create a transparent overlay for masks
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)

    # Create draw context for outlines and labels
    draw = ImageDraw.Draw(image)

    # Try to load a nice font
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            font = ImageFont.load_default()

    # Draw each segment
    for idx, segment in enumerate(segments):
        # Get mask polygon points
        mask = segment.get("mask", [])
        if not mask or len(mask) < 3:
            continue  # Need at least 3 points for a polygon

        class_name = segment.get("class_name", "unknown")
        confidence = segment.get("confidence", 0.0)
        class_id = segment.get("class_id", idx)

        # Get color for this class
        color = get_color_for_class(class_id)

        # Convert mask to flat list of coordinates for PIL
        # mask is [[x, y], [x, y], ...], need to convert to [x, y, x, y, ...]
        polygon_points = []
        for point in mask:
            if isinstance(point, (list, tuple)) and len(point) >= 2:
                polygon_points.extend([float(point[0]), float(point[1])])

        if len(polygon_points) < 6:  # Need at least 3 points (6 coordinates)
            continue

        # Draw filled polygon on overlay with transparency
        alpha = int(255 * opacity)
        fill_color = (*color, alpha)
        draw_overlay.polygon(polygon_points, fill=fill_color, outline=None)

        # Draw polygon outline on main image
        draw.line(polygon_points + polygon_points[:2], fill=color, width=line_width)

        # Get bounding box for label placement
        bbox = segment.get("bbox", [])
        if isinstance(bbox, list) and len(bbox) == 4:
            x1, y1, x2, y2 = bbox
        else:
            # Calculate bbox from mask points if not provided
            x_coords = [polygon_points[i] for i in range(0, len(polygon_points), 2)]
            y_coords = [polygon_points[i] for i in range(1, len(polygon_points), 2)]
            x1, y1 = min(x_coords), min(y_coords)
            x2, y2 = max(x_coords), max(y_coords)

        # Prepare label text
        label = f"{class_name} {confidence:.2f}"

        # Get text size for background
        try:
            bbox_text = draw.textbbox((x1, y1), label, font=font)
            text_width = bbox_text[2] - bbox_text[0]
            text_height = bbox_text[3] - bbox_text[1]
        except:
            text_width, text_height = draw.textsize(label, font=font)

        # Draw background for label
        label_bg_y1 = max(0, y1 - text_height - 10)
        draw.rectangle(
            [(x1, label_bg_y1), (x1 + text_width + 10, y1)],
            fill=color
        )

        # Draw label text
        draw.text(
            (x1 + 5, label_bg_y1 + 2),
            label,
            fill=(255, 255, 255),  # White text
            font=font
        )

    # Composite overlay onto image
    image = Image.alpha_composite(image, overlay)

    # Convert back to RGB for JPEG
    image = image.convert("RGB")

    # Convert to bytes
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=95)
    output.seek(0)

    return output.read()


def draw_faces(
    image_bytes: bytes,
    faces: List[Dict],
    line_width: int = 3,
    font_size: int = 20
) -> bytes:
    """
    Draw bounding boxes around detected faces

    Args:
        image_bytes: Original image as bytes
        faces: List of face detection dictionaries
        line_width: Width of bounding box lines
        font_size: Size of label text

    Returns:
        Annotated image as bytes (JPEG)
    """
    # Load image
    image = Image.open(io.BytesIO(image_bytes))

    # Create drawing context
    draw = ImageDraw.Draw(image)

    # Try to load a nice font
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            font = ImageFont.load_default()

    # Use green for faces
    color = (0, 255, 0)

    # Draw each face
    for idx, face in enumerate(faces):
        # Handle both list format [x1, y1, x2, y2] and dict format
        bbox = face.get("bbox", [])
        if isinstance(bbox, list) and len(bbox) == 4:
            x1, y1, x2, y2 = bbox
        elif isinstance(bbox, dict):
            x1 = bbox.get("x1", 0)
            y1 = bbox.get("y1", 0)
            x2 = bbox.get("x2", 0)
            y2 = bbox.get("y2", 0)
        else:
            continue  # Skip invalid bbox

        confidence = face.get("confidence", 0.0)

        # Draw bounding box
        draw.rectangle(
            [(x1, y1), (x2, y2)],
            outline=color,
            width=line_width
        )

        # Prepare label
        label = f"Person {idx + 1} ({confidence:.2f})"

        # Get text size
        try:
            bbox_text = draw.textbbox((x1, y1), label, font=font)
            text_width = bbox_text[2] - bbox_text[0]
            text_height = bbox_text[3] - bbox_text[1]
        except:
            text_width, text_height = draw.textsize(label, font=font)

        # Draw background for label
        label_bg_y1 = max(0, y1 - text_height - 10)
        draw.rectangle(
            [(x1, label_bg_y1), (x1 + text_width + 10, y1)],
            fill=color
        )

        # Draw label text
        draw.text(
            (x1 + 5, label_bg_y1 + 2),
            label,
            fill=(255, 255, 255),
            font=font
        )

    # Convert back to bytes
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=95)
    output.seek(0)

    return output.read()
