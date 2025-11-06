"""
Test script for YOLO video detection
Tests the /api/detect-video endpoint with a sample video
"""
import requests
import json
import sys
from pathlib import Path

# Configuration
ML_SERVICE_URL = "http://localhost:9001"
VIDEO_PATH = "/Users/innox/projects/tmp/object_detection_using_yolo_in_video_and_webcam/test.mp4"


def test_video_detection():
    """Test video object detection endpoint"""
    print("=" * 60)
    print("Testing YOLO Video Detection")
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
    endpoint = f"{ML_SERVICE_URL}/api/detect-video"
    print(f"\n🔗 Endpoint: {endpoint}")

    try:
        # Prepare request
        with open(VIDEO_PATH, "rb") as f:
            files = {
                "video": (video_file.name, f, "video/mp4")
            }
            data = {
                "confidence": 0.5,
                "classes": "car,person,truck",  # Optional: specify classes
                "frame_skip": 2  # Process every 3rd frame for speed
            }

            print("\n⏳ Uploading and processing video...")
            print(f"   Confidence: {data['confidence']}")
            print(f"   Classes: {data['classes']}")
            print(f"   Frame skip: {data['frame_skip']}")

            # Send request
            response = requests.post(
                endpoint,
                files=files,
                data=data,
                timeout=120  # 2 minute timeout
            )

            # Check response
            if response.status_code != 200:
                print(f"\n❌ Error: {response.status_code}")
                print(response.text)
                return False

            # Parse results
            result = response.json()

            print("\n" + "=" * 60)
            print("✅ VIDEO PROCESSING COMPLETE")
            print("=" * 60)

            # Video info
            video_info = result["video_info"]
            print("\n📹 Video Information:")
            print(f"   Total frames: {video_info['total_frames']}")
            print(f"   FPS: {video_info['fps']}")
            print(f"   Duration: {video_info['duration_seconds']:.2f}s")
            print(f"   Resolution: {video_info['resolution'][0]}x{video_info['resolution'][1]}")

            # Processing stats
            print(f"\n⚡ Processing Stats:")
            print(f"   Processing time: {result['processing_time_seconds']:.2f}s")
            print(f"   Avg processing FPS: {result['avg_fps']:.2f}")
            print(f"   Frames processed: {len(result['frame_detections'])}")

            # Summary
            summary = result["summary"]
            print(f"\n📊 Detection Summary:")
            print(f"   Total detections: {summary['total_detections']}")
            print(f"   Unique classes: {', '.join(summary['unique_classes'])}")
            print(f"   Frames with detections: {summary['frames_with_detections']}")
            print(f"   Frames without detections: {summary['frames_without_detections']}")
            print(f"   Avg detections per frame: {summary['avg_detections_per_frame']:.2f}")
            print(f"   Max detections in frame: {summary['max_detections_in_frame']} (frame #{summary['frame_with_most_objects']})")

            # Detections by class
            print(f"\n🏷️  Detections by Class:")
            for class_name, count in summary["detections_by_class"].items():
                print(f"   {class_name}: {count}")

            # Show first few frames with detections
            print(f"\n🎬 Sample Frame Detections (first 3 frames with objects):")
            frames_shown = 0
            for frame_det in result["frame_detections"]:
                if frame_det["count"] > 0:
                    print(f"\n   Frame #{frame_det['frame_number']} (t={frame_det['timestamp']:.2f}s):")
                    print(f"   Found {frame_det['count']} object(s):")
                    for det in frame_det["detections"][:3]:  # Show max 3 per frame
                        print(f"      - {det['class_name']} ({det['confidence']:.2f})")
                    if len(frame_det["detections"]) > 3:
                        print(f"      ... and {len(frame_det['detections']) - 3} more")
                    frames_shown += 1
                    if frames_shown >= 3:
                        break

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
    print("\n🚀 Starting Video Detection Test\n")

    # Check service health first
    if not test_service_health():
        print("\nPlease start the ML service first:")
        print("   cd ml-service")
        print("   python run.py")
        sys.exit(1)

    # Test video detection
    success = test_video_detection()

    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)
