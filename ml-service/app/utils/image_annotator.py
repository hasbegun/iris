"""
Image annotation utilities for drawing bounding boxes and labels
"""
import io
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Tuple, Optional


# Color palette for different classes (RGB format)
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


class ImageAnnotator:
    """
    Class for drawing annotations on images

    Provides methods for drawing bounding boxes, segmentation masks,
    and labels on images with consistent styling.
    """

    def __init__(self, font_size: int = 20, line_width: int = 3):
        """
        Initialize the image annotator

        Args:
            font_size: Default font size for labels
            line_width: Default line width for bounding boxes
        """
        self.font_size = font_size
        self.line_width = line_width
        self._font_cache: Dict[int, ImageFont.ImageFont] = {}

    def _load_font(self, size: Optional[int] = None) -> ImageFont.ImageFont:
        """
        Load and cache a font for text rendering

        Args:
            size: Font size (uses default if None)

        Returns:
            ImageFont object
        """
        size = size or self.font_size

        # Return cached font if available
        if size in self._font_cache:
            return self._font_cache[size]

        # Try to load a nice font, fall back to default if not available
        font = None
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
            except:
                font = ImageFont.load_default()

        # Cache the font
        self._font_cache[size] = font
        return font

    def _get_text_size(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        font: ImageFont.ImageFont
    ) -> Tuple[int, int]:
        """
        Get text dimensions for a given string

        Args:
            draw: ImageDraw context
            text: Text to measure
            font: Font to use

        Returns:
            Tuple of (width, height)
        """
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        except:
            # Fallback for older PIL versions
            return draw.textsize(text, font=font)

    def _draw_label(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        position: Tuple[float, float],
        color: Tuple[int, int, int],
        font: ImageFont.ImageFont
    ) -> None:
        """
        Draw a label with background at specified position

        Args:
            draw: ImageDraw context
            text: Label text
            position: (x, y) coordinates for label
            color: Background color
            font: Font to use
        """
        x, y = position
        text_width, text_height = self._get_text_size(draw, text, font)

        # Draw background
        label_bg_y1 = max(0, y - text_height - 10)
        draw.rectangle(
            [(x, label_bg_y1), (x + text_width + 10, y)],
            fill=color
        )

        # Draw text
        draw.text(
            (x + 5, label_bg_y1 + 2),
            text,
            fill=(255, 255, 255),  # White text
            font=font
        )

    @staticmethod
    def _get_color_for_class(class_id: int) -> Tuple[int, int, int]:
        """
        Get a consistent color for a class ID

        Args:
            class_id: Class ID

        Returns:
            RGB color tuple
        """
        return COLORS[class_id % len(COLORS)]

    @staticmethod
    def _image_to_bytes(image: Image.Image, format: str = "JPEG", quality: int = 95) -> bytes:
        """
        Convert PIL Image to bytes

        Args:
            image: PIL Image object
            format: Output format (JPEG, PNG, etc.)
            quality: Quality for JPEG compression

        Returns:
            Image as bytes
        """
        output = io.BytesIO()
        image.save(output, format=format, quality=quality)
        output.seek(0)
        return output.read()

    def draw_bounding_boxes(
        self,
        image_bytes: bytes,
        detections: List[Dict],
        line_width: Optional[int] = None,
        font_size: Optional[int] = None
    ) -> bytes:
        """
        Draw bounding boxes and labels on an image

        Args:
            image_bytes: Original image as bytes
            detections: List of detection dictionaries with bbox, class_name, confidence
            line_width: Width of bounding box lines (uses default if None)
            font_size: Size of label text (uses default if None)

        Returns:
            Annotated image as bytes (JPEG)
        """
        # Load image
        image = Image.open(io.BytesIO(image_bytes))
        draw = ImageDraw.Draw(image)

        # Get settings
        line_width = line_width or self.line_width
        font = self._load_font(font_size)

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
            color = self._get_color_for_class(class_id)

            # Draw bounding box
            draw.rectangle(
                [(x1, y1), (x2, y2)],
                outline=color,
                width=line_width
            )

            # Draw label
            label = f"{class_name} {confidence:.2f}"
            self._draw_label(draw, label, (x1, y1), color, font)

        return self._image_to_bytes(image)

    def draw_segmentation_masks(
        self,
        image_bytes: bytes,
        segments: List[Dict],
        opacity: float = 0.5,
        line_width: Optional[int] = None,
        font_size: Optional[int] = None
    ) -> bytes:
        """
        Draw segmentation masks as filled polygons with transparency

        Args:
            image_bytes: Original image as bytes
            segments: List of segmentation dictionaries with mask (polygon points), class_name, confidence
            opacity: Mask transparency (0.0 = fully transparent, 1.0 = fully opaque)
            line_width: Width of polygon outline (uses default if None)
            font_size: Size of label text (uses default if None)

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

        # Get settings
        line_width = line_width or self.line_width
        font = self._load_font(font_size)

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
            color = self._get_color_for_class(class_id)

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

            # Draw label
            label = f"{class_name} {confidence:.2f}"
            self._draw_label(draw, label, (x1, y1), color, font)

        # Composite overlay onto image
        image = Image.alpha_composite(image, overlay)

        # Convert back to RGB for JPEG
        image = image.convert("RGB")

        return self._image_to_bytes(image)

    def draw_faces(
        self,
        image_bytes: bytes,
        faces: List[Dict],
        line_width: Optional[int] = None,
        font_size: Optional[int] = None
    ) -> bytes:
        """
        Draw bounding boxes around detected faces

        Args:
            image_bytes: Original image as bytes
            faces: List of face detection dictionaries
            line_width: Width of bounding box lines (uses default if None)
            font_size: Size of label text (uses default if None)

        Returns:
            Annotated image as bytes (JPEG)
        """
        # Load image
        image = Image.open(io.BytesIO(image_bytes))
        draw = ImageDraw.Draw(image)

        # Get settings
        line_width = line_width or self.line_width
        font = self._load_font(font_size)

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

            # Draw label
            label = f"Person {idx + 1} ({confidence:.2f})"
            self._draw_label(draw, label, (x1, y1), color, font)

        return self._image_to_bytes(image)


# Convenience functions for backward compatibility
def get_color_for_class(class_id: int) -> Tuple[int, int, int]:
    """Get a consistent color for a class ID (backward compatibility)"""
    return ImageAnnotator._get_color_for_class(class_id)


def draw_bounding_boxes(
    image_bytes: bytes,
    detections: List[Dict],
    line_width: int = 3,
    font_size: int = 20
) -> bytes:
    """Draw bounding boxes on image (backward compatibility)"""
    annotator = ImageAnnotator(font_size=font_size, line_width=line_width)
    return annotator.draw_bounding_boxes(image_bytes, detections)


def draw_segmentation_masks(
    image_bytes: bytes,
    segments: List[Dict],
    opacity: float = 0.5,
    line_width: int = 2,
    font_size: int = 20
) -> bytes:
    """Draw segmentation masks on image (backward compatibility)"""
    annotator = ImageAnnotator(font_size=font_size, line_width=line_width)
    return annotator.draw_segmentation_masks(image_bytes, segments, opacity=opacity)


def draw_faces(
    image_bytes: bytes,
    faces: List[Dict],
    line_width: int = 3,
    font_size: int = 20
) -> bytes:
    """Draw face bounding boxes on image (backward compatibility)"""
    annotator = ImageAnnotator(font_size=font_size, line_width=line_width)
    return annotator.draw_faces(image_bytes, faces)
