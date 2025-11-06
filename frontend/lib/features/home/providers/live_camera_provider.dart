import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import '../../api/models/detection.dart';
import '../../settings/providers/settings_provider.dart';

/// Visualization mode for live camera
enum LiveVisualizationMode {
  detection,
  segmentation,
}

/// Live camera detection state
class LiveCameraState {
  final bool isDetecting;
  final String? targetObjects;
  final LiveVisualizationMode visualizationMode;
  final List<Detection> detections;
  final List<Segment> segments;
  final ImageMetadata? imageMetadata;
  final bool isProcessing;
  final String? error;
  final DateTime? lastDetectionTime;
  final double? lastInferenceTime;
  final double opacity;

  const LiveCameraState({
    this.isDetecting = false,
    this.targetObjects,
    this.visualizationMode = LiveVisualizationMode.detection,
    this.detections = const [],
    this.segments = const [],
    this.imageMetadata,
    this.isProcessing = false,
    this.error,
    this.lastDetectionTime,
    this.lastInferenceTime,
    this.opacity = 0.5,
  });

  LiveCameraState copyWith({
    bool? isDetecting,
    String? targetObjects,
    LiveVisualizationMode? visualizationMode,
    List<Detection>? detections,
    List<Segment>? segments,
    ImageMetadata? imageMetadata,
    bool? isProcessing,
    String? error,
    bool clearError = false,
    DateTime? lastDetectionTime,
    double? lastInferenceTime,
    double? opacity,
  }) {
    return LiveCameraState(
      isDetecting: isDetecting ?? this.isDetecting,
      targetObjects: targetObjects ?? this.targetObjects,
      visualizationMode: visualizationMode ?? this.visualizationMode,
      detections: detections ?? this.detections,
      segments: segments ?? this.segments,
      imageMetadata: imageMetadata ?? this.imageMetadata,
      isProcessing: isProcessing ?? this.isProcessing,
      error: clearError ? null : (error ?? this.error),
      lastDetectionTime: lastDetectionTime ?? this.lastDetectionTime,
      lastInferenceTime: lastInferenceTime ?? this.lastInferenceTime,
      opacity: opacity ?? this.opacity,
    );
  }

  int get detectionCount => detections.length;

  int get segmentCount => segments.length;

  bool get hasDetections => detections.isNotEmpty;

  bool get hasSegments => segments.isNotEmpty;

  String get statusText {
    if (isProcessing) return 'Processing...';
    if (isDetecting && targetObjects != null) return 'Detecting: $targetObjects';
    return 'Idle';
  }
}

/// Notifier for live camera detection
class LiveCameraNotifier extends StateNotifier<LiveCameraState> {
  final Dio _dio;
  final String _backendUrl;

  LiveCameraNotifier(this._dio, this._backendUrl) : super(const LiveCameraState());

  /// Start detection for target objects
  void startDetection(String targetObjects) {
    state = state.copyWith(
      isDetecting: true,
      targetObjects: targetObjects,
      detections: [],
      segments: [],
      clearError: true,
    );
    debugPrint('[LiveCamera] Started detection for: $targetObjects');
  }

  /// Stop detection
  void stopDetection() {
    state = state.copyWith(
      isDetecting: false,
      targetObjects: null,
      detections: [],
      segments: [],
      isProcessing: false,
      clearError: true,
    );
    debugPrint('[LiveCamera] Stopped detection');
  }

  /// Switch visualization mode
  void switchMode(LiveVisualizationMode mode) {
    debugPrint('[LiveCamera] Switching to $mode mode');
    state = state.copyWith(
      visualizationMode: mode,
      detections: [], // Clear detections when switching
      segments: [],   // Clear segments when switching
    );
    debugPrint('[LiveCamera] Mode switched successfully to $mode');
  }

  /// Set opacity for segmentation overlay
  void setOpacity(double opacity) {
    state = state.copyWith(opacity: opacity);
  }

