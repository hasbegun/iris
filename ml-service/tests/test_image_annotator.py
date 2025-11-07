"""
Tests for ImageAnnotator utility class
"""
import pytest
from PIL import Image
import io
from app.utils.image_annotator import ImageAnnotator, COLORS


class TestImageAnnotator:
    """Test ImageAnnotator class"""

    def test_initialization_default(self):
        """Test annotator initialization with defaults"""
        annotator = ImageAnnotator()
        assert annotator.font_size == 20
        assert annotator.line_width == 3
        assert annotator._font_cache == {}

    def test_initialization_custom(self):
        """Test annotator initialization with custom values"""
        annotator = ImageAnnotator(font_size=30, line_width=5)
        assert annotator.font_size == 30
        assert annotator.line_width == 5

    def test_get_color_for_class(self):
        """Test getting consistent colors for class IDs"""
        # Test first few colors
        assert ImageAnnotator._get_color_for_class(0) == COLORS[0]
        assert ImageAnnotator._get_color_for_class(1) == COLORS[1]
        assert ImageAnnotator._get_color_for_class(9) == COLORS[9]

        # Test wrapping around
        assert ImageAnnotator._get_color_for_class(10) == COLORS[0]
        assert ImageAnnotator._get_color_for_class(11) == COLORS[1]

    def test_draw_bounding_boxes(self, sample_image_bytes, sample_detections):
        """Test drawing bounding boxes on image"""
        annotator = ImageAnnotator()
        result_bytes = annotator.draw_bounding_boxes(
            image_bytes=sample_image_bytes,
            detections=sample_detections
        )

        # Verify result is valid image bytes
        assert isinstance(result_bytes, bytes)
        assert len(result_bytes) > 0

        # Verify we can load the result as an image
        result_image = Image.open(io.BytesIO(result_bytes))
        assert result_image.size == (100, 100)

    def test_draw_bounding_boxes_custom_settings(self, sample_image_bytes, sample_detections):
        """Test drawing with custom line width and font size"""
        annotator = ImageAnnotator(font_size=25, line_width=5)
        result_bytes = annotator.draw_bounding_boxes(
            image_bytes=sample_image_bytes,
            detections=sample_detections,
            line_width=4,
            font_size=15
        )

        assert isinstance(result_bytes, bytes)
        assert len(result_bytes) > 0

    def test_draw_bounding_boxes_empty_detections(self, sample_image_bytes):
        """Test drawing with no detections"""
        annotator = ImageAnnotator()
        result_bytes = annotator.draw_bounding_boxes(
            image_bytes=sample_image_bytes,
            detections=[]
        )

        # Should still return valid image
        assert isinstance(result_bytes, bytes)
        result_image = Image.open(io.BytesIO(result_bytes))
        assert result_image.size == (100, 100)

    def test_draw_bounding_boxes_dict_bbox(self, sample_image_bytes):
        """Test drawing with dict-format bbox"""
        detections = [
            {
                "bbox": {"x1": 10, "y1": 20, "x2": 50, "y2": 80},
                "class_name": "cat",
                "class_id": 0,
                "confidence": 0.92
            }
        ]

        annotator = ImageAnnotator()
        result_bytes = annotator.draw_bounding_boxes(
            image_bytes=sample_image_bytes,
            detections=detections
        )

        assert isinstance(result_bytes, bytes)
        assert len(result_bytes) > 0

    def test_draw_segmentation_masks(self, sample_image_bytes, sample_segments):
        """Test drawing segmentation masks on image"""
        annotator = ImageAnnotator()
        result_bytes = annotator.draw_segmentation_masks(
            image_bytes=sample_image_bytes,
            segments=sample_segments,
            opacity=0.5
        )

        # Verify result is valid image bytes
        assert isinstance(result_bytes, bytes)
        assert len(result_bytes) > 0

        # Verify we can load the result as an image
        result_image = Image.open(io.BytesIO(result_bytes))
        assert result_image.size == (100, 100)
        assert result_image.mode == 'RGB'  # Should be converted back to RGB

    def test_draw_segmentation_masks_different_opacity(self, sample_image_bytes, sample_segments):
        """Test drawing with different opacity values"""
        annotator = ImageAnnotator()

        # Full opacity
        result1 = annotator.draw_segmentation_masks(
            image_bytes=sample_image_bytes,
            segments=sample_segments,
            opacity=1.0
        )
        assert isinstance(result1, bytes)

        # Low opacity
        result2 = annotator.draw_segmentation_masks(
            image_bytes=sample_image_bytes,
            segments=sample_segments,
            opacity=0.2
        )
        assert isinstance(result2, bytes)

    def test_draw_segmentation_masks_empty_segments(self, sample_image_bytes):
        """Test drawing with no segments"""
        annotator = ImageAnnotator()
        result_bytes = annotator.draw_segmentation_masks(
            image_bytes=sample_image_bytes,
            segments=[],
            opacity=0.5
        )

        # Should still return valid image
        assert isinstance(result_bytes, bytes)
        result_image = Image.open(io.BytesIO(result_bytes))
        assert result_image.size == (100, 100)

    def test_draw_faces(self, sample_image_bytes, sample_faces):
        """Test drawing face bounding boxes"""
        annotator = ImageAnnotator()
        result_bytes = annotator.draw_faces(
            image_bytes=sample_image_bytes,
            faces=sample_faces
        )

        # Verify result is valid image bytes
        assert isinstance(result_bytes, bytes)
        assert len(result_bytes) > 0

        # Verify we can load the result as an image
        result_image = Image.open(io.BytesIO(result_bytes))
        assert result_image.size == (100, 100)

    def test_draw_faces_empty(self, sample_image_bytes):
        """Test drawing with no faces"""
        annotator = ImageAnnotator()
        result_bytes = annotator.draw_faces(
            image_bytes=sample_image_bytes,
            faces=[]
        )

        # Should still return valid image
        assert isinstance(result_bytes, bytes)
        result_image = Image.open(io.BytesIO(result_bytes))
        assert result_image.size == (100, 100)

    def test_font_caching(self):
        """Test that fonts are cached properly"""
        annotator = ImageAnnotator(font_size=20)

        # Load a font
        font1 = annotator._load_font(20)
        assert 20 in annotator._font_cache

        # Load same size again - should use cache
        font2 = annotator._load_font(20)
        assert font1 is font2

        # Load different size - should create new entry
        font3 = annotator._load_font(30)
        assert 30 in annotator._font_cache
        assert font1 is not font3


