"""
Test script for agent video detection
Tests the complete workflow: upload video -> agent detects objects
"""
import requests
import sys
from pathlib import Path
import json

# Configuration
BACKEND_URL = "http://localhost:8000"
VIDEO_PATH = "/Users/innox/projects/tmp/object_detection_using_yolo_in_video_and_webcam/test.mp4"


def test_service_health():
    """Check if backend service is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend service is running")
            return True
        else:
            print("❌ Backend service is not healthy")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to backend at {BACKEND_URL}")
        return False
    except Exception as e:
        print(f"❌ Error checking service: {e}")
        return False


def upload_video_and_query(video_path: str, query: str):
    """Upload video and query the agent"""
    print("\n" + "="*70)
    print("Testing Agent Video Detection")
    print("="*70)

    # Check if video exists
    video_file = Path(video_path)
    if not video_file.exists():
        print(f"❌ Video file not found: {video_path}")
        return False

    print(f"\n📹 Video: {video_file.name}")
    print(f"📊 Size: {video_file.stat().st_size / (1024*1024):.2f} MB")

    # Step 1: Upload video and get initial analysis
    print(f"\n🚀 Step 1: Uploading video...")
    try:
        with open(video_path, "rb") as f:
            files = {"video": (video_file.name, f, "video/mp4")}
            data = {"prompt": "This is a video for object detection analysis"}

            response = requests.post(
                f"{BACKEND_URL}/api/vision/analyze",
                files=files,
                data=data,
                timeout=60
            )

            if response.status_code != 200:
                print(f"❌ Failed to upload video: {response.status_code}")
                print(response.text)
                return False

            result = response.json()
            session_id = result["session_id"]
            print(f"✅ Video uploaded successfully")
            print(f"   Session ID: {session_id}")

    except Exception as e:
        print(f"❌ Error uploading video: {e}")
        return False

    # Step 2: Query the agent to detect objects
    print(f"\n🔍 Step 2: Asking agent to detect objects...")
    print(f"   Query: \"{query}\"")

    try:
        data = {
            "session_id": session_id,
            "prompt": query
        }

        response = requests.post(
            f"{BACKEND_URL}/api/agent/chat",
            json=data,
            timeout=120
        )

        if response.status_code != 200:
            print(f"❌ Agent query failed: {response.status_code}")
            print(response.text)
            return False

        result = response.json()
        agent_response = result.get("response", "")

        print(f"\n✅ Agent Response:")
        print("="*70)
        print(agent_response)
        print("="*70)

        # Check if response indicates successful detection
        if "found" in agent_response.lower() or "detected" in agent_response.lower():
            print("\n✅ Test PASSED - Agent successfully detected objects in video")
            return True
        elif "error" in agent_response.lower() or "no video" in agent_response.lower():
            print("\n❌ Test FAILED - Agent encountered an error")
            return False
        else:
            print("\n⚠️  Test uncertain - Check response above")
            return True

    except Exception as e:
        print(f"❌ Error querying agent: {e}")
        return False


def main():
    """Main test function"""
    print("\n🧪 Starting Agent Video Detection Test\n")

    # Check service health
    if not test_service_health():
        print("\nPlease start the backend service first:")
        print("   cd backend")
        print("   uvicorn app.main:app --reload")
        sys.exit(1)

    # Test 1: Detect people in video
    print("\n\n📝 Test 1: Detect people in video")
    success1 = upload_video_and_query(
        VIDEO_PATH,
        "find people in this video"
    )

    # Test 2: Detect cars
    print("\n\n📝 Test 2: Detect cars in video")
    success2 = upload_video_and_query(
        VIDEO_PATH,
        "how many cars are in this video?"
    )

    # Summary
    print("\n\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Test 1 (Detect people): {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"Test 2 (Detect cars): {'✅ PASSED' if success2 else '❌ FAILED'}")

    if success1 and success2:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
