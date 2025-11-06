import 'package:flutter/material.dart';
import '../../../api/models/detection.dart';

/// Overlay widget to draw detection boxes on live camera preview
class LiveDetectionOverlay extends StatelessWidget {
  final List<Detection> detections;
  final ImageMetadata? imageMetadata;
  final double cameraAspectRatio;

  const LiveDetectionOverlay({
    super.key,
    required this.detections,
    required this.imageMetadata,
    required this.cameraAspectRatio,
  });

  @override
  Widget build(BuildContext context) {
    if (detections.isEmpty || imageMetadata == null) {
      return const SizedBox.shrink();
    }

    return CustomPaint(
      painter: _DetectionBoxPainter(
        detections: detections,
        imageMetadata: imageMetadata!,
      ),
      child: Container(),
    );
  }
}

class _DetectionBoxPainter extends CustomPainter {
  final List<Detection> detections;
  final ImageMetadata imageMetadata;

  _DetectionBoxPainter({
    required this.detections,
    required this.imageMetadata,
  });

  @override
  void paint(Canvas canvas, Size size) {
    // Calculate scaling factors
    final scaleX = size.width / imageMetadata.width;
    final scaleY = size.height / imageMetadata.height;

    // Draw each detection
    for (final detection in detections) {
      _drawDetection(canvas, detection, scaleX, scaleY);
    }
  }

  void _drawDetection(Canvas canvas, Detection detection, double scaleX, double scaleY) {
    // Scale bounding box coordinates
    final left = detection.x1 * scaleX;
    final top = detection.y1 * scaleY;
    final right = detection.x2 * scaleX;
    final bottom = detection.y2 * scaleY;

    final rect = Rect.fromLTRB(left, top, right, bottom);

    // Assign color based on class (consistent hashing)
    final colorIndex = detection.className.hashCode.abs() % _boxColors.length;
    final boxColor = _boxColors[colorIndex];

    // Draw bounding box
    final boxPaint = Paint()
      ..color = boxColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3.0;
    canvas.drawRect(rect, boxPaint);

    // Draw filled background for label
    final labelText = '${detection.className} ${(detection.confidence * 100).toStringAsFixed(0)}%';
    final textPainter = TextPainter(
      text: TextSpan(
        text: labelText,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 14,
          fontWeight: FontWeight.bold,
        ),
      ),
      textDirection: TextDirection.ltr,
    );
    textPainter.layout();

    // Position label above the box
    final labelTop = top - textPainter.height - 4;
    final labelRect = Rect.fromLTWH(
      left,
      labelTop > 0 ? labelTop : top,
      textPainter.width + 8,
      textPainter.height + 4,
    );

    // Draw label background
    final labelPaint = Paint()
      ..color = boxColor
      ..style = PaintingStyle.fill;
    canvas.drawRect(labelRect, labelPaint);

    // Draw label text
    textPainter.paint(
      canvas,
      Offset(left + 4, labelRect.top + 2),
    );
  }

  @override
  bool shouldRepaint(covariant _DetectionBoxPainter oldDelegate) {
    return detections != oldDelegate.detections ||
        imageMetadata != oldDelegate.imageMetadata;
  }

  // Color palette for detection boxes
  static const _boxColors = [
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
