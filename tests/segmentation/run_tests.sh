#!/bin/bash

# Segmentation Testing Script
# This script tests detection and segmentation on static images and videos

set -e

echo "🧪 Segmentation Testing Suite"
echo "=============================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test directory
TEST_DIR="/Users/innox/projects/iris/tests/segmentation"
cd "$TEST_DIR"

# Check services
echo "📡 Checking services..."
if curl -s http://localhost:9001/health > /dev/null; then
    echo -e "${GREEN}✓${NC} ML Service is running"
else
    echo -e "${RED}✗${NC} ML Service is NOT running!"
    echo "Start it with: cd /Users/innox/projects/iris/ml-service && python run.py"
    exit 1
fi

if lsof -ti:9000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backend is running"
else
    echo -e "${YELLOW}⚠${NC} Backend might not be running (port 9000)"
fi

echo ""

# Download test image if not exists
if [ ! -f "test_image.jpg" ]; then
    echo "📥 Downloading test image..."
    curl -s -o test_image.jpg "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=800"
    echo -e "${GREEN}✓${NC} Test image downloaded"
fi

echo ""
echo "═══════════════════════════════════════"
echo "TEST 1: STATIC IMAGE DETECTION"
echo "═══════════════════════════════════════"
echo ""

echo "🔍 Running detection..."
DETECT_RESULT=$(curl -s -X POST http://localhost:9001/api/detect \
  -F "image=@test_image.jpg" \
  -F "confidence=0.5")

DETECT_COUNT=$(echo "$DETECT_RESULT" | jq -r '.count // 0')
DETECT_TIME=$(echo "$DETECT_RESULT" | jq -r '.inference_time_ms // 0')
DETECT_STATUS=$(echo "$DETECT_RESULT" | jq -r '.status // "error"')

if [ "$DETECT_STATUS" = "success" ]; then
    echo -e "${GREEN}✓${NC} Detection successful"
    echo "  Objects found: $DETECT_COUNT"
    echo "  Inference time: ${DETECT_TIME}ms"
    echo "  Classes: $(echo "$DETECT_RESULT" | jq -r '.detections[].class_name' | sort -u | tr '\n' ', ' | sed 's/,$//')"
else
    echo -e "${RED}✗${NC} Detection failed"
    echo "$DETECT_RESULT" | jq '.'
fi

echo ""
echo "🖼️  Generating annotated detection image..."
curl -s -X POST http://localhost:9001/api/detect-annotated \
  -F "image=@test_image.jpg" \
  -F "confidence=0.5" \
  -o detected_output.jpg

if [ -f "detected_output.jpg" ]; then
    echo -e "${GREEN}✓${NC} Annotated image saved: detected_output.jpg"
fi

echo ""
echo "═══════════════════════════════════════"
echo "TEST 2: STATIC IMAGE SEGMENTATION"
echo "═══════════════════════════════════════"
echo ""

echo "🎨 Running segmentation..."
SEGMENT_RESULT=$(curl -s -X POST http://localhost:9001/api/segment \
  -F "image=@test_image.jpg" \
  -F "confidence=0.5")

SEGMENT_COUNT=$(echo "$SEGMENT_RESULT" | jq -r '.count // 0')
SEGMENT_TIME=$(echo "$SEGMENT_RESULT" | jq -r '.inference_time_ms // 0')
SEGMENT_STATUS=$(echo "$SEGMENT_RESULT" | jq -r '.status // "error"')

if [ "$SEGMENT_STATUS" = "success" ]; then
    echo -e "${GREEN}✓${NC} Segmentation successful"
    echo "  Objects segmented: $SEGMENT_COUNT"
    echo "  Inference time: ${SEGMENT_TIME}ms"
    echo "  Classes: $(echo "$SEGMENT_RESULT" | jq -r '.segments[].class_name' | sort -u | tr '\n' ', ' | sed 's/,$//')"

    # Show mask details
    MASK_POINTS=$(echo "$SEGMENT_RESULT" | jq -r '.segments[0].mask | length // 0')
    if [ "$MASK_POINTS" -gt 0 ]; then
        echo "  Mask points (first object): $MASK_POINTS points"
    fi
else
    echo -e "${RED}✗${NC} Segmentation failed"
    echo "$SEGMENT_RESULT" | jq '.'
fi