class TestBackwardCompatibilityAnnotator:
    """Test backward compatibility functions for annotator"""

    def test_get_color_for_class_compat(self):
        """Test backward compatible get_color_for_class function"""
        from app.utils.image_annotator import get_color_for_class

        color = get_color_for_class(0)
        assert color == COLORS[0]
        assert isinstance(color, tuple)
        assert len(color) == 3

    def test_draw_bounding_boxes_compat(self, sample_image_bytes, sample_detections):
        """Test backward compatible draw_bounding_boxes function"""
        from app.utils.image_annotator import draw_bounding_boxes

        result_bytes = draw_bounding_boxes(
            image_bytes=sample_image_bytes,
            detections=sample_detections,
            line_width=3,
            font_size=20
        )

        assert isinstance(result_bytes, bytes)
        assert len(result_bytes) > 0

    def test_draw_segmentation_masks_compat(self, sample_image_bytes, sample_segments):
        """Test backward compatible draw_segmentation_masks function"""
        from app.utils.image_annotator import draw_segmentation_masks

        result_bytes = draw_segmentation_masks(
            image_bytes=sample_image_bytes,
            segments=sample_segments,
            opacity=0.5,
            line_width=2,
            font_size=20
        )

        assert isinstance(result_bytes, bytes)
        assert len(result_bytes) > 0

    def test_draw_faces_compat(self, sample_image_bytes, sample_faces):
        """Test backward compatible draw_faces function"""
        from app.utils.image_annotator import draw_faces

        result_bytes = draw_faces(
            image_bytes=sample_image_bytes,
            faces=sample_faces,
            line_width=3,
            font_size=20
        )

        assert isinstance(result_bytes, bytes)
        assert len(result_bytes) > 0
