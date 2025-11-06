import 'package:flutter/material.dart';

/// Model for object detection result from YOLO
class Detection {
  final String className;
  final double confidence;
  final List<double> bbox; // [x1, y1, x2, y2] in pixels

  const Detection({
    required this.className,
    required this.confidence,
    required this.bbox,
  });

  /// Create Detection from JSON
  factory Detection.fromJson(Map<String, dynamic> json) {
    debugPrint('[Detection] Parsing: ${json.toString()}');

    // Parse bbox - handle both List<dynamic> and List<double>
    List<double> bboxValues = [];
    final bboxField = json['bbox'];

    if (bboxField is List) {
      bboxValues = bboxField.map((e) => (e as num).toDouble()).toList();
      debugPrint('[Detection] Parsed bbox: $bboxValues');
    }

    final detection = Detection(
      className: json['class_name'] as String? ?? '',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      bbox: bboxValues,
    );

    debugPrint('[Detection] Created: ${detection.toString()}');
    return detection;
  }

  /// Convert Detection to JSON
  Map<String, dynamic> toJson() {
    return {
      'class_name': className,
      'confidence': confidence,
      'bbox': bbox,
    };
  }

  /// Get bounding box coordinates
  double get x1 => bbox.isNotEmpty ? bbox[0] : 0.0;
  double get y1 => bbox.length > 1 ? bbox[1] : 0.0;
  double get x2 => bbox.length > 2 ? bbox[2] : 0.0;
  double get y2 => bbox.length > 3 ? bbox[3] : 0.0;

  /// Get bounding box width
  double get width => x2 - x1;

  /// Get bounding box height
  double get height => y2 - y1;

  /// Get bounding box center point
  (double x, double y) get center => ((x1 + x2) / 2, (y1 + y2) / 2);

  /// Check if bbox is valid
  bool get isValid => bbox.length == 4 && width > 0 && height > 0;

  @override
  String toString() {
    return 'Detection(className: $className, confidence: ${confidence.toStringAsFixed(2)}, bbox: $bbox)';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    if (other is! Detection) return false;

    return className == other.className &&
        confidence == other.confidence &&
        _listEquals(bbox, other.bbox);
  }

  @override
  int get hashCode => Object.hash(className, confidence, bbox);

  /// Helper to compare lists
  bool _listEquals(List<double> a, List<double> b) {
    if (a.length != b.length) return false;
    for (int i = 0; i < a.length; i++) {
      if (a[i] != b[i]) return false;
    }
    return true;
  }
}

/// Model for image dimensions metadata
class ImageMetadata {
  final int width;
  final int height;

  const ImageMetadata({
    required this.width,
    required this.height,
  });

  /// Create ImageMetadata from JSON
  factory ImageMetadata.fromJson(Map<String, dynamic> json) {
    return ImageMetadata(
      width: json['width'] as int? ?? 0,
      height: json['height'] as int? ?? 0,
    );
  }

  /// Convert ImageMetadata to JSON
  Map<String, dynamic> toJson() {
    return {
      'width': width,
      'height': height,
    };
  }

  /// Get aspect ratio
  double get aspectRatio => height > 0 ? width / height : 1.0;

  /// Check if metadata is valid
  bool get isValid => width > 0 && height > 0;

  @override
  String toString() {
    return 'ImageMetadata(width: $width, height: $height)';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    if (other is! ImageMetadata) return false;

    return width == other.width && height == other.height;
  }

  @override
  int get hashCode => Object.hash(width, height);
}

/// Model for video frame with detections (for slideshow)
class VideoFrame {
  final int frameIndex;
  final double timestamp;
  final List<Detection> detections;
  final ImageMetadata imageMetadata;
  final int count;
  final List<Segment>? segments; // Optional segmentation data

  const VideoFrame({
    required this.frameIndex,
    required this.timestamp,
    required this.detections,
    required this.imageMetadata,
    required this.count,
    this.segments,
  });

