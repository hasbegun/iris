#!/usr/bin/env python3
"""
Test script for the unified /api/agent/analyze endpoint.
This endpoint accepts image + prompt in a single request (like Flutter does).
"""
import requests
import sys
from pathlib import Path

# Configuration
BACKEND_URL = "http://localhost:9000"
AGENT_ANALYZE_URL = f"{BACKEND_URL}/api/agent/analyze"

def test_agent_analyze(image_path: str, prompt: str):
    """Test the unified agent analyze endpoint."""
    print(f"\n{'='*60}")
    print(f"Testing /api/agent/analyze endpoint")
    print(f"{'='*60}")
    print(f"Image: {image_path}")
    print(f"Prompt: {prompt}")
    print(f"{'='*60}\n")

    # Check if image exists
    if not Path(image_path).exists():
        print(f"❌ Error: Image file not found: {image_path}")
        return False

    try:
        # Prepare the request (same format as Flutter)
        with open(image_path, 'rb') as f:
            files = {
                'image': ('image.jpg', f, 'image/jpeg')
            }
            data = {
                'prompt': prompt,
                # session_id is optional - backend will generate one if not provided
            }

            print("📤 Sending request to backend...")
            response = requests.post(
                AGENT_ANALYZE_URL,
                files=files,
                data=data,
                timeout=60
            )

        print(f"📊 Status Code: {response.status_code}\n")

        if response.status_code == 200:
            result = response.json()
            print("✅ Success! Agent Response:")
            print(f"{'='*60}")
            print(f"Session ID: {result.get('session_id', 'N/A')}")
            print(f"Model Used: {result.get('model_used', 'N/A')}")
            print(f"Processing Time: {result.get('processing_time', 0):.2f}s")
            print(f"\nResponse:")
            print("-" * 60)
            print(result.get('response', 'No response'))
            print(f"{'='*60}\n")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}\n")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to backend. Is it running?")
        print(f"   Expected at: {BACKEND_URL}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    # Test cases
    test_cases = [
        ("test-imgs/boxplt.jpg", "How many cars are in this image?"),
        ("test-imgs/boxplt.jpg", "What objects can you see?"),
        ("test-imgs/boxplt.jpg", "Describe this image"),
    ]

    # Allow custom test from command line
    if len(sys.argv) >= 2:
        image = sys.argv[1]
        prompt = sys.argv[2] if len(sys.argv) >= 3 else "Describe this image"
        test_cases = [(image, prompt)]

    print(f"\n🚀 Testing Agent Analyze Endpoint")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Endpoint: /api/agent/analyze")
    print(f"\nThis endpoint is now used by Flutter for all image analysis.")

    results = []
    for image_path, prompt in test_cases:
        success = test_agent_analyze(image_path, prompt)
        results.append(success)

    # Summary
    print(f"\n{'='*60}")
    print(f"Test Summary")
    print(f"{'='*60}")
    print(f"Total tests: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")
    print(f"{'='*60}\n")

    return all(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
