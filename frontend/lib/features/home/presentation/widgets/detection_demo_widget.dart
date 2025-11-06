import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../../../api/models/detection.dart';
import 'interactive_detection_overlay.dart';
import 'detection_control_panel.dart';

/// Demo widget for testing detection visualization
/// This widget combines the InteractiveDetectionOverlay and DetectionControlPanel
class DetectionDemoWidget extends StatefulWidget {
  final Uint8List imageBytes;
  final List<Detection> detections;
  final ImageMetadata imageMetadata;

  const DetectionDemoWidget({
    Key? key,
    required this.imageBytes,
    required this.detections,
    required this.imageMetadata,
  }) : super(key: key);

  @override
  State<DetectionDemoWidget> createState() => _DetectionDemoWidgetState();
}

class _DetectionDemoWidgetState extends State<DetectionDemoWidget> {
  double _minConfidence = 0.0;
  Set<String> _filteredClasses = {};
  bool _showLabels = true;
  bool _isPanelCollapsed = false;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Detection visualization
        Expanded(
          child: InteractiveDetectionOverlay(
            imageBytes: widget.imageBytes,
            detections: widget.detections,
            imageMetadata: widget.imageMetadata,
            minConfidence: _minConfidence,
            filteredClasses: _filteredClasses,
            showLabels: _showLabels,
          ),
        ),

        // Control panel
        DetectionControlPanel(
          detections: widget.detections,
          minConfidence: _minConfidence,
          filteredClasses: _filteredClasses,
          showLabels: _showLabels,
          onConfidenceChanged: (value) {
            setState(() {
              _minConfidence = value;
            });
          },
          onFilteredClassesChanged: (classes) {
            setState(() {
              _filteredClasses = classes;
            });
          },
          onShowLabelsChanged: (value) {
            setState(() {
              _showLabels = value;
            });
          },
          isCollapsed: _isPanelCollapsed,
          onToggleCollapse: () {
            setState(() {
              _isPanelCollapsed = !_isPanelCollapsed;
            });
          },
        ),
      ],
    );
  }
}

/// Example usage with sample data
class DetectionDemoExample extends StatelessWidget {
  const DetectionDemoExample({Key? key}) : super(key: key);

  /// Create sample detection data for testing
  List<Detection> get sampleDetections => [
        Detection(
          className: 'car',
          confidence: 0.89,
          bbox: [100, 200, 400, 500],
        ),
        Detection(
          className: 'car',
          confidence: 0.85,
          bbox: [500, 180, 750, 480],
        ),
        Detection(
          className: 'person',
          confidence: 0.92,
          bbox: [200, 100, 350, 550],
        ),
        Detection(
          className: 'bicycle',
          confidence: 0.78,
          bbox: [600, 300, 800, 600],
        ),
      ];

  ImageMetadata get sampleMetadata => ImageMetadata(
        width: 1920,
        height: 1080,
      );

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Detection Visualization Demo'),
      ),
      body: FutureBuilder<Uint8List>(
        // In real usage, this would be the actual image bytes
        future: _loadSampleImage(),
        builder: (context, snapshot) {
          if (snapshot.hasData) {
            return DetectionDemoWidget(
              imageBytes: snapshot.data!,
              detections: sampleDetections,
              imageMetadata: sampleMetadata,
            );
          } else if (snapshot.hasError) {
            return Center(
              child: Text('Error: ${snapshot.error}'),
            );
          } else {
            return const Center(
              child: CircularProgressIndicator(),
            );
          }
        },
      ),
    );
  }

  /// Load sample image (placeholder - would be real image in production)
  Future<Uint8List> _loadSampleImage() async {
    // In real usage, this would load from assets or network
    // For demo, return a 1x1 transparent PNG
    return Uint8List.fromList([
      137, 80, 78, 71, 13, 10, 26, 10, 0, 0, 0, 13, 73, 72, 68, 82, //
      0, 0, 0, 1, 0, 0, 0, 1, 8, 6, 0, 0, 0, 31, 21, 196, 137, 0, //
      0, 0, 13, 73, 68, 65, 84, 120, 156, 99, 96, 0, 0, 0, 2, 0, 1, //
      226, 33, 188, 51, 0, 0, 0, 0, 73, 69, 78, 68, 174, 66, 96, 130, //
    ]);
  }
}
