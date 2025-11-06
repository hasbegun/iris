import 'package:flutter/material.dart';
import '../../../api/models/detection.dart';

/// Custom painter for drawing YOLO detection bounding boxes
class DetectionBoxPainter extends CustomPainter {
  final List<Detection> detections;
  final ImageMetadata imageMetadata;
  final Size displaySize;
  final Set<int> highlightedIndices;
  final Set<String> filteredClasses;
  final double minConfidence;
  final bool showLabels;

  DetectionBoxPainter({
    required this.detections,
    required this.imageMetadata,
    required this.displaySize,
    this.highlightedIndices = const {},
    this.filteredClasses = const {},
    this.minConfidence = 0.0,
    this.showLabels = true,
  });

  /// YOLO color palette (matching ML service colors)
  static const List<Color> yoloColorPalette = [
    Color(0xFF00D9FF), // cyan
    Color(0xFFFF00E4), // magenta
    Color(0xFFFFE600), // yellow
    Color(0xFF00FF00), // lime green
    Color(0xFFFF0000), // red
    Color(0xFF00FFFF), // aqua
    Color(0xFFFF00FF), // fuchsia
    Color(0xFFFFFF00), // yellow
    Color(0xFF0000FF), // blue
    Color(0xFF00FF00), // green
  ];

  /// Get color for a class (consistent hashing)
  Color getColorForClass(String className) {
    final index = className.hashCode.abs() % yoloColorPalette.length;
    return yoloColorPalette[index];
  }

  /// Transform coordinates from image space to display space
  Rect transformBbox(Detection detection) {
    // Calculate scale to fit image in display while maintaining aspect ratio
    final imageAspect = imageMetadata.width / imageMetadata.height;
    final displayAspect = displaySize.width / displaySize.height;

    double scale;
    double offsetX = 0.0;
    double offsetY = 0.0;

    if (imageAspect > displayAspect) {
      // Image is wider - fit to width
      scale = displaySize.width / imageMetadata.width;
      offsetY = (displaySize.height - imageMetadata.height * scale) / 2;
    } else {
      // Image is taller - fit to height
      scale = displaySize.height / imageMetadata.height;
      offsetX = (displaySize.width - imageMetadata.width * scale) / 2;
    }

    // Transform bbox coordinates
    return Rect.fromLTRB(
      detection.x1 * scale + offsetX,
      detection.y1 * scale + offsetY,
      detection.x2 * scale + offsetX,
      detection.y2 * scale + offsetY,
    );
  }

  /// Check if detection passes filters
  bool passesFilters(Detection detection, int index) {
    // Confidence filter
    if (detection.confidence < minConfidence) return false;

    // Class filter (if any classes are selected, only show those)
    if (filteredClasses.isNotEmpty &&
        !filteredClasses.contains(detection.className)) {
      return false;
    }

    return true;
  }

  @override
  void paint(Canvas canvas, Size size) {
    for (int i = 0; i < detections.length; i++) {
      final detection = detections[i];

      // Skip if doesn't pass filters
      if (!passesFilters(detection, i)) continue;

      // Skip if bbox is invalid
      if (!detection.isValid) continue;

      final rect = transformBbox(detection);
      final isHighlighted = highlightedIndices.contains(i);
      final color = getColorForClass(detection.className);

      // Draw bounding box
      _drawBoundingBox(canvas, rect, color, isHighlighted);

      // Draw label if enabled
      if (showLabels) {
        _drawLabel(canvas, rect, detection, color, isHighlighted);
      }
    }
  }

  /// Draw bounding box rectangle
  void _drawBoundingBox(
      Canvas canvas, Rect rect, Color color, bool isHighlighted) {
    final paint = Paint()
      ..color = isHighlighted ? color : color.withOpacity(0.8)
      ..style = PaintingStyle.stroke
      ..strokeWidth = isHighlighted ? 3.0 : 2.0;

    canvas.drawRect(rect, paint);

    // Draw semi-transparent fill for highlighted boxes
    if (isHighlighted) {
      final fillPaint = Paint()
        ..color = color.withOpacity(0.15)
        ..style = PaintingStyle.fill;
      canvas.drawRect(rect, fillPaint);
    }
  }

  /// Draw label with class name and confidence
  void _drawLabel(Canvas canvas, Rect rect, Detection detection, Color color,
      bool isHighlighted) {
    final label = '${detection.className} ${(detection.confidence * 100).toStringAsFixed(0)}%';

    // Create text painter
    final textSpan = TextSpan(
      text: label,
      style: TextStyle(
        color: Colors.white,
        fontSize: isHighlighted ? 14 : 12,
        fontWeight: isHighlighted ? FontWeight.bold : FontWeight.normal,
      ),
    );

    final textPainter = TextPainter(
      text: textSpan,
      textDirection: TextDirection.ltr,
    );

    textPainter.layout();

    // Calculate label background size
    final padding = 4.0;
    final labelWidth = textPainter.width + padding * 2;
    final labelHeight = textPainter.height + padding * 2;

    // Position label above the box, or below if not enough space
    final labelTop = rect.top > labelHeight + 5 ? rect.top - labelHeight - 2 : rect.top + 2;
    final labelLeft = rect.left;

    // Draw label background
    final labelRect = Rect.fromLTWH(
      labelLeft,
      labelTop,
      labelWidth,
      labelHeight,
    );

    final labelPaint = Paint()
      ..color = isHighlighted ? color : color.withOpacity(0.9)
      ..style = PaintingStyle.fill;

    canvas.drawRect(labelRect, labelPaint);

    // Draw text
    textPainter.paint(
      canvas,
      Offset(labelLeft + padding, labelTop + padding),
    );
  }

  @override
  bool shouldRepaint(DetectionBoxPainter oldDelegate) {
    return detections != oldDelegate.detections ||
        highlightedIndices != oldDelegate.highlightedIndices ||
        filteredClasses != oldDelegate.filteredClasses ||
        minConfidence != oldDelegate.minConfidence ||
        displaySize != oldDelegate.displaySize ||
        showLabels != oldDelegate.showLabels;
  }

  /// Helper method to find which detection (if any) was tapped
  /// Returns the index of the tapped detection, or null if none
  static int? findTappedDetection(
    Offset tapPosition,
    List<Detection> detections,
    ImageMetadata imageMetadata,
    Size displaySize,
  ) {
    // Create a temporary painter to use transformation logic
    final painter = DetectionBoxPainter(
      detections: detections,
      imageMetadata: imageMetadata,
      displaySize: displaySize,
    );

    // Check detections in reverse order (top to bottom in visual stack)
    for (int i = detections.length - 1; i >= 0; i--) {
      final detection = detections[i];
      if (!detection.isValid) continue;

      final rect = painter.transformBbox(detection);

      // Expand hitbox slightly for easier tapping
      final expandedRect = rect.inflate(4.0);

      if (expandedRect.contains(tapPosition)) {
        return i;
      }
    }

    return null;
  }
}
