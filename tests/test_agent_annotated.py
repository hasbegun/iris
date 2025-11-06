#!/usr/bin/env python3
"""
Test agent with annotated image response
"""
import requests
import json

BASE_URL = "http://localhost:9000"

def test_annotated_workflow():
    print("="*80)
    print("Testing Agent with Annotated Image Response")
    print("="*80)
    print()

    # 1. Upload image with cars
    print("1. Uploading cars2.jpg...")
    with open("test-imgs/cars2.jpg", "rb") as f:
        resp = requests.post(
            f"{BASE_URL}/api/vision/analyze",
            files={"image": ("cars2.jpg", f, "image/jpeg")},
            data={"prompt": "Upload for testing"}
        )

    if resp.status_code != 200:
        print(f"   ✗ Upload failed: {resp.text}")
        return

    session_id = resp.json()["session_id"]
    print(f"   ✓ Session created: {session_id}")
    print()

    # 2. Query without annotation
    print("2. Query WITHOUT annotation: 'Find all cars'")
    resp = requests.post(
        f"{BASE_URL}/api/agent/query",
        json={
            "session_id": session_id,
            "query": "Find all cars",
            "annotate": False
        },
        timeout=120
    )

    if resp.status_code == 200:
        result = resp.json()
        print(f"   ✓ Response: {result['response']}")
        print(f"   ✓ Annotated image URL: {result.get('annotated_image_url', 'None')}")
    else:
        print(f"   ✗ Failed: {resp.status_code} - {resp.text}")
    print()

    # 3. Query WITH annotation
    print("3. Query WITH annotation: 'can find the cars?'")
    resp = requests.post(
        f"{BASE_URL}/api/agent/query",
        json={
            "session_id": session_id,
            "query": "can find the cars?",
            "annotate": True
        },
        timeout=120
    )

    if resp.status_code == 200:
        result = resp.json()
        print(f"   ✓ Response: {result['response']}")
        print(f"   ✓ Annotated image URL: {result.get('annotated_image_url')}")

        # Download and save the annotated image
        if result.get('annotated_image_url'):
            annotated_url = f"{BASE_URL}{result['annotated_image_url']}"
            print(f"   ✓ Downloading from: {annotated_url}")

            img_resp = requests.get(annotated_url)
            if img_resp.status_code == 200:
                with open("test-imgs/agent_annotated_result.jpg", "wb") as f:
                    f.write(img_resp.content)
                print(f"   ✓ Saved annotated image: test-imgs/agent_annotated_result.jpg ({len(img_resp.content)} bytes)")
            else:
                print(f"   ✗ Failed to download annotated image: {img_resp.status_code}")
    else:
        print(f"   ✗ Failed: {resp.status_code} - {resp.text}")
    print()

    # 4. Test with people counting
    print("4. Testing with kid1.jpg (people detection)")
    with open("test-imgs/kid1.jpg", "rb") as f:
        resp = requests.post(
            f"{BASE_URL}/api/vision/analyze",
            files={"image": ("kid1.jpg", f, "image/jpeg")},
            data={"prompt": "Upload"}
        )

    session_id2 = resp.json()["session_id"]
    print(f"   ✓ Session created: {session_id2}")

    resp = requests.post(
        f"{BASE_URL}/api/agent/query",
        json={
            "session_id": session_id2,
            "query": "How many people are there?",
            "annotate": True
        },
        timeout=120
    )

    if resp.status_code == 200:
        result = resp.json()
        print(f"   ✓ Response: {result['response']}")
        print(f"   ✓ Annotated image URL: {result.get('annotated_image_url', 'None')}")
    else:
        print(f"   ✗ Failed: {resp.status_code}")
    print()

    print("="*80)
    print("Test Complete!")
    print("="*80)


if __name__ == "__main__":
    test_annotated_workflow()