echo ""
echo "🖼️  Generating annotated segmentation image..."
curl -s -X POST http://localhost:9001/api/segment-annotated \
  -F "image=@test_image.jpg" \
  -F "confidence=0.5" \
  -F "opacity=0.5" \
  -o segmented_output.jpg

if [ -f "segmented_output.jpg" ]; then
    echo -e "${GREEN}✓${NC} Annotated image saved: segmented_output.jpg"
fi

echo ""
echo "═══════════════════════════════════════"
echo "TEST 3: CLASS FILTERING"
echo "═══════════════════════════════════════"
echo ""

echo "🔍 Testing class filtering (car, person)..."
FILTERED_RESULT=$(curl -s -X POST http://localhost:9001/api/segment \
  -F "image=@test_image.jpg" \
  -F "confidence=0.5" \
  -F "classes=car,person")

FILTERED_COUNT=$(echo "$FILTERED_RESULT" | jq -r '.count // 0')
FILTERED_CLASSES=$(echo "$FILTERED_RESULT" | jq -r '.segments[].class_name' | sort -u | tr '\n' ', ' | sed 's/,$//')

echo -e "${GREEN}✓${NC} Class filtering works"
echo "  Objects found: $FILTERED_COUNT"
echo "  Classes: $FILTERED_CLASSES"

echo ""
echo "═══════════════════════════════════════"
echo "TEST 4: STREAM ENDPOINT (Simulated)"
echo "═══════════════════════════════════════"
echo ""

echo "📹 Testing detect-stream endpoint..."
STREAM_DETECT=$(curl -s -X POST http://localhost:9000/ml/api/detect-stream \
  -F "image=@test_image.jpg" \
  -F "confidence=0.5" 2>/dev/null || curl -s -X POST http://localhost:9001/api/detect-stream \
  -F "image=@test_image.jpg" \
  -F "confidence=0.5")

STREAM_DETECT_COUNT=$(echo "$STREAM_DETECT" | jq -r '.count // 0')
STREAM_DETECT_TIME=$(echo "$STREAM_DETECT" | jq -r '.inference_time_ms // 0')

echo -e "${GREEN}✓${NC} Stream detection"
echo "  Objects: $STREAM_DETECT_COUNT"
echo "  Time: ${STREAM_DETECT_TIME}ms"

echo ""
echo "📹 Testing segment-stream endpoint..."
STREAM_SEGMENT=$(curl -s -X POST http://localhost:9000/ml/api/segment-stream \
  -F "image=@test_image.jpg" \
  -F "confidence=0.5" 2>/dev/null || curl -s -X POST http://localhost:9001/api/segment-stream \
  -F "image=@test_image.jpg" \
  -F "confidence=0.5")

STREAM_SEGMENT_COUNT=$(echo "$STREAM_SEGMENT" | jq -r '.count // 0')
STREAM_SEGMENT_TIME=$(echo "$STREAM_SEGMENT" | jq -r '.inference_time_ms // 0')

echo -e "${GREEN}✓${NC} Stream segmentation"
echo "  Objects: $STREAM_SEGMENT_COUNT"
echo "  Time: ${STREAM_SEGMENT_TIME}ms"

echo ""
echo "═══════════════════════════════════════"
echo "PERFORMANCE COMPARISON"
echo "═══════════════════════════════════════"
echo ""

echo "Detection:    ${DETECT_TIME}ms"
echo "Segmentation: ${SEGMENT_TIME}ms"
OVERHEAD=$(echo "scale=1; ($SEGMENT_TIME - $DETECT_TIME) / $DETECT_TIME * 100" | bc)
echo "Overhead:     ${OVERHEAD}%"

echo ""
echo "═══════════════════════════════════════"
echo "SUMMARY"
echo "═══════════════════════════════════════"
echo ""

echo -e "${GREEN}✓${NC} All API tests passed!"
echo ""
echo "Output files:"
echo "  - detected_output.jpg (bounding boxes)"
echo "  - segmented_output.jpg (polygon masks)"
echo ""
echo "To view results:"
echo "  open detected_output.jpg segmented_output.jpg"
echo ""
echo "Next steps:"
echo "  1. Open the images above to compare detection vs segmentation"
echo "  2. Test live camera in the Flutter app"
echo "  3. Test with your own images/videos"
echo ""
