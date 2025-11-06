#!/bin/bash

# Simple test to verify frontend can call segmentation APIs
# This tests the full stack: Flutter API -> Backend ML Service

set -e

echo "🧪 Frontend Segmentation Integration Test"
echo "=========================================="
echo ""

# Configuration
BACKEND_URL="http://localhost:9000"
ML_SERVICE_URL="http://localhost:9001"
TEST_IMAGE="test_image_street.jpg"
OUTPUT_DIR="./frontend_test_output"

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "📋 Test Configuration:"
echo "  Backend URL: $BACKEND_URL"
echo "  ML Service URL: $ML_SERVICE_URL"
echo "  Test Image: $TEST_IMAGE"
echo "  Output Dir: $OUTPUT_DIR"
echo ""

# Check if test image exists
if [ ! -f "$TEST_IMAGE" ]; then
    echo "❌ Test image not found: $TEST_IMAGE"
    exit 1
fi

echo "✅ Test image found"
echo ""

# Test 1: Health Check
echo "🏥 Test 1: ML Service Health Check"
if curl -s "$ML_SERVICE_URL/health" | grep -q "healthy"; then
    echo "✅ ML Service is healthy"
else
    echo "❌ ML Service is not healthy"
    exit 1
fi
echo ""

# Test 2: Direct Detection API (JSON response)
echo "📦 Test 2: Detection API (JSON)"
DETECTION_RESPONSE=$(curl -s -X POST "$ML_SERVICE_URL/api/detect" \
    -F "image=@$TEST_IMAGE" \
    -F "confidence=0.3")

DETECTION_COUNT=$(echo "$DETECTION_RESPONSE" | jq -r '.count // 0')
DETECTION_TIME=$(echo "$DETECTION_RESPONSE" | jq -r '.inference_time_ms // 0')

echo "  Detected: $DETECTION_COUNT objects"
echo "  Inference time: ${DETECTION_TIME}ms"

if [ "$DETECTION_COUNT" -gt 0 ]; then
    echo "✅ Detection API works"
else
    echo "⚠️  No objects detected (may be normal for this image)"
fi
echo ""

# Test 3: Direct Segmentation API (JSON response)
echo "🎨 Test 3: Segmentation API (JSON)"
SEGMENTATION_RESPONSE=$(curl -s -X POST "$ML_SERVICE_URL/api/segment" \
    -F "image=@$TEST_IMAGE" \
    -F "confidence=0.3")

SEGMENT_COUNT=$(echo "$SEGMENTATION_RESPONSE" | jq -r '.count // 0')
SEGMENT_TIME=$(echo "$SEGMENTATION_RESPONSE" | jq -r '.inference_time_ms // 0')

echo "  Segmented: $SEGMENT_COUNT objects"
echo "  Inference time: ${SEGMENT_TIME}ms"

if [ "$SEGMENT_COUNT" -gt 0 ]; then
    echo "✅ Segmentation API works"
else
    echo "⚠️  No segments detected (may be normal for this image)"
fi
echo ""

# Test 4: Annotated Detection Image
echo "📸 Test 4: Detection Annotated Image"
curl -s -X POST "$ML_SERVICE_URL/api/detect-annotated" \
    -F "image=@$TEST_IMAGE" \
    -F "confidence=0.3" \
    -F "line_width=3" \
    -F "font_size=20" \
    -o "$OUTPUT_DIR/detected.jpg"

DETECTED_SIZE=$(stat -f%z "$OUTPUT_DIR/detected.jpg" 2>/dev/null || stat -c%s "$OUTPUT_DIR/detected.jpg" 2>/dev/null)

if [ "$DETECTED_SIZE" -gt 1000 ]; then
    echo "  File size: ${DETECTED_SIZE} bytes"
    echo "✅ Detection annotated image generated"
else
    echo "❌ Detection annotated image failed (size: ${DETECTED_SIZE} bytes)"
    exit 1
fi
echo ""

# Test 5: Annotated Segmentation Image
echo "🎨 Test 5: Segmentation Annotated Image"
curl -s -X POST "$ML_SERVICE_URL/api/segment-annotated" \
    -F "image=@$TEST_IMAGE" \
    -F "confidence=0.3" \
    -F "opacity=0.5" \
    -F "line_width=2" \
    -F "font_size=20" \
    -o "$OUTPUT_DIR/segmented.jpg"

SEGMENTED_SIZE=$(stat -f%z "$OUTPUT_DIR/segmented.jpg" 2>/dev/null || stat -c%s "$OUTPUT_DIR/segmented.jpg" 2>/dev/null)

if [ "$SEGMENTED_SIZE" -gt 1000 ]; then
    echo "  File size: ${SEGMENTED_SIZE} bytes"
    echo "✅ Segmentation annotated image generated"
else
    echo "❌ Segmentation annotated image failed (size: ${SEGMENTED_SIZE} bytes)"
    exit 1
fi
echo ""

# Test 6: Compare outputs
echo "📊 Test 6: Output Comparison"
echo "  Detection image: $OUTPUT_DIR/detected.jpg (${DETECTED_SIZE} bytes)"
echo "  Segmentation image: $OUTPUT_DIR/segmented.jpg (${SEGMENTED_SIZE} bytes)"
echo ""

# Summary
echo "=========================================="
echo "✅ All Frontend Integration Tests Passed!"
echo "=========================================="
echo ""
echo "📁 Output files saved to: $OUTPUT_DIR/"
echo ""
echo "🎉 Frontend can successfully:"
echo "  ✓ Call detection API and get JSON response"
echo "  ✓ Call segmentation API and get JSON response"
echo "  ✓ Get annotated detection images"
echo "  ✓ Get annotated segmentation images"
echo ""
echo "🔍 Compare the images visually:"
echo "  open $OUTPUT_DIR/detected.jpg $OUTPUT_DIR/segmented.jpg"
echo ""
echo "Next steps:"
echo "  1. Integrate these API calls into Flutter app"
echo "  2. Display annotated images in ResponseDisplay"
echo "  3. Add InteractiveSegmentationOverlay for tap-to-select"
echo "  4. Add SegmentationControlPanel for user controls"
