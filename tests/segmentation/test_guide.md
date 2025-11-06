# Segmentation Testing Guide

## Prerequisites

Ensure both services are running:
- ✅ ML Service: http://localhost:9001
- ✅ Backend: http://localhost:9000

Check ML service health:
```bash
curl http://localhost:9001/health
```

---

## Test 1: Static Image Detection & Segmentation

### A. Object Detection (Bounding Boxes)

**Test with a sample image:**

```bash
# Download a test image
curl -o test_image.jpg "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=800"

# Run detection
curl -X POST http://localhost:9001/api/detect \
  -F "image=@test_image.jpg" \
  -F "confidence=0.5" \
  | jq '.'
```

**Expected Response:**
```json
{
  "status": "success",
  "detections": [
    {
      "class_name": "car",
      "confidence": 0.87,
      "bbox": [100, 200, 400, 500]
    }
  ],
  "count": 1,
  "image_shape": [800, 1200],
  "inference_time_ms": 45.2
}
```

**Test with class filtering:**
```bash
curl -X POST http://localhost:9001/api/detect \
  -F "image=@test_image.jpg" \
  -F "confidence=0.5" \
  -F "classes=car,person" \
  | jq '.detections[].class_name'
```

**Get annotated image with bounding boxes:**
```bash
curl -X POST http://localhost:9001/api/detect-annotated \
  -F "image=@test_image.jpg" \
  -F "confidence=0.5" \
  -o detected_output.jpg

# View the image
open detected_output.jpg  # macOS
```

---

### B. Instance Segmentation (Polygon Masks)

**Run segmentation:**

```bash
curl -X POST http://localhost:9001/api/segment \
  -F "image=@test_image.jpg" \
  -F "confidence=0.5" \
  | jq '.'
```

**Expected Response:**
```json
{
  "status": "success",
  "segments": [
    {
      "class_name": "car",
      "confidence": 0.89,
      "bbox": [100, 200, 400, 500],
      "mask": [[150, 220], [180, 210], [200, 250], ...]
    }
  ],
  "count": 1,
  "image_shape": [800, 1200],
  "inference_time_ms": 52.3
}
```

**Test with class filtering:**
```bash
curl -X POST http://localhost:9001/api/segment \
  -F "image=@test_image.jpg" \
  -F "confidence=0.5" \
  -F "classes=car,person" \
  | jq '.segments[] | {class_name, confidence, mask_points: (.mask | length)}'
```

**Get annotated image with segmentation masks:**
```bash
curl -X POST http://localhost:9001/api/segment-annotated \
  -F "image=@test_image.jpg" \
  -F "confidence=0.5" \
  -F "opacity=0.5" \
  -o segmented_output.jpg

# View the image
open segmented_output.jpg  # macOS
```

**Compare detection vs segmentation:**
```bash
# Side by side
open detected_output.jpg segmented_output.jpg
```

---

## Test 2: Video Detection & Segmentation

### A. Video Object Detection

**Test with a sample video:**

```bash
# Use a short test video (create or download)
# For testing, you can use any MP4 video

curl -X POST http://localhost:9001/api/detect-video \
  -F "video=@test_video.mp4" \
  -F "confidence=0.5" \
  -F "frame_skip=2" \
  | jq '{
    status,
    frames_processed: (.frame_detections | length),
    total_detections: .summary.total_detections,
    classes_found: .summary.unique_classes
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "frames_processed": 30,
  "total_detections": 45,
  "classes_found": ["car", "person", "truck"]
}
```

**Get frame-by-frame details:**
```bash
curl -X POST http://localhost:9001/api/detect-video \
  -F "video=@test_video.mp4" \
  -F "confidence=0.5" \
  | jq '.frame_detections[] | {frame: .frame_number, count: .count}'
```

---

### B. Video Instance Segmentation

**Run video segmentation:**

```bash
curl -X POST http://localhost:9001/api/segment-video \
  -F "video=@test_video.mp4" \
  -F "confidence=0.5" \
  -F "frame_skip=2" \
  | jq '{
    status,
    frames_processed: (.frame_segmentations | length),
    total_segments: .summary.total_detections,
    classes_found: .summary.unique_classes
  }'
```

**Compare processing times:**
```bash
echo "Detection:"
curl -X POST http://localhost:9001/api/detect-video \
  -F "video=@test_video.mp4" \
  -F "confidence=0.5" \
  | jq '.processing_time_seconds'

echo "Segmentation:"
curl -X POST http://localhost:9001/api/segment-video \
  -F "video=@test_video.mp4" \
  -F "confidence=0.5" \
  | jq '.processing_time_seconds'
```

---

## Test 3: Live Video Stream Detection & Segmentation

