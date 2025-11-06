"""
Unit test for Phase 1: Verify Detection Data Structures
Tests that the models and context manager work correctly without needing running services.
"""
import sys
sys.path.insert(0, '/Users/innox/projects/iris/backend')

def test_detection_models():
    """Test that Detection and ImageMetadata models work correctly."""
    print("=" * 60)
    print("Phase 1 Unit Test: Detection Data Structures")
    print("=" * 60)

    print("\n1. Testing Detection model...")
    try:
        from app.models.schemas import Detection, ImageMetadata

        # Create a sample detection
        det = Detection(
            class_name="car",
            confidence=0.89,
            bbox=[120.5, 200.3, 450.2, 380.7]
        )

        print(f"   ✓ Detection model created successfully")
        print(f"     - class_name: {det.class_name}")
        print(f"     - confidence: {det.confidence}")
        print(f"     - bbox: {det.bbox}")

        # Test serialization
        det_dict = det.model_dump()
        print(f"   ✓ Detection serializes to dict: {det_dict}")

    except Exception as e:
        print(f"   ✗ Detection model failed: {e}")
        return False

    print("\n2. Testing ImageMetadata model...")
    try:
        metadata = ImageMetadata(width=1920, height=1080)
        print(f"   ✓ ImageMetadata model created successfully")
        print(f"     - width: {metadata.width}")
        print(f"     - height: {metadata.height}")

        meta_dict = metadata.model_dump()
        print(f"   ✓ ImageMetadata serializes to dict: {meta_dict}")

    except Exception as e:
        print(f"   ✗ ImageMetadata model failed: {e}")
        return False

    print("\n3. Testing AgentAnalyzeResponse with detections...")
    try:
        from app.models.schemas import AgentAnalyzeResponse
        from datetime import datetime

        response = AgentAnalyzeResponse(
            session_id="test-123",
            response="I found 2 cars in the image",
            model_used="llama3",
            processing_time=1.5,
            timestamp=datetime.now(),
            annotated_image_url="/api/images/test.jpg",
            has_annotated_image=True,
            detections=[
                Detection(class_name="car", confidence=0.89, bbox=[100, 200, 300, 400]),
                Detection(class_name="car", confidence=0.85, bbox=[500, 200, 700, 400]),
            ],
            image_metadata=ImageMetadata(width=1920, height=1080)
        )

        print(f"   ✓ AgentAnalyzeResponse created successfully")
        print(f"     - detections: {len(response.detections) if response.detections else 0} objects")
        print(f"     - image_metadata: {response.image_metadata}")

        # Test JSON serialization
        response_dict = response.model_dump()
        print(f"   ✓ Response serializes to dict")
        print(f"     - Keys: {list(response_dict.keys())}")

    except Exception as e:
        print(f"   ✗ AgentAnalyzeResponse failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n4. Testing ContextManager detection storage...")
    try:
        from app.services.context_manager import ContextManager

        cm = ContextManager()
        session_id = cm.create_session()

        print(f"   ✓ Created session: {session_id}")

        # Store detections
        sample_detections = [
            {"class_name": "car", "confidence": 0.89, "bbox": [100, 200, 300, 400]},
            {"class_name": "person", "confidence": 0.92, "bbox": [500, 100, 600, 400]},
        ]
        image_shape = (1080, 1920)  # height, width

        cm.store_detections(session_id, sample_detections, image_shape)
        print(f"   ✓ Stored {len(sample_detections)} detections")

        # Retrieve detections
        retrieved = cm.get_detections(session_id)
        print(f"   ✓ Retrieved detections")
        print(f"     - detections count: {len(retrieved['detections'])}")
        print(f"     - image_shape: {retrieved['image_shape']}")

        # Verify data integrity
        assert len(retrieved['detections']) == 2, "Wrong detection count"
        assert retrieved['image_shape'] == image_shape, "Wrong image shape"
        assert retrieved['detections'][0]['class_name'] == "car", "Wrong class name"

        print(f"   ✓ Data integrity verified")

    except Exception as e:
        print(f"   ✗ ContextManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    print("✓ Detection model: OK")
    print("✓ ImageMetadata model: OK")
    print("✓ AgentAnalyzeResponse with detections: OK")
    print("✓ ContextManager storage: OK")
    print("\n🎉 Phase 1 Data Structures: ALL TESTS PASSED")
    return True

if __name__ == "__main__":
    success = test_detection_models()
    exit(0 if success else 1)
