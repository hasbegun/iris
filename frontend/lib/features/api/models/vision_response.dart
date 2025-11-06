import 'dart:convert';
import 'package:flutter/material.dart';
import 'detection.dart';

/// Response from vision analysis API
class VisionResponse {
  final String response;
  final String modelUsed;
  final double processingTime;
  final String sessionId;
  final String? annotatedImageUrl;
  final bool hasAnnotatedImage;
  final List<Detection>? detections;
  final List<Segment>? segments;
  final ImageMetadata? imageMetadata;
  final VideoFramesMetadata? videoFrames;

  const VisionResponse({
    required this.response,
    required this.modelUsed,
    required this.processingTime,
    required this.sessionId,
    this.annotatedImageUrl,
    this.hasAnnotatedImage = false,
    this.detections,
    this.segments,
    this.imageMetadata,
    this.videoFrames,
  });

  factory VisionResponse.fromJson(Map<String, dynamic> json) {
    // DEBUG: Log the full JSON response
    debugPrint('[VisionResponse] Parsing JSON response:');
    try {
      final prettyJson = const JsonEncoder.withIndent('  ').convert(json);
      debugPrint(prettyJson);
    } catch (e) {
      debugPrint('[VisionResponse] Failed to pretty-print JSON: $e');
      debugPrint(json.toString());
    }

    // Safely extract response field - handle both String and List types
    String responseText = '';
    final responseField = json['response'];

    if (responseField is String) {
      responseText = responseField;
    } else if (responseField is List) {
      // If response is a list (error case), convert to string
      responseText = responseField.map((e) => e.toString()).join(', ');
    } else if (responseField != null) {
      // Handle any other type
      responseText = responseField.toString();
    }

    // Parse detections if present
    List<Detection>? detections;
    if (json['detections'] != null && json['detections'] is List) {
      debugPrint('[VisionResponse] Found detections array with ${(json['detections'] as List).length} items');
      detections = (json['detections'] as List)
          .map((detJson) => Detection.fromJson(detJson as Map<String, dynamic>))
          .toList();
      debugPrint('[VisionResponse] Parsed ${detections.length} Detection objects');
    } else {
      debugPrint('[VisionResponse] No detections in response');
    }

    // Parse segments if present
    List<Segment>? segments;
    if (json['segments'] != null && json['segments'] is List) {
      debugPrint('[VisionResponse] Found segments array with ${(json['segments'] as List).length} items');
      segments = (json['segments'] as List)
          .map((segJson) => Segment.fromJson(segJson as Map<String, dynamic>))
          .toList();
      debugPrint('[VisionResponse] Parsed ${segments.length} Segment objects');
    } else {
      debugPrint('[VisionResponse] No segments in response');
    }

    // Parse image metadata if present
    ImageMetadata? imageMetadata;
    if (json['image_metadata'] != null && json['image_metadata'] is Map) {
      imageMetadata = ImageMetadata.fromJson(
          json['image_metadata'] as Map<String, dynamic>);
      debugPrint('[VisionResponse] Parsed image metadata: ${imageMetadata.width}x${imageMetadata.height}');
    } else {
      debugPrint('[VisionResponse] No image metadata in response');
    }

    // Parse video frames metadata if present
    VideoFramesMetadata? videoFrames;
    if (json['video_frames'] != null && json['video_frames'] is Map) {
      videoFrames = VideoFramesMetadata.fromJson(
          json['video_frames'] as Map<String, dynamic>);
      debugPrint('[VisionResponse] Parsed video frames: ${videoFrames.framesCount} frames');
    } else {
      debugPrint('[VisionResponse] No video frames in response');
    }

    return VisionResponse(
      response: responseText.isEmpty ? '' : responseText,
      modelUsed: json['model_used'] as String? ?? 'unknown',
      processingTime: (json['processing_time'] as num?)?.toDouble() ?? 0.0,
      sessionId: json['session_id'] as String? ?? '',
      annotatedImageUrl: json['annotated_image_url'] as String?,
      hasAnnotatedImage: json['has_annotated_image'] as bool? ?? false,
      detections: detections,
      segments: segments,
      imageMetadata: imageMetadata,
      videoFrames: videoFrames,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'response': response,
      'model_used': modelUsed,
      'processing_time': processingTime,
      'session_id': sessionId,
      'annotated_image_url': annotatedImageUrl,
      'has_annotated_image': hasAnnotatedImage,
      'detections': detections?.map((d) => d.toJson()).toList(),
      'segments': segments?.map((s) => s.toJson()).toList(),
      'image_metadata': imageMetadata?.toJson(),
      'video_frames': videoFrames?.toJson(),
    };
  }

  /// Check if this response has detection data (single frame)
  bool get hasDetections =>
      detections != null && detections!.isNotEmpty && imageMetadata != null;

  /// Check if this response has segmentation data (single frame)
  bool get hasSegments =>
      segments != null && segments!.isNotEmpty && imageMetadata != null;

  /// Check if this response has video frames data (slideshow)
  bool get hasVideoFrames => videoFrames != null && videoFrames!.isValid;

  /// Get count of detections by class
  Map<String, int> get detectionCounts {
    if (detections == null) return {};

    final counts = <String, int>{};
    for (final detection in detections!) {
      counts[detection.className] = (counts[detection.className] ?? 0) + 1;
    }
    return counts;
  }

  /// Get count of segments by class
  Map<String, int> get segmentCounts {
    if (segments == null) return {};

    final counts = <String, int>{};
    for (final segment in segments!) {
      counts[segment.className] = (counts[segment.className] ?? 0) + 1;
    }
    return counts;
  }

  /// Get total detection count
  int get totalDetections => detections?.length ?? 0;

  /// Get total segment count
  int get totalSegments => segments?.length ?? 0;
}
