# ML Service Tests

Comprehensive test suite for the ML Service refactored codebase.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                      # Shared fixtures
├── test_validation.py               # ValidationResult tests
├── test_yolo_api.py                 # parse_classes utility tests
├── test_image_utils.py              # ImageProcessor class tests
├── test_image_annotator.py          # ImageAnnotator class tests
├── test_video_frame_service.py      # VideoFrameService tests
├── test_validators.py               # ImageValidator & VideoValidator tests
├── test_handlers.py                 # DetectionHandler & AnnotationHandler tests
└── README.md                        # This file
```

## Test Coverage

### Unit Tests

1. **ValidationResult** (`test_validation.py`)
   - Success/failure creation
   - Boolean conversion
   - Error message handling

2. **parse_classes utility** (`test_yolo_api.py`)
   - Valid class parsing
   - Edge cases (empty, whitespace, commas)
   - Complex input handling

3. **ImageProcessor** (`test_image_utils.py`)
   - Bytes to image conversion
   - Image to bytes conversion (JPEG/PNG)
   - Image resizing with aspect ratio
   - Image validation
   - Numpy array conversion
   - Backward compatibility functions

4. **ImageAnnotator** (`test_image_annotator.py`)
   - Bounding box drawing
   - Segmentation mask drawing
   - Face detection visualization
   - Color consistency
   - Font caching
   - Backward compatibility functions

5. **VideoFrameService** (`test_video_frame_service.py`)
   - Video info extraction
   - Single frame extraction
   - Frame conversion to JPEG
   - Error handling
   - Temporary file management

6. **Validators** (`test_validators.py`)
   - ImageValidator: size limits, format validation, confidence validation
   - VideoValidator: size limits, format support, filename parsing

7. **Handlers** (`test_handlers.py`)
   - DetectionHandler: object detection, segmentation, face detection
   - AnnotationHandler: annotated images, error handling, opacity validation

## Running Tests

### Install Test Dependencies

```bash
pip install pytest pytest-asyncio
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
# From project root
pytest

# With verbose output
pytest -v

# With coverage
pytest --cov=app --cov-report=html
```

### Run Specific Test Files

```bash
# Test validation module
pytest tests/test_validation.py

# Test image utilities
pytest tests/test_image_utils.py

# Test YOLO API utilities
pytest tests/test_yolo_api.py
```

### Run Specific Test Classes or Functions

```bash
# Run specific test class
pytest tests/test_image_utils.py::TestImageProcessor

# Run specific test function
pytest tests/test_validation.py::TestValidationResult::test_success_creation
```

## Test Fixtures

Common fixtures are defined in `conftest.py`:

- `sample_image_bytes` - 100x100 RGB test image
- `sample_large_image_bytes` - 2500x2000 RGB test image (for resize testing)
- `sample_detections` - Mock detection results
- `sample_segments` - Mock segmentation results
- `sample_faces` - Mock face detection results
- `sample_numpy_array` - Random numpy array for testing

## Writing New Tests

When adding new tests:

1. Create test file: `test_<module_name>.py`
2. Use descriptive test class names: `TestClassName`
3. Use descriptive test function names: `test_specific_behavior`
4. Add docstrings explaining what is being tested
5. Use fixtures from `conftest.py` where applicable
6. Mock external dependencies (OpenCV, models, etc.)

Example:
```python
def test_my_feature(sample_image_bytes):
    \"\"\"Test that my feature works correctly\"\"\"
    result = my_function(sample_image_bytes)
    assert result is not None
    assert result.status == "success"
```

## Continuous Integration

These tests should be run:
- Before committing code
- In CI/CD pipeline
- Before deploying to production

## Notes

- Tests use mocking for external dependencies (OpenCV, YOLO models)
- No actual YOLO models need to be loaded to run tests
- Tests focus on refactored code (ValidationResult, ImageProcessor, ImageAnnotator, VideoFrameService, parse_classes)
- All backward compatibility functions are tested
