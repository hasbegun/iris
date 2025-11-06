import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../../../api/models/detection.dart';
import 'detection_box_painter.dart';

/// Interactive widget that displays an image with detection bounding boxes
/// Supports tapping boxes to highlight and show details
class InteractiveDetectionOverlay extends StatefulWidget {
  final Uint8List imageBytes;
  final List<Detection> detections;
  final ImageMetadata imageMetadata;
  final double minConfidence;
  final Set<String> filteredClasses;
  final bool showLabels;

  const InteractiveDetectionOverlay({
    Key? key,
    required this.imageBytes,
    required this.detections,
    required this.imageMetadata,
    this.minConfidence = 0.0,
    this.filteredClasses = const {},
    this.showLabels = true,
  }) : super(key: key);

  @override
  State<InteractiveDetectionOverlay> createState() =>
      _InteractiveDetectionOverlayState();
}

class _InteractiveDetectionOverlayState
    extends State<InteractiveDetectionOverlay> {
  int? _selectedDetectionIndex;
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

          // Detection boxes overlay
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
                    painter: DetectionBoxPainter(
                      detections: widget.detections,
                      imageMetadata: widget.imageMetadata,
                      displaySize: displaySize,
                      highlightedIndices:
                          _selectedDetectionIndex != null
                              ? {_selectedDetectionIndex!}
                              : {},
                      filteredClasses: widget.filteredClasses,
                      minConfidence: widget.minConfidence,
                      showLabels: widget.showLabels,
                    ),
                  ),
                );
              },
            ),
          ),

          // Detection info tooltip (shown when a box is tapped)
          if (_selectedDetectionIndex != null)
            _buildDetectionTooltip(),
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

  /// Handle tap to select/deselect detection
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

    // Find tapped detection
    final tappedIndex = DetectionBoxPainter.findTappedDetection(
      imageTapPosition,
      widget.detections,
      widget.imageMetadata,
      displaySize,
    );

    setState(() {
      if (tappedIndex != null && tappedIndex == _selectedDetectionIndex) {
        // Tapped the same box - deselect
        _selectedDetectionIndex = null;
      } else {
        // Tapped a different box or empty space
        _selectedDetectionIndex = tappedIndex;
      }
    });
  }

  /// Build tooltip showing detection details
  Widget _buildDetectionTooltip() {
    if (_selectedDetectionIndex == null ||
        _selectedDetectionIndex! >= widget.detections.length) {
      return const SizedBox.shrink();
    }

    final detection = widget.detections[_selectedDetectionIndex!];

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
                    detection.className.toUpperCase(),
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
                        _selectedDetectionIndex = null;
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
                '${(detection.confidence * 100).toStringAsFixed(1)}%',
              ),
              _buildInfoRow(
                'Position',
                '(${detection.x1.toInt()}, ${detection.y1.toInt()}) → (${detection.x2.toInt()}, ${detection.y2.toInt()})',
              ),
              _buildInfoRow(
                'Size',
                '${detection.width.toInt()} × ${detection.height.toInt()} px',
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
}
