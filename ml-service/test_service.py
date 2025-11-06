"""
Simple test script for ML Service
Tests the endpoints with a sample image
"""
import requests
import sys
from pathlib import Path


def test_ml_service(image_path: str, base_url: str = "http://localhost:8001"):
    """
    Test ML service endpoints

    Args:
        image_path: Path to test image
        base_url: ML service base URL
    """
    print(f"🧪 Testing ML Service at {base_url}")
    print(f"📸 Using image: {image_path}\n")

    if not Path(image_path).exists():
        print(f"❌ Error: Image file not found: {image_path}")
        return False

    # Test health endpoint
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        response.raise_for_status()
        health = response.json()
        print(f"   ✅ Status: {health['status']}")
        print(f"   ✅ Models loaded: {health['models_loaded']}")
        print(f"   ✅ Device: {health['device']}\n")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}\n")
        return False

    # Test object detection
    print("2. Testing object detection...")
    try:
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {'confidence': 0.5}
            response = requests.post(f"{base_url}/api/detect", files=files, data=data)
            response.raise_for_status()
            result = response.json()

        print(f"   ✅ Detected {result['count']} objects")
        print(f"   ⏱️  Inference time: {result['inference_time_ms']}ms")

        if result['detections']:
            print(f"   📦 Objects found:")
            for det in result['detections'][:5]:  # Show first 5
                print(f"      - {det['class_name']}: {det['confidence']:.2f}")
        print()
    except Exception as e:
        print(f"   ❌ Detection failed: {e}\n")

    # Test segmentation
    print("3. Testing segmentation...")
    try:
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {'confidence': 0.5}
            response = requests.post(f"{base_url}/api/segment", files=files, data=data)
            response.raise_for_status()
            result = response.json()

        print(f"   ✅ Segmented {result['count']} objects")
        print(f"   ⏱️  Inference time: {result['inference_time_ms']}ms\n")
    except Exception as e:
        print(f"   ❌ Segmentation failed: {e}\n")

    # Test face detection
    print("4. Testing face detection...")
    try:
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {'confidence': 0.5}
            response = requests.post(f"{base_url}/api/detect-faces", files=files, data=data)
            response.raise_for_status()
            result = response.json()

        print(f"   ✅ Detected {result['count']} face(s)")
        print(f"   ⏱️  Inference time: {result['inference_time_ms']}ms\n")
    except Exception as e:
        print(f"   ❌ Face detection failed: {e}\n")

    # Test metrics
    print("5. Testing metrics endpoint...")
    try:
        response = requests.get(f"{base_url}/metrics")
        response.raise_for_status()
        metrics = response.json()
        print(f"   ✅ Total requests: {metrics['total_requests']}")
        print(f"   ✅ Avg inference time: {metrics['avg_inference_time_ms']}ms")
        print(f"   ✅ Memory usage: {metrics['memory_usage_mb']}MB\n")
    except Exception as e:
        print(f"   ❌ Metrics failed: {e}\n")

    print("✅ All tests completed!")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_service.py <path_to_image>")
        print("Example: python test_service.py test.jpg")
        sys.exit(1)

    image_path = sys.argv[1]
    test_ml_service(image_path)
