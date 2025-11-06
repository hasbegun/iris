# Segmentation Feature - Proper Incremental Plan

## What Went Wrong

We jumped ahead to Phase 3 (live camera segmentation) and broke the working object detection feature. The incremental approach was ignored.

### Key Mistakes:
1. Modified `live_camera_provider.dart` to add mode switching before proving static image worked
2. Changed API endpoint from `/ml/api/detect-stream` to `/api/detect-stream`
3. Added UI controls for segmentation mode before basic functionality was tested
4. Broke working live detection in favor of incomplete segmentation feature

### Rollback Completed ✅
- Restored `live_camera_provider.dart` to working version (240 lines)
- Removed mode toggle from `live_camera_widget.dart`
- Removed segmentation control panel from live camera
- Restored correct `/ml/api/detect-stream` endpoint
- Live object detection should work again

---

## The RIGHT Incremental Approach

### Foundation (Already Done) ✅
- API endpoints exist: `/api/detect`, `/api/segment`, `/api/detect-annotated`, `/api/segment-annotated`
- Streaming endpoints exist: `/ml/api/detect-stream`, `/ml/api/segment-stream`
- Data models created: `DetectionResponse`, `SegmentationResponse`, `Segment`
- UI components ready: `InteractiveSegmentationOverlay`, `SegmentationControlPanel`
- Test script validates all endpoints work: `test_frontend_integration.sh`

---

## Phase 1: Static Image Segmentation 📸

**Goal**: Add segmentation option to static image analysis (camera roll, file picker)

### Current State:
- ✅ Backend API working (`/api/segment`)
- ✅ Models parse responses correctly (`SegmentationResponse`)
- ✅ UI components built (`InteractiveSegmentationOverlay`, `SegmentationControlPanel`)
- ❌ NOT integrated into app UI

### What To Do:
**File**: `/Users/innox/projects/iris/frontend/lib/features/home/presentation/widgets/response_display.dart`

Currently this file only shows **detections** (bounding boxes). We need to add **segmentation** option.

#### Step 1.1: Update response_display.dart state
```dart
// Add to _ResponseDisplayState class
VisualizationMode _visualizationMode = VisualizationMode.detection; // NEW

// Existing segmentation controls (already there)
double _minConfidence = 0.0;
Set<String> _filteredClasses = {};
double _opacity = 0.5;
bool _fillStyle = true;
bool _showLabels = true;
```

#### Step 1.2: Add mode toggle to header
```dart
// In _buildVisualizationHeader, add a toggle button:
// [Detection] [Segmentation]
// Only show if response.hasSegments is true
```

#### Step 1.3: Build segmentation visualization
```dart
Widget _buildSegmentationVisualization(BuildContext context) {
  if (!widget.response.hasSegments) return Container();

  return InteractiveSegmentationOverlay(
    imageBytes: widget.imageBytes!,
    segments: widget.response.segments!,
    imageMetadata: widget.response.imageMetadata!,
    minConfidence: _minConfidence,
    filteredClasses: _filteredClasses,
    showLabels: _showLabels,
    opacity: _opacity,
    fillStyle: _fillStyle,
  );
}
```

#### Step 1.4: Add SegmentationControlPanel
```dart
// Only show when _visualizationMode == VisualizationMode.segmentation
if (_visualizationMode == VisualizationMode.segmentation)
  SegmentationControlPanel(
    segments: widget.response.segments!,
    minConfidence: _minConfidence,
    filteredClasses: _filteredClasses,
    showLabels: _showLabels,
    opacity: _opacity,
    fillStyle: _fillStyle,
    onConfidenceChanged: (val) => setState(() => _minConfidence = val),
    onFilteredClassesChanged: (classes) => setState(() => _filteredClasses = classes),
    onShowLabelsChanged: (val) => setState(() => _showLabels = val),
    onOpacityChanged: (val) => setState(() => _opacity = val),
    onFillStyleChanged: (val) => setState(() => _fillStyle = val),
    isCollapsed: _isPanelCollapsed,
    onToggleCollapse: () => setState(() => _isPanelCollapsed = !_isPanelCollapsed),
  )
```

### Testing Phase 1:
1. Take photo or pick from gallery
2. Process with vision service
3. Toggle between Detection and Segmentation views
4. Adjust controls (opacity, confidence, filters)
5. Verify interactive tap-to-select works
6. Test on multiple images with different objects

### Success Criteria:
- [ ] User can toggle between detection and segmentation for static images
- [ ] Segmentation masks render correctly
- [ ] Control panel updates visualization in real-time
- [ ] Tap-to-select works (selects individual segments)
- [ ] Performance is acceptable (<100ms to render)

