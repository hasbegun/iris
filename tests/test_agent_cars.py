#!/usr/bin/env python3
"""
Test agent with image containing cars
"""
import requests
import sys


def test_agent():
    BASE_URL = "http://localhost:9000"

    # 1. Upload image
    print("📸 Uploading street image with cars...")
    with open("test-imgs/cars2.jpg", "rb") as f:
        resp = requests.post(
            f"{BASE_URL}/api/vision/analyze",
            files={"image": ("street.jpg", f, "image/jpeg")},
            data={"prompt": "Upload for testing"}
        )

    if resp.status_code != 200:
        print(f"❌ Upload failed: {resp.text}")
        sys.exit(1)

    session_id = resp.json()["session_id"]
    print(f"✅ Session created: {session_id}\n")

    # 2. Test detection queries
    test_queries = [
        "What do you see in this image?",
        "Find all cars",
        "How many people are there?",
        "Are there any trucks or buses?",
        "Do you see dogs?",
        "Do you see cats?",
    ]

    for query in test_queries:
        print(f"{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}")

        try:
            resp = requests.post(
                f"{BASE_URL}/api/agent/query",
                json={"session_id": session_id, "query": query},
                timeout=120
            )

            if resp.status_code == 200:
                result = resp.json()
                print(f"✅ Status: {result['status']}")
                print(f"Response:\n{result['response']}\n")
            else:
                print(f"❌ Error: {resp.status_code}")
                print(f"{resp.text}\n")

        except Exception as e:
            print(f"❌ Exception: {e}\n")


if __name__ == "__main__":
    test_agent()
