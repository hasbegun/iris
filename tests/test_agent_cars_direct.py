#!/usr/bin/env python3
"""
Direct test for car detection with agent
"""
import requests
import sys


def test_agent():
    BASE_URL = "http://localhost:9000"

    # 1. Upload cars2.jpg
    print("📸 Uploading cars2.jpg...")
    with open("test-imgs/cars2.jpg", "rb") as f:
        resp = requests.post(
            f"{BASE_URL}/api/vision/analyze",
            files={"image": ("cars2.jpg", f, "image/jpeg")},
            data={"prompt": "Upload for testing"}
        )

    if resp.status_code != 200:
        print(f"❌ Upload failed: {resp.text}")
        sys.exit(1)

    session_id = resp.json()["session_id"]
    print(f"✅ Session created: {session_id}\n")

    # 2. Test different car detection queries
    test_queries = [
        "can find the cars?",  # User's exact query from Flutter
        "Find all cars",
        "How many cars are there?",
        "Are there any vehicles?",
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