  /// Create VideoFrame from JSON
  factory VideoFrame.fromJson(Map<String, dynamic> json) {
    debugPrint('[VideoFrame] Parsing frame ${json['frame_index']}');

    // Parse detections
    List<Detection> detections = [];
    if (json['detections'] != null && json['detections'] is List) {
      detections = (json['detections'] as List)
          .map((detJson) => Detection.fromJson(detJson as Map<String, dynamic>))
          .toList();
    }

    // Parse segments (optional)
    List<Segment>? segments;
    if (json['segments'] != null && json['segments'] is List) {
      segments = (json['segments'] as List)
          .map((segJson) => Segment.fromJson(segJson as Map<String, dynamic>))
          .toList();
      debugPrint('[VideoFrame] Parsed ${segments.length} segments');
    }

    // Parse image metadata
    ImageMetadata? metadata;
    if (json['image_shape'] != null && json['image_shape'] is List) {
      final shape = json['image_shape'] as List;
      if (shape.length >= 2) {
        metadata = ImageMetadata(
          height: (shape[0] as num).toInt(),
          width: (shape[1] as num).toInt(),
        );
      }
    }

    return VideoFrame(
      frameIndex: json['frame_index'] as int? ?? 0,
      timestamp: (json['timestamp'] as num?)?.toDouble() ?? 0.0,
      detections: detections,
      imageMetadata: metadata ?? const ImageMetadata(width: 0, height: 0),
      count: json['count'] as int? ?? 0,
      segments: segments,
    );
  }

  /// Convert VideoFrame to JSON
  Map<String, dynamic> toJson() {
    return {
      'frame_index': frameIndex,
      'timestamp': timestamp,
      'detections': detections.map((d) => d.toJson()).toList(),
      'image_shape': [imageMetadata.height, imageMetadata.width],
      'count': count,
      if (segments != null) 'segments': segments!.map((s) => s.toJson()).toList(),
    };
  }

  /// Format timestamp as MM:SS
  String get formattedTimestamp {
    final minutes = (timestamp / 60).floor();
    final seconds = (timestamp % 60).floor();
    return '${minutes.toString().padLeft(1, '0')}:${seconds.toString().padLeft(2, '0')}';
  }

  /// Check if frame has segmentation data
  bool get hasSegments => segments != null && segments!.isNotEmpty;

  @override
  String toString() {
    return 'VideoFrame(frameIndex: $frameIndex, timestamp: ${timestamp.toStringAsFixed(2)}s, detections: ${detections.length})';
  }
}

/// Metadata about video frames collection
class VideoFramesMetadata {
  final int framesCount;
  final List<VideoFrame> frames;
  final int totalDetections;
  final double videoDuration;

  const VideoFramesMetadata({
    required this.framesCount,
    required this.frames,
    required this.totalDetections,
    required this.videoDuration,
  });

  /// Create VideoFramesMetadata from JSON
  factory VideoFramesMetadata.fromJson(Map<String, dynamic> json) {
    debugPrint('[VideoFramesMetadata] Parsing ${json['frames_count']} frames');

    // Parse frames array
    List<VideoFrame> frames = [];
    if (json['frames'] != null && json['frames'] is List) {
      frames = (json['frames'] as List)
          .map((frameJson) => VideoFrame.fromJson(frameJson as Map<String, dynamic>))
          .toList();
    }

    return VideoFramesMetadata(
      framesCount: json['frames_count'] as int? ?? 0,
      frames: frames,
      totalDetections: json['total_detections'] as int? ?? 0,
      videoDuration: (json['video_duration'] as num?)?.toDouble() ?? 0.0,
    );
  }

  /// Convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'frames_count': framesCount,
      'frames': frames.map((f) => f.toJson()).toList(),
      'total_detections': totalDetections,
      'video_duration': videoDuration,
    };
  }

  /// Check if this is valid video frames data
  bool get isValid => framesCount > 0 && frames.isNotEmpty;

  /// Get frame at index
  VideoFrame? getFrame(int index) {
    if (index >= 0 && index < frames.length) {
      return frames[index];
    }
    return null;
  }

  @override
  String toString() {
    return 'VideoFramesMetadata(framesCount: $framesCount, totalDetections: $totalDetections, videoDuration: ${videoDuration.toStringAsFixed(1)}s)';
  }
}