  /// Process a camera frame for detection or segmentation
  Future<void> processFrame(Uint8List frameBytes) async {
    // Skip if not detecting or already processing
    if (!state.isDetecting) {
      debugPrint('[LiveCameraProvider] Skipping frame - not detecting');
      return;
    }

    if (state.isProcessing) {
      debugPrint('[LiveCameraProvider] Skipping frame - already processing');
      return;
    }

    state = state.copyWith(isProcessing: true);
    debugPrint('[LiveCameraProvider] Processing frame: ${frameBytes.length} bytes (mode: ${state.visualizationMode})');

    try {
      // Prepare form data
      final Map<String, dynamic> formDataMap = {
        'image': MultipartFile.fromBytes(
          frameBytes,
          filename: 'frame.jpg',
        ),
        'confidence': 0.5,
      };

      // Only add classes filter if target objects is specified and not empty
      if (state.targetObjects != null && state.targetObjects!.isNotEmpty) {
        formDataMap['classes'] = state.targetObjects;
        debugPrint('[LiveCameraProvider] Filtering for classes: ${state.targetObjects}');
      } else {
        debugPrint('[LiveCameraProvider] Detecting all classes');
      }

      final formData = FormData.fromMap(formDataMap);

      // Choose endpoint based on visualization mode
      final endpoint = state.visualizationMode == LiveVisualizationMode.detection
          ? '/ml/api/detect-stream'
          : '/ml/api/segment-stream';
      final url = '$_backendUrl$endpoint';
      debugPrint('[LiveCameraProvider] Current mode: ${state.visualizationMode}');
      debugPrint('[LiveCameraProvider] Sending request to: $url');

      // Call ML service streaming endpoint
      final response = await _dio.post(
        url,
        data: formData,
        options: Options(
          headers: {'Content-Type': 'multipart/form-data'},
          receiveTimeout: const Duration(seconds: 5),
          sendTimeout: const Duration(seconds: 5),
        ),
      );

      debugPrint('[LiveCameraProvider] Response status: ${response.statusCode}');

      if (response.statusCode == 200) {
        final data = response.data as Map<String, dynamic>;

        // Parse image metadata (both endpoints return this)
        final imageShape = data['image_shape'] as List?;
        ImageMetadata? metadata;
        if (imageShape != null && imageShape.length >= 2) {
          final height = imageShape[0] as int;
          final width = imageShape[1] as int;
          metadata = ImageMetadata(
            width: width,
            height: height,
          );
          debugPrint('[LiveCameraProvider] Image shape: ${width}x${height}');
        }

        final inferenceTime = (data['inference_time_ms'] as num?)?.toDouble();

        if (state.visualizationMode == LiveVisualizationMode.detection) {
          // Parse detections
          final detectionsList = (data['detections'] as List?)
              ?.map((d) => Detection.fromJson(d as Map<String, dynamic>))
              .toList() ?? [];

          // Only update metadata if we successfully parsed it from response
          if (metadata != null) {
            state = state.copyWith(
              detections: detectionsList,
              imageMetadata: metadata,
              isProcessing: false,
              lastDetectionTime: DateTime.now(),
              lastInferenceTime: inferenceTime,
              clearError: true,
            );
          } else {
            // Keep existing metadata if response doesn't include it
            state = state.copyWith(
              detections: detectionsList,
              isProcessing: false,
              lastDetectionTime: DateTime.now(),
              lastInferenceTime: inferenceTime,
              clearError: true,
            );
            debugPrint('[LiveCameraProvider] ⚠️ Warning: image_shape not in response, using existing imageMetadata');
          }

          debugPrint('[LiveCamera] Detected ${detectionsList.length} objects in ${inferenceTime?.toStringAsFixed(3)}s');
        } else {
          // Parse segments
          debugPrint('[LiveCameraProvider] ===== SEGMENTATION MODE =====');
          debugPrint('[LiveCameraProvider] Response data keys: ${data.keys.toList()}');
          debugPrint('[LiveCameraProvider] Response data: ${data.toString()}');

          final segmentsList = <Segment>[];
          try {
            final segmentsData = data['segments'];
            debugPrint('[LiveCameraProvider] Segments data type: ${segmentsData.runtimeType}');
            debugPrint('[LiveCameraProvider] Segments data: $segmentsData');

            if (segmentsData is List) {
              for (var i = 0; i < segmentsData.length; i++) {
                try {
                  final segmentJson = segmentsData[i] as Map<String, dynamic>;
                  debugPrint('[LiveCameraProvider] Parsing segment $i: $segmentJson');
                  final segment = Segment.fromJson(segmentJson);
                  segmentsList.add(segment);
                  debugPrint('[LiveCameraProvider] ✓ Successfully parsed segment $i: ${segment.className}');
                } catch (e, stack) {
                  debugPrint('[LiveCameraProvider] ❌ Error parsing segment $i: $e');
                  debugPrint('[LiveCameraProvider] Stack: $stack');
                }
              }
            }
          } catch (e, stack) {
            debugPrint('[LiveCameraProvider] ❌ Error accessing segments: $e');
            debugPrint('[LiveCameraProvider] Stack: $stack');
          }

          debugPrint('[LiveCameraProvider] Total parsed: ${segmentsList.length} segments');
          if (segmentsList.isNotEmpty) {
            debugPrint('[LiveCameraProvider] First segment details:');
            debugPrint('[LiveCameraProvider]   - className: ${segmentsList.first.className}');
            debugPrint('[LiveCameraProvider]   - confidence: ${segmentsList.first.confidence}');
            debugPrint('[LiveCameraProvider]   - hasMask: ${segmentsList.first.hasMask}');
            debugPrint('[LiveCameraProvider]   - mask points: ${segmentsList.first.mask.length}');
          }

          // Only update metadata if we successfully parsed it from response
          if (metadata != null) {
            state = state.copyWith(
              segments: segmentsList,
              imageMetadata: metadata,
              isProcessing: false,
              lastDetectionTime: DateTime.now(),
              lastInferenceTime: inferenceTime,
              clearError: true,
            );
            debugPrint('[LiveCameraProvider] ✓ Updated imageMetadata: ${metadata.width}x${metadata.height}');
          } else {
            // Keep existing metadata if response doesn't include it
            state = state.copyWith(
              segments: segmentsList,
              isProcessing: false,
              lastDetectionTime: DateTime.now(),
              lastInferenceTime: inferenceTime,
              clearError: true,
            );
            debugPrint('[LiveCameraProvider] ⚠️ Warning: image_shape not in response, using existing imageMetadata: ${state.imageMetadata}');
          }

          debugPrint('[LiveCameraProvider] State updated with ${state.segments.length} segments');
          debugPrint('[LiveCameraProvider] State.imageMetadata: ${state.imageMetadata}');
          debugPrint('[LiveCameraProvider] State.hasSegments: ${state.hasSegments}');
          debugPrint('[LiveCamera] ✓ Segmented ${segmentsList.length} objects in ${inferenceTime?.toStringAsFixed(3)}ms');
        }
      } else {
        debugPrint('[LiveCameraProvider] Processing failed with status: ${response.statusCode}');
        throw Exception('Processing failed with status: ${response.statusCode}');
      }
    } catch (e, stackTrace) {
      debugPrint('[LiveCameraProvider] ❌ Error processing frame: $e');
      debugPrint('[LiveCameraProvider] Stack trace: $stackTrace');
      state = state.copyWith(
        isProcessing: false,
        error: 'Processing failed: $e',
      );
    }
  }

