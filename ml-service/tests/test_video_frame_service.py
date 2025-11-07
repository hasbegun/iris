"""
Tests for VideoFrameService
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from app.services.video_frame_service import VideoFrameService, VideoInfo, FrameData


class TestVideoInfo:
    """Test VideoInfo dataclass"""

    def test_video_info_creation(self):
        """Test creating VideoInfo"""
        info = VideoInfo(
            total_frames=300,
            fps=30.0,
            duration=10.0,
            width=1920,
            height=1080
        )
        assert info.total_frames == 300
        assert info.fps == 30.0
        assert info.duration == 10.0
        assert info.width == 1920
        assert info.height == 1080


class TestFrameData:
    """Test FrameData dataclass"""

    def test_frame_data_creation(self):
        """Test creating FrameData"""
        frame_data = FrameData(
            frame_bytes=b'test_bytes',
            frame_index=5,
            timestamp=0.5,
            frame_base64='dGVzdF9ieXRlcw=='
        )
        assert frame_data.frame_bytes == b'test_bytes'
        assert frame_data.frame_index == 5
        assert frame_data.timestamp == 0.5
        assert frame_data.frame_base64 == 'dGVzdF9ieXRlcw=='

    def test_frame_data_optional_base64(self):
        """Test FrameData with optional base64"""
        frame_data = FrameData(
            frame_bytes=b'test_bytes',
            frame_index=5,
            timestamp=0.5
        )
        assert frame_data.frame_base64 is None


class TestVideoFrameService:
    """Test VideoFrameService class"""

    def test_initialization(self):
        """Test service initialization"""
        service = VideoFrameService()
        assert service is not None

    def test_encode_bytes_to_base64(self):
        """Test base64 encoding"""
        test_bytes = b'Hello World'
        result = VideoFrameService.encode_bytes_to_base64(test_bytes)
        assert result == 'SGVsbG8gV29ybGQ='
        assert isinstance(result, str)

    @patch('app.services.video_frame_service.cv2.VideoCapture')
    @patch('app.services.video_frame_service.tempfile.mkstemp')
    @patch('os.write')
    @patch('os.close')
    @patch('os.remove')
    @patch('os.path.exists')
    @patch('app.services.video_frame_service.cv2.CAP_PROP_FRAME_COUNT', 7)
    @patch('app.services.video_frame_service.cv2.CAP_PROP_FPS', 5)
    @patch('app.services.video_frame_service.cv2.CAP_PROP_FRAME_WIDTH', 3)
    @patch('app.services.video_frame_service.cv2.CAP_PROP_FRAME_HEIGHT', 4)
    def test_get_video_info(
        self,
        mock_exists,
        mock_remove,
        mock_os_close,
        mock_os_write,
        mock_mkstemp,
        mock_capture_class
    ):
        """Test getting video info"""
        # Setup mocks
        mock_mkstemp.return_value = (123, '/tmp/test.mp4')
        mock_exists.return_value = True

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        # Create a side_effect that returns different values for different props
        get_values = {7: 300, 5: 30.0, 3: 1920, 4: 1080}
        mock_cap.get = MagicMock(side_effect=lambda prop: get_values.get(prop, 0))
        mock_capture_class.return_value = mock_cap

        # Test
        service = VideoFrameService()
        video_bytes = b'fake_video_bytes'
        info = service.get_video_info(video_bytes)

        # Assertions
        assert isinstance(info, VideoInfo)
        assert info.total_frames == 300
        assert info.fps == 30.0
        assert info.width == 1920
        assert info.height == 1080
        assert info.duration == 10.0  # 300 frames / 30 fps

        # Verify cleanup
        mock_cap.release.assert_called_once()
        mock_remove.assert_called_once()

    @patch('app.services.video_frame_service.cv2.VideoCapture')
    @patch('app.services.video_frame_service.tempfile.mkstemp')
    @patch('os.write')
    @patch('os.close')
    @patch('os.remove')
    @patch('os.path.exists')
    def test_get_video_info_failed_open(
        self,
        mock_exists,
        mock_remove,
        mock_os_close,
        mock_os_write,
        mock_mkstemp,
        mock_capture_class
    ):
        """Test get_video_info when video can't be opened"""
        mock_mkstemp.return_value = (123, '/tmp/test.mp4')
        mock_exists.return_value = True

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_capture_class.return_value = mock_cap

        service = VideoFrameService()
        video_bytes = b'fake_video_bytes'

        with pytest.raises(ValueError, match="Failed to open video file"):
            service.get_video_info(video_bytes)

    @patch('app.services.video_frame_service.cv2.VideoCapture')
    @patch('app.services.video_frame_service.cv2.cvtColor')
    @patch('app.services.video_frame_service.Image.fromarray')
    @patch('app.services.video_frame_service.tempfile.mkstemp')
    @patch('os.write')
    @patch('os.close')
    @patch('os.remove')
    @patch('os.path.exists')
    @patch('app.services.video_frame_service.cv2.CAP_PROP_FRAME_COUNT', 7)
    @patch('app.services.video_frame_service.cv2.CAP_PROP_FPS', 5)
    @patch('app.services.video_frame_service.cv2.CAP_PROP_POS_FRAMES', 1)
    def test_extract_single_frame(
        self,
        mock_exists,
        mock_remove,
        mock_os_close,
        mock_os_write,
        mock_mkstemp,
        mock_from_array,
        mock_cvt_color,
        mock_capture_class
    ):
        """Test extracting a single frame"""
        # Setup mocks
        mock_mkstemp.return_value = (123, '/tmp/test.mp4')
        mock_exists.return_value = True

        # Mock video capture
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        get_values = {7: 100, 5: 30.0}
        mock_cap.get = MagicMock(side_effect=lambda prop: get_values.get(prop, 0))

        # Create a fake frame
        fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, fake_frame)
        mock_capture_class.return_value = mock_cap

        # Mock image conversion
        mock_cvt_color.return_value = fake_frame
        mock_pil_image = MagicMock()
        mock_pil_image.save = MagicMock()
        mock_from_array.return_value = mock_pil_image

        # Mock BytesIO for JPEG output
        with patch('app.services.video_frame_service.BytesIO') as mock_bytesio:
            mock_bytes_obj = MagicMock()
            mock_bytes_obj.getvalue.return_value = b'jpeg_bytes'
            mock_bytesio.return_value = mock_bytes_obj

            # Test
            service = VideoFrameService()
            video_bytes = b'fake_video_bytes'
            frame_data = service.extract_single_frame(
                video_bytes=video_bytes,
                frame_index=50,
                include_base64=False,
                jpeg_quality=85
            )

            # Assertions
            assert isinstance(frame_data, FrameData)
            assert frame_data.frame_index == 50
            assert frame_data.timestamp == 50 / 30.0
            assert frame_data.frame_bytes == b'jpeg_bytes'
            assert frame_data.frame_base64 is None

            # Verify frame seeking
            mock_cap.set.assert_called_once()

    @patch('app.services.video_frame_service.cv2.VideoCapture')
    @patch('app.services.video_frame_service.tempfile.mkstemp')
    @patch('os.write')
    @patch('os.close')
    @patch('os.remove')
    @patch('os.path.exists')
    @patch('app.services.video_frame_service.cv2.CAP_PROP_FRAME_COUNT', 7)
    @patch('app.services.video_frame_service.cv2.CAP_PROP_FPS', 5)
    def test_extract_single_frame_invalid_index(
        self,
        mock_exists,
        mock_remove,
        mock_os_close,
        mock_os_write,
        mock_mkstemp,
        mock_capture_class
    ):
        """Test extracting frame with invalid index"""
        mock_mkstemp.return_value = (123, '/tmp/test.mp4')
        mock_exists.return_value = True

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        get_values = {7: 100, 5: 30.0}
        mock_cap.get = MagicMock(side_effect=lambda prop: get_values.get(prop, 0))
        mock_capture_class.return_value = mock_cap

        service = VideoFrameService()
        video_bytes = b'fake_video_bytes'

        # Test with out of range index
        with pytest.raises(ValueError, match="out of range"):
            service.extract_single_frame(
                video_bytes=video_bytes,
                frame_index=150,  # > 100 total frames
                include_base64=False
            )

    def test_frame_to_jpeg_bytes(self):
        """Test converting frame to JPEG bytes"""
        # Create a simple test frame
        fake_frame = np.zeros((100, 100, 3), dtype=np.uint8)

        with patch('app.services.video_frame_service.cv2.cvtColor') as mock_cvt:
            with patch('app.services.video_frame_service.Image.fromarray') as mock_from_array:
                # Mock PIL image
                mock_pil_image = MagicMock()
                mock_from_array.return_value = mock_pil_image

                # Mock BytesIO
                with patch('app.services.video_frame_service.BytesIO') as mock_bytesio:
                    mock_bytes_obj = MagicMock()
                    mock_bytes_obj.getvalue.return_value = b'test_jpeg'
                    mock_bytesio.return_value = mock_bytes_obj

                    # Mock cvtColor to return RGB frame
                    mock_cvt.return_value = fake_frame

                    # Test
                    result = VideoFrameService._frame_to_jpeg_bytes(fake_frame, quality=90)

                    assert result == b'test_jpeg'
                    mock_pil_image.save.assert_called_once()

    @patch('app.services.video_frame_service.tempfile.mkstemp')
    @patch('os.write')
    @patch('os.close')
    def test_write_video_to_temp(self, mock_os_close, mock_os_write, mock_mkstemp):
        """Test writing video bytes to temporary file"""
        mock_mkstemp.return_value = (123, '/tmp/test.mp4')

        video_bytes = b'fake_video_data'
        result = VideoFrameService._write_video_to_temp(video_bytes, suffix='.mp4')

        assert result == '/tmp/test.mp4'
        mock_mkstemp.assert_called_once_with(suffix='.mp4')
        mock_os_write.assert_called_once_with(123, video_bytes)
        mock_os_close.assert_called_once_with(123)
