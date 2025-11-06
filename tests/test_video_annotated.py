"""
Test script for YOLO video annotation
Tests the /api/detect-video-annotated endpoint with a sample video
"""
import requests
import sys
from pathlib import Path

# Configuration
ML_SERVICE_URL = "http://localhost:9001"
VIDEO_PATH = "/Users/innox/projects/tmp/object_detection_using_yolo_in_video_and_webcam/test.mp4"
OUTPUT_PATH = "annotated_output.mp4"


def test_video_annotation():
    """Test video annotation endpoint"""
    print("=" * 60)
    print("Testing YOLO Video Annotation")
    print("=" * 60)

    # Check if video file exists
    video_file = Path(VIDEO_PATH)
    if not video_file.exists():
        print(f"❌ Error: Video file not found at {VIDEO_PATH}")
        print("Please provide a valid video file path.")
        return False

    print(f"\n📹 Video file: {video_file.name}")
    print(f"📊 File size: {video_file.stat().st_size / (1024*1024):.2f} MB")

    # Test endpoint
    endpoint = f"{ML_SERVICE_URL}/api/detect-video-annotated"
    print(f"\n🔗 Endpoint: {endpoint}")

    try:
        # Prepare request
        with open(VIDEO_PATH, "rb") as f:
            files = {
                "video": (video_file.name, f, "video/mp4")
            }
            data = {
                "confidence": 0.5,
                "classes": "person",  # Only detect people in this test
                "frame_skip": 0,  # Process all frames for better annotation
                "line_width": 3,
                "font_scale": 0.8
            }

            print("\n⏳ Uploading and processing video...")
            print(f"   Confidence: {data['confidence']}")
            print(f"   Classes: {data['classes']}")
            print(f"   Frame skip: {data['frame_skip']}")
            print(f"   Line width: {data['line_width']}")
            print(f"   Font scale: {data['font_scale']}")

            # Send request
            response = requests.post(
                endpoint,
                files=files,
                data=data,
                timeout=300  # 5 minute timeout for full video processing
            )

            # Check response
            if response.status_code != 200:
                print(f"\n❌ Error: {response.status_code}")
                print(response.text)
                return False

            # Get stats from headers
            total_detections = response.headers.get('X-Total-Detections', 'N/A')
            frames_processed = response.headers.get('X-Frames-Processed', 'N/A')
            processing_time = response.headers.get('X-Processing-Time', 'N/A')

            # Save annotated video
            output_file = Path(OUTPUT_PATH)
            with open(output_file, 'wb') as f:
                f.write(response.content)

            output_size_mb = len(response.content) / (1024*1024)

            print("\n" + "=" * 60)
            print("✅ VIDEO ANNOTATION COMPLETE")
            print("=" * 60)

            print(f"\n📊 Processing Stats:")
            print(f"   Total detections: {total_detections}")
            print(f"   Frames processed: {frames_processed}")
            print(f"   Processing time: {processing_time}s")

            print(f"\n💾 Output:")
            print(f"   File: {output_file.absolute()}")
            print(f"   Size: {output_size_mb:.2f} MB")

            print(f"\n🎬 You can now watch the annotated video:")
            print(f"   open {output_file.absolute()}")

            print("\n" + "=" * 60)
            return True

    except requests.exceptions.ConnectionError:
        print(f"\n❌ Error: Cannot connect to ML service at {ML_SERVICE_URL}")
        print("Make sure the ML service is running:")
        print("   cd ml-service")
        print("   python run.py")
        return False
    except requests.exceptions.Timeout:
        print("\n❌ Error: Request timed out")
        print("Video processing took too long. Try:")
        print("   - Using a shorter video")
        print("   - Increasing frame_skip value")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_service_health():
    """Check if ML service is running"""
    try:
        response = requests.get(f"{ML_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print("\n✅ ML Service is running")
            print(f"   Status: {health['status']}")
            print(f"   Models loaded: {health['models_loaded']}")
            print(f"   Device: {health['device']}")
            return True
        else:
            print("\n❌ ML Service is not healthy")
            return False
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Cannot connect to ML service at {ML_SERVICE_URL}")
        return False
    except Exception as e:
        print(f"\n❌ Error checking service: {e}")
        return False


if __name__ == "__main__":
    print("\n🚀 Starting Video Annotation Test\n")

    # Check service health first
    if not test_service_health():
        print("\nPlease start the ML service first:")
        print("   cd ml-service")
        print("   python run.py")
        sys.exit(1)

    # Test video annotation
    success = test_video_annotation()

    if success:
        print("\n✅ Test passed!")
        sys.exit(0)
    else:
        print("\n❌ Test failed!")
        sys.exit(1)
