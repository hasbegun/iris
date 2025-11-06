#!/usr/bin/env python3
"""
Test annotated image detection
"""
import requests
import json

ML_URL = "http://localhost:9001"

# 1. First test regular detection to see format
print("Testing regular detection...")
with open("test-imgs/cars2.jpg", "rb") as f:
    resp = requests.post(
        f"{ML_URL}/api/detect",
        files={"image": ("cars2.jpg", f, "image/jpeg")},
        data={"confidence": "0.7", "classes": "car"}
    )

if resp.status_code == 200:
    result = resp.json()
    print(f"✓ Detection successful")
    print(f"Status: {result.get('status')}")
    print(f"Count: {result.get('count')}")
    print(f"Detections:")
    for i, det in enumerate(result.get('detections', [])[:2]):  # Show first 2
        print(f"  Detection {i+1}: {json.dumps(det, indent=4)}")
else:
    print(f"✗ Detection failed: {resp.status_code}")
    print(resp.text)

print("\n" + "="*80 + "\n")

# 2. Test annotated detection
print("Testing annotated detection...")
with open("test-imgs/cars2.jpg", "rb") as f:
    resp = requests.post(
        f"{ML_URL}/api/detect-annotated",
        files={"image": ("cars2.jpg", f, "image/jpeg")},
        data={"confidence": "0.7", "classes": "car"}
    )

if resp.status_code == 200 and resp.headers.get('content-type') == 'image/jpeg':
    with open("test-imgs/cars2_annotated.jpg", "wb") as f:
        f.write(resp.content)
    print(f"✓ Annotated image saved ({len(resp.content)} bytes)")
else:
    print(f"✗ Annotation failed: {resp.status_code}")
    print(resp.text)