  /// Clear error
  void clearError() {
    state = state.copyWith(clearError: true);
  }

  /// Reset state
  void reset() {
    state = const LiveCameraState();
  }
}

/// Provider for live camera detection
final liveCameraProvider = StateNotifierProvider<LiveCameraNotifier, LiveCameraState>((ref) {
  final dio = Dio(
    BaseOptions(
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
      sendTimeout: const Duration(seconds: 10),
    ),
  );
  final backendUrl = ref.watch(settingsProvider.select((s) => s.backendUrl));
  return LiveCameraNotifier(dio, backendUrl);
});

/// Provider for detection status
final liveCameraDetectingProvider = Provider<bool>((ref) {
  return ref.watch(liveCameraProvider).isDetecting;
});

/// Provider for current detections
final liveCameraDetectionsProvider = Provider<List<Detection>>((ref) {
  return ref.watch(liveCameraProvider).detections;
});

/// Provider for detection count
final liveCameraDetectionCountProvider = Provider<int>((ref) {
  return ref.watch(liveCameraProvider).detectionCount;
});

/// Provider for processing state
final liveCameraProcessingProvider = Provider<bool>((ref) {
  return ref.watch(liveCameraProvider).isProcessing;
});

/// Provider for error
final liveCameraErrorProvider = Provider<String?>((ref) {
  return ref.watch(liveCameraProvider).error;
});
