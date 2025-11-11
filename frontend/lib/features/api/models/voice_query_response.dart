import 'dart:convert';
import 'package:flutter/material.dart';

/// Response from voice query API
class VoiceQueryResponse {
  final String sessionId;
  final String query;
  final String queryType;
  final String response;
  final List<String>? detectedObjects;
  final int detectionsCount;
  final bool usedDetectionVerification;
  final double processingTime;
  final DateTime timestamp;

  const VoiceQueryResponse({
    required this.sessionId,
    required this.query,
    required this.queryType,
    required this.response,
    this.detectedObjects,
    required this.detectionsCount,
    required this.usedDetectionVerification,
    required this.processingTime,
    required this.timestamp,
  });

  factory VoiceQueryResponse.fromJson(Map<String, dynamic> json) {
    // DEBUG: Log the full JSON response
    debugPrint('[VoiceQueryResponse] Parsing JSON response:');
    try {
      final prettyJson = const JsonEncoder.withIndent('  ').convert(json);
      debugPrint(prettyJson);
    } catch (e) {
      debugPrint('[VoiceQueryResponse] Failed to pretty-print JSON: $e');
      debugPrint(json.toString());
    }

    // Parse detected objects list
    List<String>? detectedObjects;
    if (json['detected_objects'] != null && json['detected_objects'] is List) {
      detectedObjects = (json['detected_objects'] as List)
          .map((obj) => obj.toString())
          .toList();
      debugPrint('[VoiceQueryResponse] Found ${detectedObjects.length} detected objects');
    }

    // Parse timestamp
    DateTime timestamp = DateTime.now();
    if (json['timestamp'] != null) {
      try {
        timestamp = DateTime.parse(json['timestamp'] as String);
      } catch (e) {
        debugPrint('[VoiceQueryResponse] Failed to parse timestamp: $e');
      }
    }

    return VoiceQueryResponse(
      sessionId: json['session_id'] as String? ?? '',
      query: json['query'] as String? ?? '',
      queryType: json['query_type'] as String? ?? 'general',
      response: json['response'] as String? ?? '',
      detectedObjects: detectedObjects,
      detectionsCount: (json['detections_count'] as num?)?.toInt() ?? 0,
      usedDetectionVerification: json['used_detection_verification'] as bool? ?? false,
      processingTime: (json['processing_time'] as num?)?.toDouble() ?? 0.0,
      timestamp: timestamp,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'session_id': sessionId,
      'query': query,
      'query_type': queryType,
      'response': response,
      'detected_objects': detectedObjects,
      'detections_count': detectionsCount,
      'used_detection_verification': usedDetectionVerification,
      'processing_time': processingTime,
      'timestamp': timestamp.toIso8601String(),
    };
  }

  /// Check if any objects were detected
  bool get hasDetections => detectionsCount > 0 && detectedObjects != null && detectedObjects!.isNotEmpty;

  /// Get formatted detection summary
  String get detectionSummary {
    if (!hasDetections) return 'No objects detected';
    if (detectedObjects!.length == 1) return '1 object: ${detectedObjects![0]}';
    return '${detectedObjects!.length} objects: ${detectedObjects!.join(", ")}';
  }

  /// Get query type display name
  String get queryTypeDisplay {
    switch (queryType) {
      case 'object':
        return 'Object Identification';
      case 'action':
        return 'Action Recognition';
      case 'safety':
        return 'Safety Check';
      case 'count':
        return 'Counting';
      case 'general':
        return 'General Description';
      default:
        return queryType;
    }
  }
}
