# 🚀 Quick Start Testing Guide

## Run All Tests

```bash
cd /Users/innox/projects/iris/tests/segmentation
./run_tests.sh
```

---

## Manual Testing

### 1️⃣  Test Static Image (Fastest)

```bash
cd /Users/innox/projects/iris/tests/segmentation

# Detection
curl -X POST http://localhost:9001/api/detect \
  -F "image=@test_image.jpg" \
  -F "confidence=0.5" | jq

# Segmentation
curl -X POST http://localhost:9001/api/segment \
  -F "image=@test_image.jpg" \
  -F "confidence=0.5" | jq

# View annotated images
curl -X POST http://localhost:9001/api/detect-annotated \
  -F "image=@test_image.jpg" -F "confidence=0.5" -o detected.jpg

curl -X POST http://localhost:9001/api/segment-annotated \
  -F "image=@test_image.jpg" -F "confidence=0.5" -F "opacity=0.5" -o segmented.jpg

open detected.jpg segmented.jpg
```

### 2️⃣  Test Video (If you have a video file)

```bash
# Detection
curl -X POST http://localhost:9001/api/detect-video \
  -F "video=@your_video.mp4" \
  -F "confidence=0.5" | jq

# Segmentation
curl -X POST http://localhost:9001/api/segment-video \
  -F "video=@your_video.mp4" \
  -F "confidence=0.5" | jq
```

### 3️⃣  Test Live Camera (Using Flutter App)

```bash
# Start the app
cd /Users/innox/projects/iris/frontend
flutter run
```

**In the app:**
1. Navigate to **Live Camera**
2. Tap the **mode toggle button** (⬜/🎨 icon, top-right)
3. Tap **"Start Detection"** or **"Start Segmentation"**
4. Point camera at objects

---

## Endpoints Summary

| Endpoint | Purpose | Input | Output |
|----------|---------|-------|--------|
| `/api/detect` | Static image detection | Image | Bounding boxes |
| `/api/segment` | Static image segmentation | Image | Polygon masks |
| `/api/detect-stream` | Live camera detection | Frame | Bounding boxes (fast) |
| `/api/segment-stream` | Live camera segmentation | Frame | Polygon masks (fast) |
| `/api/detect-video` | Video detection | Video | Frame-by-frame boxes |
| `/api/segment-video` | Video segmentation | Video | Frame-by-frame masks |
| `/api/detect-annotated` | Get annotated image | Image | JPEG with boxes |
| `/api/segment-annotated` | Get annotated image | Image | JPEG with masks |

---

## Expected Results

### Detection Output
```json
{
  "status": "success",
  "detections": [{
    "class_name": "car",
    "confidence": 0.87,
    "bbox": [100, 200, 400, 500]
  }],
  "count": 1,
  "inference_time_ms": 30.5
}
```

### Segmentation Output
```json
{
  "status": "success",
  "segments": [{
    "class_name": "car",
    "confidence": 0.89,
    "bbox": [100, 200, 400, 500],
    "mask": [[150, 220], [180, 210], ...]
  }],
  "count": 1,
  "inference_time_ms": 45.2
}
```

---

## Performance Targets

- **Detection**: 20-50ms per frame
- **Segmentation**: 30-60ms per frame (10-20% slower)
- **Live Stream**: 3-10 FPS

---

## Troubleshooting

### Services Not Running
```bash
# Check ML service
curl http://localhost:9001/health

# If not running, start it:
cd /Users/innox/projects/iris/ml-service
source ~/.zshrc && conda activate iris-ml && python run.py
```

### No Objects Detected
- Try a different image with clear objects (cars, people, etc.)
- Lower confidence threshold: `confidence=0.3`
- Check image is valid: `file test_image.jpg`

### App Not Showing Overlays
- Make sure you tapped "Start Detection" or "Start Segmentation"
- Check camera permissions are granted
- Verify backend is running on port 9000

---

## Next Steps

1. ✅ Run automated tests: `./run_tests.sh`
2. 📸 Test with your own images
3. 🎥 Test with your own videos
4. 📱 Test live camera in the app
5. 🎨 Compare detection (boxes) vs segmentation (masks)

---

For detailed documentation, see: [test_guide.md](test_guide.md)