/// Model for detection response from API
class DetectionResponse {
  final String status;
  final List<Detection> detections;
  final int count;
  final ImageMetadata imageMetadata;
  final double inferenceTimeMs;

  const DetectionResponse({
    required this.status,
    required this.detections,
    required this.count,
    required this.imageMetadata,
    required this.inferenceTimeMs,
  });

  /// Create DetectionResponse from JSON
  factory DetectionResponse.fromJson(Map<String, dynamic> json) {
    debugPrint('[DetectionResponse] Parsing response');

    // Parse detections
    List<Detection> detections = [];
    if (json['detections'] != null && json['detections'] is List) {
      detections = (json['detections'] as List)
          .map((detJson) => Detection.fromJson(detJson as Map<String, dynamic>))
          .toList();
    }

    // Parse image metadata
    ImageMetadata? metadata;
    if (json['image_shape'] != null && json['image_shape'] is List) {
      final shape = json['image_shape'] as List;
      if (shape.length >= 2) {
        metadata = ImageMetadata(
          height: (shape[0] as num).toInt(),
          width: (shape[1] as num).toInt(),
        );
      }
    }

    return DetectionResponse(
      status: json['status'] as String? ?? 'unknown',
      detections: detections,
      count: json['count'] as int? ?? 0,
      imageMetadata: metadata ?? const ImageMetadata(width: 0, height: 0),
      inferenceTimeMs: (json['inference_time_ms'] as num?)?.toDouble() ?? 0.0,
    );
  }

  /// Convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'status': status,
      'detections': detections.map((d) => d.toJson()).toList(),
      'count': count,
      'image_shape': [imageMetadata.height, imageMetadata.width],
      'inference_time_ms': inferenceTimeMs,
    };
  }

  /// Check if detection was successful
  bool get isSuccess => status == 'success';

  @override
  String toString() {
    return 'DetectionResponse(status: $status, detections: ${detections.length}, inferenceTime: ${inferenceTimeMs.toStringAsFixed(1)}ms)';
  }
}

/// Model for instance segmentation result from YOLO
class Segment {
  final String className;
  final double confidence;
  final List<double> bbox; // [x1, y1, x2, y2] in pixels
  final List<List<double>> mask; // Polygon points [[x, y], [x, y], ...]

  const Segment({
    required this.className,
    required this.confidence,
    required this.bbox,
    required this.mask,
  });

  /// Create Segment from JSON
  factory Segment.fromJson(Map<String, dynamic> json) {
    debugPrint('[Segment] Parsing: ${json.toString()}');

    // Parse bbox - handle both List<dynamic> and List<double>
    List<double> bboxValues = [];
    final bboxField = json['bbox'];

    if (bboxField is List) {
      bboxValues = bboxField.map((e) => (e as num).toDouble()).toList();
      debugPrint('[Segment] Parsed bbox: $bboxValues');
    }

    // Parse mask - [[x, y], [x, y], ...]
    List<List<double>> maskPoints = [];
    final maskField = json['mask'];

    if (maskField is List) {
      for (var point in maskField) {
        if (point is List && point.length >= 2) {
          maskPoints.add([
            (point[0] as num).toDouble(),
            (point[1] as num).toDouble(),
          ]);
        }
      }
      debugPrint('[Segment] Parsed mask: ${maskPoints.length} points');
    }

    final segment = Segment(
      className: json['class_name'] as String? ?? '',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      bbox: bboxValues,
      mask: maskPoints,
    );

    debugPrint('[Segment] Created: ${segment.toString()}');
    return segment;
  }

  /// Convert Segment to JSON
  Map<String, dynamic> toJson() {
    return {
      'class_name': className,
      'confidence': confidence,
      'bbox': bbox,
      'mask': mask,
    };
  }

