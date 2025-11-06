"""
Quick test for video validation
Tests that video size limits are working correctly
"""
import requests
import io

BASE_URL = "http://localhost:9001"

def test_small_video_file():
    """Test that small 'video' file passes validation"""
    print("\n🧪 Test 1: Small video file (5MB)")

    # Create 5MB of dummy data with .mp4 extension
    dummy_video = b"x" * (5 * 1024 * 1024)

    files = {
        'image': ('test.mp4', io.BytesIO(dummy_video), 'video/mp4')
    }
    data = {
        'confidence': 0.5
    }

    response = requests.post(
        f"{BASE_URL}/api/detect-faces",
        files=files,
        data=data
    )

    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response: {response.text}")
        print("❌ FAILED: Should accept 5MB video")
    else:
        print("✅ PASSED: 5MB video accepted")

    return response.status_code == 200


def test_medium_video_file():
    """Test that medium 'video' file (30MB) passes validation"""
    print("\n🧪 Test 2: Medium video file (30MB)")

    # Create 30MB of dummy data
    dummy_video = b"x" * (30 * 1024 * 1024)

    files = {
        'image': ('test.mp4', io.BytesIO(dummy_video), 'video/mp4')
    }
    data = {
        'confidence': 0.5
    }

    response = requests.post(
        f"{BASE_URL}/api/detect-faces",
        files=files,
        data=data
    )

    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response: {response.text[:200]}")
        print("❌ FAILED: Should accept 30MB video")
    else:
        print("✅ PASSED: 30MB video accepted")

    return response.status_code == 200


def test_large_video_file():
    """Test that large 'video' file (60MB) is rejected"""
    print("\n🧪 Test 3: Large video file (60MB) - should REJECT")

    # Create 60MB of dummy data
    dummy_video = b"x" * (60 * 1024 * 1024)

    files = {
        'image': ('test.mp4', io.BytesIO(dummy_video), 'video/mp4')
    }
    data = {
        'confidence': 0.5
    }

    response = requests.post(
        f"{BASE_URL}/api/detect-faces",
        files=files,
        data=data
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")

    if response.status_code == 400 and "too large" in response.text.lower():
        print("✅ PASSED: 60MB video correctly rejected")
        return True
    else:
        print("❌ FAILED: Should reject 60MB video")
        return False


def test_image_on_detect_endpoint():
    """Test that /api/detect still rejects videos"""
    print("\n🧪 Test 4: Video to /api/detect endpoint - should REJECT")

    # Create 5MB video file
    dummy_video = b"x" * (5 * 1024 * 1024)

    files = {
        'image': ('test.mp4', io.BytesIO(dummy_video), 'video/mp4')
    }
    data = {
        'confidence': 0.7
    }

    response = requests.post(
        f"{BASE_URL}/api/detect",
        files=files,
        data=data
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")

    # /api/detect should only accept images
    if response.status_code == 400:
        print("✅ PASSED: /api/detect correctly rejects videos")
        return True
    else:
        print("❌ FAILED: /api/detect should reject videos")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("VIDEO VALIDATION TESTS")
    print("=" * 60)

    results = []

    try:
        results.append(("Small video (5MB)", test_small_video_file()))
        results.append(("Medium video (30MB)", test_medium_video_file()))
        results.append(("Large video (60MB - reject)", test_large_video_file()))
        results.append(("Video to image endpoint", test_image_on_detect_endpoint()))

        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)

        for name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}: {name}")

        all_passed = all(result[1] for result in results)

        if all_passed:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print("\n⚠️  SOME TESTS FAILED")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
