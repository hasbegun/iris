#!/usr/bin/env python3
"""
Download a test image for testing YOLO integration
"""
import requests
from pathlib import Path

def download_test_image():
    """Download a sample image for testing"""

    # Create test-imgs directory
    test_dir = Path("test-imgs")
    test_dir.mkdir(exist_ok=True)

    # Sample image URL (free to use)
    image_url = "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=800"
    output_path = test_dir / "sample.jpg"

    if output_path.exists():
        print(f"✓ Test image already exists: {output_path}")
        return

    print(f"Downloading test image from Unsplash...")

    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            f.write(response.content)

        print(f"✓ Test image downloaded: {output_path}")
        print(f"  Size: {len(response.content) / 1024:.1f} KB")

    except Exception as e:
        print(f"✗ Failed to download test image: {e}")
        print(f"  Please manually place a test image in: {test_dir}/sample.jpg")

if __name__ == "__main__":
    download_test_image()
