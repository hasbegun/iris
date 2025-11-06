import 'package:flutter/material.dart';
import '../../../api/models/detection.dart';

/// Overlay widget to draw segmentation masks on live camera preview
class LiveSegmentationOverlay extends StatelessWidget {
  final List<Segment> segments;
  final ImageMetadata? imageMetadata;
  final double cameraAspectRatio;
  final double opacity;
  final double minConfidence;
  final Set<String> filteredClasses;
  final bool showLabels;
  final bool fillStyle;

  const LiveSegmentationOverlay({
    super.key,
    required this.segments,
    required this.imageMetadata,
    required this.cameraAspectRatio,
    this.opacity = 0.5,
    this.minConfidence = 0.0,
    this.filteredClasses = const {},
    this.showLabels = true,
    this.fillStyle = true,
  });

  @override
  Widget build(BuildContext context) {
    debugPrint('[LiveSegmentationOverlay] ========================================');
    debugPrint('[LiveSegmentationOverlay] build() called');
    debugPrint('[LiveSegmentationOverlay] segments count: ${segments.length}');
    debugPrint('[LiveSegmentationOverlay] segments.isEmpty: ${segments.isEmpty}');
    debugPrint('[LiveSegmentationOverlay] imageMetadata: $imageMetadata');
    debugPrint('[LiveSegmentationOverlay] imageMetadata == null: ${imageMetadata == null}');

    if (segments.isEmpty) {
      debugPrint('[LiveSegmentationOverlay] ❌ Skipping render - NO SEGMENTS');
      return const SizedBox.shrink();
    }

    if (imageMetadata == null) {
      debugPrint('[LiveSegmentationOverlay] ❌ Skipping render - NO METADATA');
      debugPrint('[LiveSegmentationOverlay] This is the problem! imageMetadata is null');
      return const SizedBox.shrink();
    }

    debugPrint('[LiveSegmentationOverlay] ✓ Rendering ${segments.length} segments');
    for (var i = 0; i < segments.length; i++) {
      debugPrint('[LiveSegmentationOverlay] Segment $i: ${segments[i].className}, hasMask: ${segments[i].hasMask}, points: ${segments[i].mask.length}');
    }

    return CustomPaint(
      painter: _SegmentationMaskPainter(
        segments: segments,
        imageMetadata: imageMetadata!,
        opacity: opacity,
        minConfidence: minConfidence,
        filteredClasses: filteredClasses,
        showLabels: showLabels,
        fillStyle: fillStyle,
      ),
      child: Container(),
    );
  }
}

class _SegmentationMaskPainter extends CustomPainter {
  final List<Segment> segments;
  final ImageMetadata imageMetadata;
  final double opacity;
  final double minConfidence;
  final Set<String> filteredClasses;
  final bool showLabels;
  final bool fillStyle;

  _SegmentationMaskPainter({
    required this.segments,
    required this.imageMetadata,
    required this.opacity,
    required this.minConfidence,
    required this.filteredClasses,
    required this.showLabels,
    required this.fillStyle,
  });

  @override
  void paint(Canvas canvas, Size size) {
    // Calculate scaling factors
    final scaleX = size.width / imageMetadata.width;
    final scaleY = size.height / imageMetadata.height;

    // Draw each segment with filtering
    for (final segment in segments) {
      // Skip if filtered out by confidence
      if (segment.confidence < minConfidence) continue;

      // Skip if filtered out by class
      if (filteredClasses.isNotEmpty && filteredClasses.contains(segment.className)) {
        continue;
      }

      _drawSegment(canvas, segment, scaleX, scaleY);
    }
  }

  void _drawSegment(Canvas canvas, Segment segment, double scaleX, double scaleY) {
    // Skip if no mask
    if (!segment.hasMask) {
      return;
    }

    // Assign color based on class (consistent hashing)
    final colorIndex = segment.className.hashCode.abs() % _maskColors.length;
    final maskColor = _maskColors[colorIndex];

    // Build polygon path from mask points
    final path = Path();
    bool firstPoint = true;

    for (final point in segment.mask) {
      if (point.length >= 2) {
        final x = point[0] * scaleX;
        final y = point[1] * scaleY;

        if (firstPoint) {
          path.moveTo(x, y);
          firstPoint = false;
        } else {
          path.lineTo(x, y);
        }
      }
    }
    path.close();

    // Draw filled polygon with transparency (if fillStyle is true)
    if (fillStyle) {
      final fillPaint = Paint()
        ..color = maskColor.withOpacity(opacity)
        ..style = PaintingStyle.fill;
      canvas.drawPath(path, fillPaint);
    }

    // Draw polygon outline
    final outlinePaint = Paint()
      ..color = maskColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;
    canvas.drawPath(path, outlinePaint);

    // Draw label if enabled
    if (!showLabels) return;

    final labelText = '${segment.className} ${(segment.confidence * 100).toStringAsFixed(0)}%';
    final textPainter = TextPainter(
      text: TextSpan(
        text: labelText,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 14,
          fontWeight: FontWeight.bold,
          shadows: [
            Shadow(
              color: Colors.black,
              blurRadius: 4,
              offset: Offset(1, 1),
            ),
          ],
        ),
      ),
      textDirection: TextDirection.ltr,
    );
    textPainter.layout();

    // Position label at top-left of bounding box
    final left = segment.x1 * scaleX;
    final top = segment.y1 * scaleY;

    // Draw label background
    final labelRect = Rect.fromLTWH(
      left,
      top - textPainter.height - 8,
      textPainter.width + 8,
      textPainter.height + 4,
    );

    final labelPaint = Paint()
      ..color = maskColor
      ..style = PaintingStyle.fill;
    canvas.drawRect(labelRect, labelPaint);

    // Draw label text
    textPainter.paint(
      canvas,
      Offset(left + 4, labelRect.top + 2),
    );
  }

  @override
  bool shouldRepaint(covariant _SegmentationMaskPainter oldDelegate) {
    return segments != oldDelegate.segments ||
        imageMetadata != oldDelegate.imageMetadata ||
        opacity != oldDelegate.opacity ||
        minConfidence != oldDelegate.minConfidence ||
        filteredClasses != oldDelegate.filteredClasses ||
        showLabels != oldDelegate.showLabels ||
        fillStyle != oldDelegate.fillStyle;
  }

  // Color palette for segmentation masks (same as detection for consistency)
  static const _maskColors = [
    Color(0xFFFF6B6B), // Red
    Color(0xFF4ECDC4), // Cyan
    Color(0xFF45B7D1), // Blue
    Color(0xFF96CEB4), // Green
    Color(0xFFFECA57), // Yellow
    Color(0xFFFF9FF3), // Pink
    Color(0xFF54A0FF), // Light Blue
    Color(0xFF48DBFB), // Aqua
    Color(0xFF1DD1A1), // Emerald
    Color(0xFFEE5A6F), // Rose
  ];
}
