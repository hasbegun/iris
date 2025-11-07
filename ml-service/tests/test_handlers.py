"""
Tests for DetectionHandler and AnnotationHandler
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from fastapi import HTTPException, UploadFile
from fastapi.responses import Response
from io import BytesIO

from app.handlers.detection_handler import DetectionHandler
from app.handlers.annotation_handler import AnnotationHandler


# Helper function to create mock UploadFile
def create_mock_upload_file(content: bytes, filename: str = "test.jpg"):
    """Create a mock UploadFile for testing"""
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = filename
    mock_file.content_type = "image/jpeg"
    mock_file.read = AsyncMock(return_value=content)
    return mock_file


class TestDetectionHandler:
    """Test DetectionHandler class"""

    @pytest.fixture
    def mock_yolo_service(self):
        """Create a mock YOLO service"""
        service = AsyncMock()
        service.detect = AsyncMock(return_value={
            "status": "success",
            "count": 2,
            "detections": [
                {"class_name": "person", "confidence": 0.95, "bbox": [10, 20, 50, 80]},
                {"class_name": "dog", "confidence": 0.87, "bbox": [60, 30, 90, 70]}
            ],
            "image_shape": [100, 100, 3],
            "inference_time_ms": 45.2
        })
        service.segment = AsyncMock(return_value={
            "status": "success",
            "count": 1,
            "segments": [
                {"class_name": "car", "confidence": 0.92, "mask": [[10, 20], [50, 20]]}
            ],
            "image_shape": [100, 100, 3],
            "inference_time_ms": 52.1
        })
        service.detect_faces = AsyncMock(return_value={
            "status": "success",
            "count": 1,
            "faces": [
                {"confidence": 0.98, "bbox": [20, 30, 60, 80]}
            ],
            "image_shape": [100, 100, 3],
            "inference_time_ms": 38.5
        })
        return service

    @pytest.mark.asyncio
    async def test_process_detection_success(self, mock_yolo_service, sample_image_bytes):
        """Test successful object detection processing"""
        handler = DetectionHandler(yolo_service=mock_yolo_service)
        mock_file = create_mock_upload_file(sample_image_bytes)

        result = await handler.process(
            image=mock_file,
            confidence=0.5,
            classes="person,dog"
        )

        assert result["status"] == "success"
        assert result["count"] == 2
        assert len(result["detections"]) == 2
        mock_yolo_service.detect.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_detection_invalid_confidence(self, mock_yolo_service, sample_image_bytes):
        """Test detection with invalid confidence value"""
        handler = DetectionHandler(yolo_service=mock_yolo_service)
        mock_file = create_mock_upload_file(sample_image_bytes)

        with pytest.raises(HTTPException) as exc_info:
            await handler.process(
                image=mock_file,
                confidence=1.5,  # Invalid
                classes=None
            )

        assert exc_info.value.status_code == 400
        assert "confidence" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_process_detection_service_error(self, mock_yolo_service, sample_image_bytes):
        """Test detection when YOLO service returns error"""
        mock_yolo_service.detect = AsyncMock(return_value={
            "status": "error",
            "message": "Model loading failed"
        })

        handler = DetectionHandler(yolo_service=mock_yolo_service)
        mock_file = create_mock_upload_file(sample_image_bytes)

        with pytest.raises(HTTPException) as exc_info:
            await handler.process(
                image=mock_file,
                confidence=0.5,
                classes=None
            )

        assert exc_info.value.status_code == 400
        assert "Model loading failed" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_process_detection_with_classes(self, mock_yolo_service, sample_image_bytes):
        """Test detection with class filtering"""
        handler = DetectionHandler(yolo_service=mock_yolo_service)
        mock_file = create_mock_upload_file(sample_image_bytes)

        await handler.process(
            image=mock_file,
            confidence=0.5,
            classes="person,car,dog"
        )

        # Verify classes were parsed and passed to service
        call_args = mock_yolo_service.detect.call_args
        assert call_args[1]["classes"] == ["person", "car", "dog"]

    @pytest.mark.asyncio
    async def test_process_segmentation_success(self, mock_yolo_service, sample_image_bytes):
        """Test successful segmentation processing"""
        handler = DetectionHandler(yolo_service=mock_yolo_service)
        mock_file = create_mock_upload_file(sample_image_bytes)

        result = await handler.process_segmentation(
            image=mock_file,
            confidence=0.5,
            classes="car"
        )

        assert result["status"] == "success"
        assert result["count"] == 1
        assert len(result["segments"]) == 1
        mock_yolo_service.segment.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_face_detection_success(self, mock_yolo_service, sample_image_bytes):
        """Test successful face detection processing"""
        handler = DetectionHandler(yolo_service=mock_yolo_service)
        mock_file = create_mock_upload_file(sample_image_bytes)

        result = await handler.process_face_detection(
            image=mock_file,
            confidence=0.5
        )

        assert result["status"] == "success"
        assert result["count"] == 1
        assert len(result["faces"]) == 1
        mock_yolo_service.detect_faces.assert_called_once()


class TestAnnotationHandler:
    """Test AnnotationHandler class"""

    @pytest.fixture
    def mock_yolo_service(self):
        """Create a mock YOLO service"""
        service = AsyncMock()
        service.detect = AsyncMock(return_value={
            "status": "success",
            "detections": [
                {"class_name": "person", "class_id": 0, "confidence": 0.95, "bbox": [10, 20, 50, 80]},
            ]
        })
        service.segment = AsyncMock(return_value={
            "status": "success",
            "segments": [
                {
                    "class_name": "car",
                    "class_id": 2,
                    "confidence": 0.92,
                    "mask": [[10, 20], [50, 20], [50, 80], [10, 80]],
                    "bbox": [10, 20, 50, 80]
                }
            ]
        })
        service.detect_faces = AsyncMock(return_value={
            "status": "success",
            "faces": [
                {"confidence": 0.98, "bbox": [20, 30, 60, 80]}
            ]
        })
        return service

    @pytest.mark.asyncio
    async def test_process_not_implemented(self, mock_yolo_service):
        """Test that base process method raises NotImplementedError"""
        handler = AnnotationHandler(yolo_service=mock_yolo_service)

        with pytest.raises(NotImplementedError) as exc_info:
            await handler.process()

        assert "process_annotated_detection" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_process_annotated_detection_success(self, mock_yolo_service, sample_image_bytes):
        """Test successful annotated detection"""
        handler = AnnotationHandler(yolo_service=mock_yolo_service)
        mock_file = create_mock_upload_file(sample_image_bytes)

        with patch('app.handlers.annotation_handler.draw_bounding_boxes') as mock_draw:
            mock_draw.return_value = b'annotated_image_bytes'

            result = await handler.process_annotated_detection(
                image=mock_file,
                confidence=0.5,
                classes="person",
                line_width=3,
                font_size=20
            )

            assert isinstance(result, Response)
            assert result.media_type == "image/jpeg"
            assert result.body == b'annotated_image_bytes'
            mock_draw.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_annotated_detection_no_detections(self, mock_yolo_service, sample_image_bytes):
        """Test annotated detection with no detections returns original image"""
        mock_yolo_service.detect = AsyncMock(return_value={
            "status": "success",
            "detections": []
        })

        handler = AnnotationHandler(yolo_service=mock_yolo_service)
        mock_file = create_mock_upload_file(sample_image_bytes)

        result = await handler.process_annotated_detection(
            image=mock_file,
            confidence=0.5
        )

        # Should return original image when no detections
        assert isinstance(result, Response)
        assert result.body == sample_image_bytes

    @pytest.mark.asyncio
    async def test_process_annotated_detection_annotation_fails(self, mock_yolo_service, sample_image_bytes):
        """Test annotated detection when annotation drawing fails"""
        handler = AnnotationHandler(yolo_service=mock_yolo_service)
        mock_file = create_mock_upload_file(sample_image_bytes)

        with patch('app.handlers.annotation_handler.draw_bounding_boxes') as mock_draw:
            mock_draw.side_effect = Exception("Drawing failed")

            with pytest.raises(HTTPException) as exc_info:
                await handler.process_annotated_detection(
                    image=mock_file,
                    confidence=0.5
                )

            assert exc_info.value.status_code == 500
            assert "Failed to draw annotations" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_process_annotated_face_detection_success(self, mock_yolo_service, sample_image_bytes):
        """Test successful annotated face detection"""
        handler = AnnotationHandler(yolo_service=mock_yolo_service)
        mock_file = create_mock_upload_file(sample_image_bytes)

        with patch('app.handlers.annotation_handler.draw_faces') as mock_draw:
            mock_draw.return_value = b'annotated_image_bytes'

            result = await handler.process_annotated_face_detection(
                image=mock_file,
                confidence=0.5,
                line_width=3,
                font_size=20
            )

            assert isinstance(result, Response)
            assert result.media_type == "image/jpeg"
            mock_draw.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_annotated_face_detection_no_faces(self, mock_yolo_service, sample_image_bytes):
        """Test annotated face detection with no faces"""
        mock_yolo_service.detect_faces = AsyncMock(return_value={
            "status": "success",
            "faces": []
        })

        handler = AnnotationHandler(yolo_service=mock_yolo_service)
        mock_file = create_mock_upload_file(sample_image_bytes)

        result = await handler.process_annotated_face_detection(
            image=mock_file,
            confidence=0.5
        )

        # Should return original image when no faces
        assert isinstance(result, Response)
        assert result.body == sample_image_bytes

    @pytest.mark.asyncio
    async def test_process_annotated_segmentation_success(self, mock_yolo_service, sample_image_bytes):
        """Test successful annotated segmentation"""
        handler = AnnotationHandler(yolo_service=mock_yolo_service)
        mock_file = create_mock_upload_file(sample_image_bytes)

        with patch('app.handlers.annotation_handler.draw_segmentation_masks') as mock_draw:
            mock_draw.return_value = b'annotated_image_bytes'

            result = await handler.process_annotated_segmentation(
                image=mock_file,
                confidence=0.5,
                classes="car",
                opacity=0.5,
                line_width=2,
                font_size=20
            )

            assert isinstance(result, Response)
            assert result.media_type == "image/jpeg"
            mock_draw.assert_called_once()
            # Verify opacity was passed correctly
            call_kwargs = mock_draw.call_args[1]
            assert call_kwargs["opacity"] == 0.5

    @pytest.mark.asyncio
    async def test_process_annotated_segmentation_invalid_opacity(self, mock_yolo_service, sample_image_bytes):
        """Test annotated segmentation with invalid opacity"""
        handler = AnnotationHandler(yolo_service=mock_yolo_service)
        mock_file = create_mock_upload_file(sample_image_bytes)

        # Test opacity > 1.0
        with pytest.raises(HTTPException) as exc_info:
            await handler.process_annotated_segmentation(
                image=mock_file,
                confidence=0.5,
                opacity=1.5
            )

        assert exc_info.value.status_code == 400
        assert "opacity" in str(exc_info.value.detail).lower()

        # Test opacity < 0.0
        with pytest.raises(HTTPException) as exc_info:
            await handler.process_annotated_segmentation(
                image=mock_file,
                confidence=0.5,
                opacity=-0.1
            )

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_process_annotated_segmentation_no_segments(self, mock_yolo_service, sample_image_bytes):
        """Test annotated segmentation with no segments"""
        mock_yolo_service.segment = AsyncMock(return_value={
            "status": "success",
            "segments": []
        })

        handler = AnnotationHandler(yolo_service=mock_yolo_service)
        mock_file = create_mock_upload_file(sample_image_bytes)

        result = await handler.process_annotated_segmentation(
            image=mock_file,
            confidence=0.5
        )

        # Should return original image when no segments
        assert isinstance(result, Response)
        assert result.body == sample_image_bytes

    @pytest.mark.asyncio
    async def test_process_annotated_detection_service_error(self, mock_yolo_service, sample_image_bytes):
        """Test annotated detection when YOLO service returns error"""
        mock_yolo_service.detect = AsyncMock(return_value={
            "status": "error",
            "message": "Detection failed"
        })

        handler = AnnotationHandler(yolo_service=mock_yolo_service)
        mock_file = create_mock_upload_file(sample_image_bytes)

        with pytest.raises(HTTPException) as exc_info:
            await handler.process_annotated_detection(
                image=mock_file,
                confidence=0.5
            )

        assert exc_info.value.status_code == 400
        assert "Detection failed" in str(exc_info.value.detail)
