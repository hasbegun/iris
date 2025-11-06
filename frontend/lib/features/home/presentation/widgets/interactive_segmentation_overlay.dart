import 'dart:typed_data';
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import '../../../api/models/detection.dart';

/// Interactive widget that displays an image with segmentation masks
/// Supports tapping masks to highlight and show details
class InteractiveSegmentationOverlay extends StatefulWidget {
  final Uint8List imageBytes;
  final List<Segment> segments;
  final ImageMetadata imageMetadata;
  final double minConfidence;
  final Set<String> filteredClasses;
  final bool showLabels;
  final double opacity;
  final bool fillStyle;

  const InteractiveSegmentationOverlay({
    Key? key,
    required this.imageBytes,
    required this.segments,
    required this.imageMetadata,
    this.minConfidence = 0.0,
    this.filteredClasses = const {},
    this.showLabels = true,
    this.opacity = 0.5,
    this.fillStyle = true,
  }) : super(key: key);

  @override
  State<InteractiveSegmentationOverlay> createState() =>
      _InteractiveSegmentationOverlayState();
}

class _InteractiveSegmentationOverlayState
    extends State<InteractiveSegmentationOverlay> {
  int? _selectedSegmentIndex;
  final GlobalKey _imageKey = GlobalKey();

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: _handleTapDown,
      child: Stack(
        children: [
          // Base image
          Center(
            child: Image.memory(
              widget.imageBytes,
              key: _imageKey,
              fit: BoxFit.contain,
            ),
          ),

          // Segmentation masks overlay
          Center(
            child: LayoutBuilder(
              builder: (context, constraints) {
                // Calculate display size maintaining aspect ratio
                final displaySize = _calculateDisplaySize(
                  constraints.maxWidth,
                  constraints.maxHeight,
                );

                return SizedBox(
                  width: displaySize.width,
                  height: displaySize.height,
                  child: CustomPaint(
                    painter: SegmentationMaskPainter(
                      segments: widget.segments,
                      imageMetadata: widget.imageMetadata,
                      displaySize: displaySize,
                      highlightedIndices:
                          _selectedSegmentIndex != null
                              ? {_selectedSegmentIndex!}
                              : {},
                      filteredClasses: widget.filteredClasses,
                      minConfidence: widget.minConfidence,
                      showLabels: widget.showLabels,
                      opacity: widget.opacity,
                      fillStyle: widget.fillStyle,
                    ),
                  ),
                );
              },
            ),
          ),

          // Segment info tooltip (shown when a mask is tapped)
          if (_selectedSegmentIndex != null)
            _buildSegmentTooltip(),
        ],
      ),
    );
  }

  /// Calculate display size maintaining aspect ratio
  Size _calculateDisplaySize(double maxWidth, double maxHeight) {
    final imageAspect =
        widget.imageMetadata.width / widget.imageMetadata.height;
    final containerAspect = maxWidth / maxHeight;

    double width, height;

    if (imageAspect > containerAspect) {
      // Image is wider - fit to width
      width = maxWidth;
      height = maxWidth / imageAspect;
    } else {
      // Image is taller - fit to height
      height = maxHeight;
      width = maxHeight * imageAspect;
    }

    return Size(width, height);
  }

  /// Handle tap to select/deselect segment
  void _handleTapDown(TapDownDetails details) {
    final renderBox = context.findRenderObject() as RenderBox?;
    if (renderBox == null) return;

    // Get tap position relative to the widget
    final localPosition = details.localPosition;

    // Get the actual display size
    final containerSize = renderBox.size;
    final displaySize = _calculateDisplaySize(
      containerSize.width,
      containerSize.height,
    );

    // Calculate offset to center the image
    final offsetX = (containerSize.width - displaySize.width) / 2;
    final offsetY = (containerSize.height - displaySize.height) / 2;

    // Adjust tap position to be relative to the image
    final imageTapPosition = Offset(
      localPosition.dx - offsetX,
      localPosition.dy - offsetY,
    );

    // Find tapped segment
    final tappedIndex = SegmentationMaskPainter.findTappedSegment(
      imageTapPosition,
      widget.segments,
      widget.imageMetadata,
      displaySize,
    );

    setState(() {
      if (tappedIndex != null && tappedIndex == _selectedSegmentIndex) {
        // Tapped the same segment - deselect
        _selectedSegmentIndex = null;
      } else {
        // Tapped a different segment or empty space
        _selectedSegmentIndex = tappedIndex;
      }
    });
  }

  /// Build tooltip showing segment details
  Widget _buildSegmentTooltip() {
    if (_selectedSegmentIndex == null ||
        _selectedSegmentIndex! >= widget.segments.length) {
      return const SizedBox.shrink();
    }

    final segment = widget.segments[_selectedSegmentIndex!];

    // Calculate polygon area (approximate)
    final area = _calculatePolygonArea(segment.mask);

    return Positioned(
      bottom: 16,
      left: 16,
      right: 16,
      child: Material(
        elevation: 4,
        borderRadius: BorderRadius.circular(12),
        color: Colors.black87,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    segment.className.toUpperCase(),
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, color: Colors.white, size: 20),
                    onPressed: () {
                      setState(() {
                        _selectedSegmentIndex = null;
                      });
                    },
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              _buildInfoRow(
                'Confidence',
                '${(segment.confidence * 100).toStringAsFixed(1)}%',
              ),
              _buildInfoRow(
                'Bounding Box',
                '(${segment.x1.toInt()}, ${segment.y1.toInt()}) → (${segment.x2.toInt()}, ${segment.y2.toInt()})',
              ),
              _buildInfoRow(
                'Mask Points',
                '${segment.mask.length} points',
              ),
              _buildInfoRow(
                'Area',
                '${area.toStringAsFixed(0)} px²',
              ),
            ],
          ),
        ),
      ),
    );
  }

  /// Build info row for tooltip
  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            '$label:',
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 12,
            ),
          ),
          const SizedBox(width: 8),
          Flexible(
            child: Text(
              value,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }

  /// Calculate approximate polygon area using Shoelace formula
  double _calculatePolygonArea(List<List<double>> points) {
    if (points.length < 3) return 0.0;

    double area = 0.0;
    for (int i = 0; i < points.length; i++) {
      final j = (i + 1) % points.length;
      area += points[i][0] * points[j][1];
      area -= points[j][0] * points[i][1];
    }
    return (area.abs() / 2.0);
  }
}