### Using the Flutter App

**Test through the app UI:**

1. **Launch the Flutter app**
   ```bash
   cd /Users/innox/projects/iris/frontend
   flutter run
   ```

2. **Navigate to Live Camera**
   - From home screen, tap on "Live Camera" or navigate to it

3. **Test Detection Mode (Default)**
   - Tap "Start Detection" button
   - Point camera at objects (cars, people, etc.)
   - Observe **bounding boxes** drawn around detected objects
   - Check status banner shows "Detection" mode
   - Verify inference time is displayed (should be <100ms)

4. **Test Segmentation Mode**
   - Tap the **mode toggle button** (top-right, next to mic icon)
     - Icon changes from `⬜` to `🎨`
   - Tap "Start Segmentation" button
   - Point camera at objects
   - Observe **colored polygon masks** around detected objects
   - Check status banner shows "Segmentation" mode
   - Verify inference time (should be ~10-20% slower than detection)

5. **Test Mode Switching**
   - While segmentation is running, tap mode toggle button
   - Should switch to detection immediately
   - Boxes should replace masks
   - Status should update

6. **Test Class Filtering**
   - Use voice command: "Find cars" or "Find person"
   - Only specified classes should be detected/segmented

### Using curl (Stream Simulation)

**Test stream endpoint with a static image:**

```bash
# Simulate a camera frame
curl -X POST http://localhost:9000/ml/api/detect-stream \
  -F "image=@test_image.jpg" \
  -F "confidence=0.5" \
  | jq '{count, inference_time_ms}'

curl -X POST http://localhost:9000/ml/api/segment-stream \
  -F "image=@test_image.jpg" \
  -F "confidence=0.5" \
  | jq '{count, inference_time_ms}'
```

**Performance benchmark:**
```bash
# Run 10 frames and measure average time
for i in {1..10}; do
  curl -s -X POST http://localhost:9000/ml/api/segment-stream \
    -F "image=@test_image.jpg" \
    -F "confidence=0.5" \
    | jq '.inference_time_ms'
done | awk '{sum+=$1} END {print "Average:", sum/NR, "ms"}'
```

---

## Expected Performance

### Inference Times (on Apple Silicon MPS)

| Mode | Image | Video Frame | Notes |
|------|-------|-------------|-------|
| Detection | 30-50ms | 30-50ms | Fast, bounding boxes only |
| Segmentation | 40-60ms | 40-60ms | ~10-20% slower, polygon masks |

### Frame Rates (Live Stream)

| Mode | FPS | Notes |
|------|-----|-------|
| Detection | 5-10 FPS | Limited by network + processing |
| Segmentation | 3-5 FPS | Slightly slower due to mask processing |

---

## Validation Checklist

### Test 1: Static Image ✓
- [ ] Detection returns bounding boxes
- [ ] Segmentation returns polygon masks
- [ ] Class filtering works
- [ ] Annotated images are generated correctly
- [ ] Masks show transparent colored overlays

### Test 2: Video ✓
- [ ] Video detection processes all frames
- [ ] Video segmentation processes all frames
- [ ] Frame skip parameter works
- [ ] Summary statistics are accurate
- [ ] Processing completes without errors

### Test 3: Live Stream ✓
- [ ] Camera preview works
- [ ] Detection mode draws bounding boxes
- [ ] Segmentation mode draws polygon masks
- [ ] Mode toggle switches correctly
- [ ] Status banner updates
- [ ] Inference time is displayed
- [ ] Performance is acceptable (3-10 FPS)

---

## Troubleshooting

### ML Service Issues
```bash
# Check if ML service is running
curl http://localhost:9001/health

# Check logs
tail -f /path/to/ml-service/logs

# Restart ML service
cd /Users/innox/projects/iris/ml-service
source ~/.zshrc && conda activate iris-ml && python run.py
```

### Backend Issues
```bash
# Check if backend is running
lsof -ti:9000

# Restart backend
cd /Users/innox/projects/iris/backend
# (restart command)
```

### Frontend Issues
```bash
# Clear and rebuild
cd /Users/innox/projects/iris/frontend
flutter clean
flutter pub get
flutter run
```

---

## Sample Test Images

You can download these for testing:

```bash
# Street scene with cars
curl -o street.jpg "https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=800"

# People
curl -o people.jpg "https://images.unsplash.com/photo-1511632765486-a01980e01a18?w=800"

# Mixed objects
curl -o mixed.jpg "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=800"
```

---

## Success Criteria

✅ **All tests pass** with:
- No errors in API responses
- Correct object detection/segmentation
- Acceptable performance (<100ms per frame)
- Smooth mode switching in app
- Clear visual feedback (boxes vs masks)