**Estimated Time**: 2-3 hours
**Risk Level**: Low (doesn't affect existing features)

---

## Phase 2: Video Segmentation 🎥

**Goal**: Add segmentation support for video analysis

### Prerequisites:
- Phase 1 complete and tested
- Video analysis already works for detection

### What To Do:
**Files**:
- `/Users/innox/projects/iris/frontend/lib/features/home/presentation/widgets/video_frame_slideshow.dart`
- Backend video processing code (if needed)

#### Step 2.1: Check backend video segmentation support
```bash
# Test if backend can segment video frames
curl -X POST http://localhost:9001/ml/api/segment-video \
  -F "video=@test_video.mp4" \
  -F "confidence=0.5"
```

#### Step 2.2: Update video frame slideshow
- Add mode toggle (Detection vs Segmentation)
- Render segmentation masks on video frames
- Reuse `SegmentationControlPanel` from Phase 1

### Testing Phase 2:
1. Upload test video
2. Process with vision service
3. Toggle between detection and segmentation
4. Scrub through frames, verify masks render correctly
5. Test different video lengths and resolutions

### Success Criteria:
- [ ] Video frames show segmentation masks
- [ ] Frame navigation works smoothly
- [ ] Mode toggle switches between detection/segmentation
- [ ] Control panel adjusts all frames consistently

**Estimated Time**: 3-4 hours
**Risk Level**: Medium (video processing can be complex)

---

## Phase 3: Live Camera Segmentation 📹

**Goal**: Add segmentation mode to live camera feed

### Prerequisites:
- Phase 1 complete and tested
- Phase 2 complete and tested
- Live object detection working (restored)

### What To Do:
**Files**:
- `/Users/innox/projects/iris/frontend/lib/features/home/providers/live_camera_provider.dart`
- `/Users/innox/projects/iris/frontend/lib/features/home/presentation/widgets/live_camera_widget.dart`

#### Step 3.1: Add mode to live_camera_provider.dart
```dart
enum DetectionMode { detection, segmentation }

class LiveCameraState {
  // Add:
  final DetectionMode mode;
  final List<Segment> segments; // for segmentation mode

  // Segmentation control state
  final double minConfidence;
  final Set<String> filteredClasses;
  final bool showLabels;
  final double opacity;
  final bool fillStyle;
}
```

#### Step 3.2: Update processFrame() to call correct endpoint
```dart
// Choose endpoint based on mode
final endpoint = state.mode == DetectionMode.detection
    ? '/ml/api/detect-stream'
    : '/ml/api/segment-stream';

// Parse response based on mode
if (state.mode == DetectionMode.segmentation) {
  final segments = /* parse segments */;
  state = state.copyWith(segments: segments, detections: []);
} else {
  final detections = /* parse detections */;
  state = state.copyWith(detections: detections, segments: []);
}
```

#### Step 3.3: Add mode toggle to live_camera_widget.dart
```dart
// AppBar action:
IconButton(
  icon: Icon(isSegmentation ? Icons.colorize : Icons.crop_square),
  onPressed: () => ref.read(liveCameraProvider.notifier).toggleMode(),
)
```

#### Step 3.4: Conditionally render overlay
```dart
if (_isDetecting && liveCameraState.hasDetections)
  liveCameraState.mode == DetectionMode.segmentation
      ? LiveSegmentationOverlay(
          segments: liveCameraState.segments,
          imageMetadata: liveCameraState.imageMetadata,
          // ... pass control parameters
        )
      : LiveDetectionOverlay(
          detections: liveCameraState.detections,
          imageMetadata: liveCameraState.imageMetadata,
        )
```

#### Step 3.5: Add SegmentationControlPanel (conditionally)
```dart
// Only show when in segmentation mode and detecting
if (_isDetecting && liveCameraState.mode == DetectionMode.segmentation)
  Positioned(
    right: 8,
    bottom: 200,
    child: SegmentationControlPanel(/* ... */),
  )
```

### Testing Phase 3:
1. Open live camera
2. Start detection (default mode)
3. Toggle to segmentation mode
4. Verify masks render in real-time
5. Adjust controls, verify instant updates
6. Toggle back to detection, verify it still works
7. Test on different devices (Android/iOS)
8. Test performance (FPS, latency)

### Success Criteria:
- [ ] Mode toggle switches between detection and segmentation
- [ ] Live segmentation renders at >10 FPS
- [ ] Control panel updates visualization in real-time
- [ ] No regression: detection mode still works perfectly
- [ ] Works on both Android and iOS

**Estimated Time**: 4-5 hours (including testing)
**Risk Level**: High (affects working feature, requires careful testing)

---

## Summary

| Phase | What | Files | Risk | Time |
|-------|------|-------|------|------|
| 1 | Static image segmentation | `response_display.dart` | Low | 2-3h |
| 2 | Video segmentation | `video_frame_slideshow.dart` | Medium | 3-4h |
| 3 | Live camera segmentation | `live_camera_*` files | High | 4-5h |

**Total Estimated Time**: 9-12 hours

**Key Principle**: Each phase must be **fully tested and working** before moving to the next.

---

## Current Status

- ✅ **Rollback Complete**: Live detection restored to working state
- ⏳ **Next Step**: Start Phase 1 (Static Image Segmentation)

Last Updated: 2025-01-04