/// Custom painter for drawing segmentation masks
class SegmentationMaskPainter extends CustomPainter {
  final List<Segment> segments;
  final ImageMetadata imageMetadata;
  final Size displaySize;
  final Set<int> highlightedIndices;
  final Set<String> filteredClasses;
  final double minConfidence;
  final bool showLabels;
  final double opacity;
  final bool fillStyle;

  SegmentationMaskPainter({
    required this.segments,
    required this.imageMetadata,
    required this.displaySize,
    required this.highlightedIndices,
    required this.filteredClasses,
    required this.minConfidence,
    required this.showLabels,
    required this.opacity,
    required this.fillStyle,
  });

  @override
  void paint(Canvas canvas, Size size) {
    // Calculate scaling factors
    final scaleX = displaySize.width / imageMetadata.width;
    final scaleY = displaySize.height / imageMetadata.height;

    // Draw each segment
    for (int i = 0; i < segments.length; i++) {
      final segment = segments[i];

      // Skip if filtered out
      if (segment.confidence < minConfidence) continue;
      if (filteredClasses.isNotEmpty &&
          filteredClasses.contains(segment.className)) continue;

      final isHighlighted = highlightedIndices.contains(i);

      _drawSegment(canvas, segment, scaleX, scaleY, isHighlighted);
    }
  }

  void _drawSegment(Canvas canvas, Segment segment, double scaleX, double scaleY, bool isHighlighted) {
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
        ..color = maskColor.withOpacity(isHighlighted ? opacity * 1.5 : opacity)
        ..style = PaintingStyle.fill;
      canvas.drawPath(path, fillPaint);
    }

    // Draw polygon outline
    final outlinePaint = Paint()
      ..color = isHighlighted ? maskColor.withOpacity(1.0) : maskColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = isHighlighted ? 4.0 : 2.0;
    canvas.drawPath(path, outlinePaint);

    // Draw label if enabled
    if (showLabels) {
      _drawLabel(canvas, segment, maskColor, scaleX, scaleY);
    }
  }

  void _drawLabel(Canvas canvas, Segment segment, Color color, double scaleX, double scaleY) {
    // Draw label at the center of bounding box
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
      ..color = color
      ..style = PaintingStyle.fill;
    canvas.drawRect(labelRect, labelPaint);

    // Draw label text
    textPainter.paint(
      canvas,
      Offset(left + 4, labelRect.top + 2),
    );
  }

  @override
  bool shouldRepaint(covariant SegmentationMaskPainter oldDelegate) {
    return segments != oldDelegate.segments ||
        imageMetadata != oldDelegate.imageMetadata ||
        displaySize != oldDelegate.displaySize ||
        highlightedIndices != oldDelegate.highlightedIndices ||
        filteredClasses != oldDelegate.filteredClasses ||
        minConfidence != oldDelegate.minConfidence ||
        showLabels != oldDelegate.showLabels ||
        opacity != oldDelegate.opacity ||
        fillStyle != oldDelegate.fillStyle;
  }

  /// Find which segment was tapped
  static int? findTappedSegment(
    Offset tapPosition,
    List<Segment> segments,
    ImageMetadata imageMetadata,
    Size displaySize,
  ) {
    final scaleX = displaySize.width / imageMetadata.width;
    final scaleY = displaySize.height / imageMetadata.height;

    // Check segments in reverse order (top-most first)
    for (int i = segments.length - 1; i >= 0; i--) {
      final segment = segments[i];

      if (!segment.hasMask) continue;

      // Check if point is inside polygon using ray casting algorithm
      if (_isPointInPolygon(tapPosition, segment.mask, scaleX, scaleY)) {
        return i;
      }
    }

    return null;
  }

  /// Check if point is inside polygon using ray casting algorithm
  static bool _isPointInPolygon(
    Offset point,
    List<List<double>> polygon,
    double scaleX,
    double scaleY,
  ) {
    if (polygon.length < 3) return false;

    bool inside = false;
    for (int i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
      final xi = polygon[i][0] * scaleX;
      final yi = polygon[i][1] * scaleY;
      final xj = polygon[j][0] * scaleX;
      final yj = polygon[j][1] * scaleY;

      final intersect = ((yi > point.dy) != (yj > point.dy)) &&
          (point.dx < (xj - xi) * (point.dy - yi) / (yj - yi) + xi);

      if (intersect) inside = !inside;
    }

    return inside;
  }

  // Color palette for segmentation masks (same as live camera for consistency)
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