  /// Get bounding box coordinates
  double get x1 => bbox.isNotEmpty ? bbox[0] : 0.0;
  double get y1 => bbox.length > 1 ? bbox[1] : 0.0;
  double get x2 => bbox.length > 2 ? bbox[2] : 0.0;
  double get y2 => bbox.length > 3 ? bbox[3] : 0.0;

  /// Get bounding box width
  double get width => x2 - x1;

  /// Get bounding box height
  double get height => y2 - y1;

  /// Get bounding box center point
  (double x, double y) get center => ((x1 + x2) / 2, (y1 + y2) / 2);

  /// Check if bbox is valid
  bool get isValid => bbox.length == 4 && width > 0 && height > 0;

  /// Check if mask is valid (at least 3 points for a polygon)
  bool get hasMask => mask.isNotEmpty && mask.length >= 3;

  @override
  String toString() {
    return 'Segment(className: $className, confidence: ${confidence.toStringAsFixed(2)}, bbox: $bbox, maskPoints: ${mask.length})';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    if (other is! Segment) return false;

    return className == other.className &&
        confidence == other.confidence &&
        _listEquals(bbox, other.bbox) &&
        _maskEquals(mask, other.mask);
  }

  @override
  int get hashCode => Object.hash(className, confidence, bbox, mask);

  /// Helper to compare lists
  bool _listEquals(List<double> a, List<double> b) {
    if (a.length != b.length) return false;
    for (int i = 0; i < a.length; i++) {
      if (a[i] != b[i]) return false;
    }
    return true;
  }

  /// Helper to compare mask lists
  bool _maskEquals(List<List<double>> a, List<List<double>> b) {
    if (a.length != b.length) return false;
    for (int i = 0; i < a.length; i++) {
      if (!_listEquals(a[i], b[i])) return false;
    }
    return true;
  }
}

/// Model for segmentation response from API
class SegmentationResponse {
  final String status;
  final List<Segment> segments;
  final int count;
  final ImageMetadata imageMetadata;
  final double inferenceTimeMs;

  const SegmentationResponse({
    required this.status,
    required this.segments,
    required this.count,
    required this.imageMetadata,
    required this.inferenceTimeMs,
  });

  /// Create SegmentationResponse from JSON
  factory SegmentationResponse.fromJson(Map<String, dynamic> json) {
    debugPrint('[SegmentationResponse] Parsing response');

    // Parse segments
    List<Segment> segments = [];
    if (json['segments'] != null && json['segments'] is List) {
      segments = (json['segments'] as List)
          .map((segJson) => Segment.fromJson(segJson as Map<String, dynamic>))
          .toList();
    }

    // Parse image metadata
    ImageMetadata? metadata;
    if (json['image_shape'] != null && json['image_shape'] is List) {
      final shape = json['image_shape'] as List;
      if (shape.length >= 2) {
        metadata = ImageMetadata(
          height: (shape[0] as num).toInt(),
          width: (shape[1] as num).toInt(),
        );
      }
    }

    return SegmentationResponse(
      status: json['status'] as String? ?? 'unknown',
      segments: segments,
      count: json['count'] as int? ?? 0,
      imageMetadata: metadata ?? const ImageMetadata(width: 0, height: 0),
      inferenceTimeMs: (json['inference_time_ms'] as num?)?.toDouble() ?? 0.0,
    );
  }

  /// Convert to JSON
  Map<String, dynamic> toJson() {
    return {
      'status': status,
      'segments': segments.map((s) => s.toJson()).toList(),
      'count': count,
      'image_shape': [imageMetadata.height, imageMetadata.width],
      'inference_time_ms': inferenceTimeMs,
    };
  }

  /// Check if segmentation was successful
  bool get isSuccess => status == 'success';

  @override
  String toString() {
    return 'SegmentationResponse(status: $status, segments: ${segments.length}, inferenceTime: ${inferenceTimeMs.toStringAsFixed(1)}ms)';
  }
}
