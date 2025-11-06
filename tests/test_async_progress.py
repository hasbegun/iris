"""
Test script for async video processing with progress tracking
Demonstrates real-time progress monitoring
"""
import requests
import time
import sys
from pathlib import Path

# Configuration
ML_SERVICE_URL = "http://localhost:9001"
VIDEO_PATH = "/Users/innox/projects/tmp/object_detection_using_yolo_in_video_and_webcam/test.mp4"


def draw_progress_bar(progress: float, width: int = 50) -> str:
    """Draw a simple progress bar"""
    filled = int(width * progress)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {progress*100:.1f}%"


def test_async_processing():
    """Test async video processing with progress tracking"""
    print("=" * 70)
    print("Testing Async Video Processing with Progress Tracking")
    print("=" * 70)

    # Check if video file exists
    video_file = Path(VIDEO_PATH)
    if not video_file.exists():
        print(f"❌ Error: Video file not found at {VIDEO_PATH}")
        return False

    print(f"\n📹 Video file: {video_file.name}")
    print(f"📊 File size: {video_file.stat().st_size / (1024*1024):.2f} MB")

    # Step 1: Submit task
    print("\n🚀 Step 1: Submitting video for async processing...")
    endpoint = f"{ML_SERVICE_URL}/api/detect-video-async"

    try:
        with open(VIDEO_PATH, "rb") as f:
            files = {"video": (video_file.name, f, "video/mp4")}
            data = {
                "confidence": 0.5,
                "classes": "person",
                "frame_skip": 0,
                "line_width": 3,
                "font_scale": 0.8
            }

            response = requests.post(endpoint, files=files, data=data, timeout=30)

            if response.status_code != 200:
                print(f"❌ Error submitting task: {response.status_code}")
                print(response.text)
                return False

            result = response.json()
            task_id = result["task_id"]
            status_url = f"{ML_SERVICE_URL}{result['status_url']}"

            print(f"✅ Task submitted successfully!")
            print(f"   Task ID: {task_id}")
            print(f"   Status URL: {status_url}")

    except Exception as e:
        print(f"❌ Error submitting task: {e}")
        return False

    # Step 2: Poll for progress
    print(f"\n📊 Step 2: Monitoring progress...")
    print()

    last_status = None
    start_time = time.time()

    while True:
        try:
            # Get task status
            response = requests.get(status_url, timeout=5)
            if response.status_code != 200:
                print(f"❌ Error getting status: {response.status_code}")
                return False

            status = response.json()

            # Only update if status changed
            if status != last_status:
                # Clear previous line and draw progress
                print(f"\r\033[K", end="")  # Clear line

                progress = status["progress"]
                current = status["current_frame"]
                total = status["total_frames"]
                task_status = status["status"]
                message = status["message"]
                elapsed = status["elapsed_time"]

                # Draw progress bar
                progress_bar = draw_progress_bar(progress)

                if task_status == "processing":
                    print(f"⏳ {progress_bar} | Frame {current}/{total} | {elapsed:.1f}s", end="", flush=True)
                elif task_status == "completed":
                    print(f"\r\033[K✅ {progress_bar} | Completed in {elapsed:.1f}s")
                    break
                elif task_status == "failed":
                    print(f"\r\033[K❌ Task failed: {status.get('error', 'Unknown error')}")
                    return False
                elif task_status == "pending":
                    print(f"⏳ Waiting to start...")

                last_status = status

            # Wait before next poll
            time.sleep(0.5)

            # Timeout after 5 minutes
            if time.time() - start_time > 300:
                print("\n⏰ Timeout waiting for task to complete")
                return False

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Error polling status: {e}")
            return False

    # Step 3: Get final result
    print(f"\n📊 Step 3: Getting final result...")
    try:
        response = requests.get(status_url, timeout=5)
        if response.status_code != 200:
            print(f"❌ Error getting final result: {response.status_code}")
            return False

        final_status = response.json()
        result = final_status.get("result", {})

        if result:
            stats = result.get("stats", {})

            print("\n" + "=" * 70)
            print("✅ PROCESSING COMPLETE")
            print("=" * 70)

            print(f"\n📹 Video Info:")
            video_info = stats.get("video_info", {})
            print(f"   Total frames: {video_info.get('total_frames', 'N/A')}")
            print(f"   FPS: {video_info.get('fps', 'N/A')}")
            print(f"   Duration: {video_info.get('duration_seconds', 'N/A')}s")
            print(f"   Resolution: {video_info.get('resolution', 'N/A')}")

            print(f"\n📊 Detection Stats:")
            print(f"   Total detections: {stats.get('total_detections', 0)}")
            print(f"   Frames processed: {stats.get('frames_processed', 0)}")
            print(f"   Frames with detections: {stats.get('frames_with_detections', 0)}")
            print(f"   Processing time: {stats.get('processing_time_seconds', 0):.2f}s")

            print(f"\n🏷️  Detections by Class:")
            for class_name, count in stats.get('detections_by_class', {}).items():
                print(f"   {class_name}: {count}")

            print(f"\n💾 Output Size: {result.get('output_size_mb', 0):.2f} MB")

            print("\n" + "=" * 70)

        return True

    except Exception as e:
        print(f"❌ Error getting final result: {e}")
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
    print("\n🚀 Starting Async Video Processing Test\n")

    # Check service health first
    if not test_service_health():
        print("\nPlease start the ML service first:")
        print("   cd ml-service")
        print("   python run.py")
        sys.exit(1)

    # Test async processing
    success = test_async_processing()

    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)
