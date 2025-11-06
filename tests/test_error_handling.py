"""
Test script to verify agent error handling for video detection
Tests that the agent properly handles errors without getting stuck in parsing loops
"""
import requests
import sys

# Configuration
BACKEND_URL = "http://localhost:8000"


def test_video_query_without_upload():
    """
    Test querying for video objects without uploading a video first.
    Should get a clean error message, not a parsing error.
    """
    print("\n" + "="*70)
    print("Test: Video query WITHOUT uploading video (error handling test)")
    print("="*70)

    try:
        # Create a new session and query without uploading any video
        data = {
            "prompt": "find cars in the video"
        }

        print(f"\n🔍 Sending query: \"{data['prompt']}\"")
        print("   (No video uploaded - should get clean error message)")

        response = requests.post(
            f"{BACKEND_URL}/api/agent/chat",
            json=data,
            timeout=30
        )

        if response.status_code != 200:
            print(f"❌ Request failed: {response.status_code}")
            print(response.text)
            return False

        result = response.json()
        agent_response = result.get("response", "")

        print(f"\n📝 Agent Response:")
        print("-"*70)
        print(agent_response)
        print("-"*70)

        # Check for clean error handling (not parsing errors)
        if "parsing" in agent_response.lower() or "invalid format" in agent_response.lower():
            print("\n❌ FAILED - Got parsing error (agent stuck in loop)")
            return False
        elif "no video" in agent_response.lower() or "upload" in agent_response.lower():
            print("\n✅ PASSED - Got clean error message")
            return True
        else:
            print("\n⚠️  UNCERTAIN - Response doesn't clearly indicate error")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


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


def main():
    """Main test function"""
    print("\n🧪 Testing Agent Error Handling\n")

    # Check service health
    if not test_service_health():
        print("\nPlease start the backend service first:")
        print("   cd backend")
        print("   uvicorn app.main:app --reload")
        sys.exit(1)

    # Run the test
    success = test_video_query_without_upload()

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    if success:
        print("✅ Error handling test PASSED")
        print("   Agent correctly handles missing video without parsing errors")
        sys.exit(0)
    else:
        print("❌ Error handling test FAILED")
        print("   Agent may be stuck in parsing loop or not handling errors properly")
        sys.exit(1)


if __name__ == "__main__":
    main()
