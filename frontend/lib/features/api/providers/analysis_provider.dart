import 'dart:io';
import 'dart:typed_data';
import 'package:crypto/crypto.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../home/models/media_item.dart';
import '../../settings/providers/settings_provider.dart';
import '../models/analysis_state.dart';
import '../models/api_error.dart';
import '../models/conversation_message.dart';
import '../models/vision_response.dart';
import '../services/api_service.dart';

/// Provider for API service
final apiServiceProvider = Provider<ApiService>((ref) {
  // Only rebuild when backendUrl changes, not when other settings change
  final backendUrl = ref.watch(settingsProvider.select((s) => s.backendUrl));
  return ApiService(backendUrl);
});

/// Vision analysis provider notifier
class AnalysisNotifier extends StateNotifier<AnalysisState> {
  final ApiService _apiService;

  AnalysisNotifier(this._apiService) : super(const AnalysisState());

  /// Compute SHA-256 hash of a file
  Future<String> _computeFileHash(File file) async {
    final bytes = await file.readAsBytes();
    final digest = sha256.convert(bytes);
    return digest.toString();
  }

  /// Analyze media with prompt
  Future<void> analyzeMedia({
    required MediaItem mediaItem,
    required String prompt,
  }) async {
    try {
      // Compute hash of the media file for tracking
      final mediaHash = await _computeFileHash(mediaItem.file);

      // Read image bytes for images
      // For videos, we'll fetch the extracted frame from backend after analysis
      Uint8List? imageBytes;

      if (mediaItem.isImage) {
        imageBytes = await mediaItem.file.readAsBytes();
        debugPrint('[AnalysisProvider] Read ${imageBytes.length} bytes from image file');
      } else {
        debugPrint('[AnalysisProvider] Video file - will fetch extracted frame after analysis');
      }

      state = state.copyWith(isLoading: true, clearError: true);

      VisionResponse response;

      if (mediaItem.isImage) {
        response = await _apiService.analyzeImage(
          imageFile: mediaItem.file,
          prompt: prompt,
          sessionId: state.sessionId,
        );
      } else {
        response = await _apiService.analyzeVideo(
          videoFile: mediaItem.file,
          prompt: prompt,
          sessionId: state.sessionId,
        );

        // For videos, check if backend has video frames metadata (slideshow mode)
        if (response.sessionId.isNotEmpty) {
          try {
            debugPrint('[AnalysisProvider] Checking for video frames metadata');
            final videoFramesMetadata = await _apiService.fetchVideoFramesMetadata(response.sessionId);

            if (videoFramesMetadata != null && videoFramesMetadata.isValid) {
              // Slideshow mode: Multiple frames available
              debugPrint('[AnalysisProvider] Got video frames metadata: ${videoFramesMetadata.framesCount} frames');

              // Update response to include video frames
              response = VisionResponse(
                response: response.response,
                modelUsed: response.modelUsed,
                processingTime: response.processingTime,
                sessionId: response.sessionId,
                annotatedImageUrl: response.annotatedImageUrl,
                hasAnnotatedImage: response.hasAnnotatedImage,
                detections: response.detections,
                imageMetadata: response.imageMetadata,
                videoFrames: videoFramesMetadata,
              );

              // Fetch first frame for display (optional, since slideshow will fetch on demand)
              // This gives immediate visual feedback
              final firstFrameBytes = await _apiService.fetchFrameByIndex(response.sessionId, 0);
              if (firstFrameBytes != null) {
                imageBytes = firstFrameBytes;
                debugPrint('[AnalysisProvider] Got first video frame: ${firstFrameBytes.length} bytes');
              }
            } else if (response.hasDetections) {
              // Single frame mode: Backward compatibility
              debugPrint('[AnalysisProvider] No slideshow data, fetching single extracted frame');
              final frameBytes = await _apiService.fetchImageBytes(response.sessionId);
              if (frameBytes != null) {
                imageBytes = frameBytes;
                debugPrint('[AnalysisProvider] Got video frame: ${frameBytes.length} bytes');
              }
            }
          } catch (e) {
            debugPrint('[AnalysisProvider] Failed to fetch video frames data: $e');
          }
        }
      }

      // Debug logging for detection data
      debugPrint('[AnalysisProvider] Response received:');
      debugPrint('  - Has detections: ${response.hasDetections}');
      debugPrint('  - Detections count: ${response.totalDetections}');
      debugPrint('  - Image metadata: ${response.imageMetadata}');
      if (response.detections != null && response.detections!.isNotEmpty) {
        debugPrint('  - First detection: ${response.detections!.first}');
      }

      // Add to conversation history WITH imageBytes for interactive rendering
      final message = ConversationMessage(
        prompt: prompt,
        response: response,
        timestamp: DateTime.now(),
        imageBytes: imageBytes, // CRITICAL: Pass image bytes for client-side rendering
      );

      debugPrint('[AnalysisProvider] Created ConversationMessage with imageBytes: ${message.imageBytes != null}');

      final updatedHistory = [...state.conversationHistory, message];

      state = state.copyWith(
        conversationHistory: updatedHistory,
        isLoading: false,
        sessionId: response.sessionId,
        currentMediaHash: mediaHash,
        clearError: true,
      );

      debugPrint('[AnalysisProvider] Analysis completed successfully');
    } on ApiError catch (e) {
      debugPrint('[AnalysisProvider] API error: $e');
      state = state.copyWith(
        isLoading: false,
        error: e,
      );
    } catch (e) {
      debugPrint('[AnalysisProvider] Unexpected error: $e');
      state = state.copyWith(
        isLoading: false,
        error: ApiError.fromException(e),
      );
    }
  }

  /// Enrich a conversation message with segmentation data
  Future<void> enrichWithSegmentation(int messageIndex) async {
    if (messageIndex < 0 || messageIndex >= state.conversationHistory.length) {
      debugPrint('[AnalysisProvider] Invalid message index: $messageIndex');
      return;
    }

    final message = state.conversationHistory[messageIndex];

    // Check if we have image bytes
    if (message.imageBytes == null) {
      debugPrint('[AnalysisProvider] No image bytes available for message $messageIndex');
      return;
    }

    // Check if already has segmentation data
    if (message.response.hasSegments) {
      debugPrint('[AnalysisProvider] Message $messageIndex already has segmentation data');
      return;
    }

    try {
      state = state.copyWith(isLoading: true, clearError: true);
      debugPrint('[AnalysisProvider] Enriching message $messageIndex with segmentation data');

      // Call segmentation API
      final segmentationResponse = await _apiService.segmentImageFromBytes(
        imageBytes: message.imageBytes!,
        confidence: 0.5,
      );

      debugPrint('[AnalysisProvider] Received ${segmentationResponse.segments.length} segments');

      // Create updated response by merging segmentation data into existing response
      final updatedResponse = VisionResponse(
        response: message.response.response,
        modelUsed: message.response.modelUsed,
        processingTime: message.response.processingTime,
        sessionId: message.response.sessionId,
        annotatedImageUrl: message.response.annotatedImageUrl,
        hasAnnotatedImage: message.response.hasAnnotatedImage,
        detections: message.response.detections, // Keep existing detections
        segments: segmentationResponse.segments, // Add new segments
        imageMetadata: segmentationResponse.imageMetadata ?? message.response.imageMetadata,
        videoFrames: message.response.videoFrames,
      );

      // Update the message
      final updatedMessage = message.copyWith(response: updatedResponse);

      // Update conversation history
      final updatedHistory = List<ConversationMessage>.from(state.conversationHistory);
      updatedHistory[messageIndex] = updatedMessage;

      state = state.copyWith(
        conversationHistory: updatedHistory,
        isLoading: false,
        clearError: true,
      );

      debugPrint('[AnalysisProvider] Successfully enriched message $messageIndex with segmentation data');
    } on ApiError catch (e) {
      debugPrint('[AnalysisProvider] API error enriching with segmentation: $e');
      state = state.copyWith(
        isLoading: false,
        error: e,
      );
    } catch (e) {
      debugPrint('[AnalysisProvider] Unexpected error enriching with segmentation: $e');
      state = state.copyWith(
        isLoading: false,
        error: ApiError.fromException(e),
      );
    }
  }

  /// Enrich video frames with segmentation data
  Future<void> enrichWithVideoSegmentation(int messageIndex) async {
    if (messageIndex < 0 || messageIndex >= state.conversationHistory.length) {
      debugPrint('[AnalysisProvider] Invalid message index: $messageIndex');
      return;
    }

    final message = state.conversationHistory[messageIndex];

    // Check if we have video frames
    if (message.response.videoFrames == null || !message.response.videoFrames!.isValid) {
      debugPrint('[AnalysisProvider] No video frames available for message $messageIndex');
      return;
    }

    // Check if already has segmentation data on any frame
    final hasSegments = message.response.videoFrames!.frames.any((frame) => frame.hasSegments);
    if (hasSegments) {
      debugPrint('[AnalysisProvider] Message $messageIndex already has video segmentation data');
      return;
    }

    // Check if we have a session ID
    if (message.response.sessionId.isEmpty) {
      debugPrint('[AnalysisProvider] No session ID available for message $messageIndex');
      return;
    }

    try {
      state = state.copyWith(isLoading: true, clearError: true);
      debugPrint('[AnalysisProvider] Enriching message $messageIndex with video segmentation data');

      // Call video segmentation API
      final enrichedMetadata = await _apiService.segmentVideoFrames(
        sessionId: message.response.sessionId,
        confidence: 0.7,
      );

      debugPrint('[AnalysisProvider] Received enriched metadata with ${enrichedMetadata.framesCount} frames');

      // Create updated response by replacing video frames metadata
      final updatedResponse = VisionResponse(
        response: message.response.response,
        modelUsed: message.response.modelUsed,
        processingTime: message.response.processingTime,
        sessionId: message.response.sessionId,
        annotatedImageUrl: message.response.annotatedImageUrl,
        hasAnnotatedImage: message.response.hasAnnotatedImage,
        detections: message.response.detections,
        segments: message.response.segments,
        imageMetadata: message.response.imageMetadata,
        videoFrames: enrichedMetadata, // Replace with enriched metadata
      );

      // Update the message
      final updatedMessage = message.copyWith(response: updatedResponse);

      // Update conversation history
      final updatedHistory = List<ConversationMessage>.from(state.conversationHistory);
      updatedHistory[messageIndex] = updatedMessage;

      state = state.copyWith(
        conversationHistory: updatedHistory,
        isLoading: false,
        clearError: true,
      );

      debugPrint('[AnalysisProvider] Successfully enriched message $messageIndex with video segmentation data');
    } on ApiError catch (e) {
      debugPrint('[AnalysisProvider] API error enriching with video segmentation: $e');
      state = state.copyWith(
        isLoading: false,
        error: e,
      );
    } catch (e) {
      debugPrint('[AnalysisProvider] Unexpected error enriching with video segmentation: $e');
      state = state.copyWith(
        isLoading: false,
        error: ApiError.fromException(e),
      );
    }
  }

  /// Clear conversation history
  void clearConversation() {
    state = state.copyWith(conversationHistory: [], clearError: true);
  }

  /// Clear error
  void clearError() {
    state = state.copyWith(clearError: true);
  }

  /// Start new session
  void startNewSession() {
    state = const AnalysisState();
  }

  /// Check backend health
  Future<bool> checkBackendHealth() async {
    try {
      return await _apiService.checkHealth();
    } catch (e) {
      debugPrint('Health check error: $e');
      return false;
    }
  }
}

/// Provider for vision analysis
final analysisProvider = StateNotifierProvider<AnalysisNotifier, AnalysisState>((ref) {
  final apiService = ref.watch(apiServiceProvider);
  return AnalysisNotifier(apiService);
});

/// Provider for conversation history
final conversationHistoryProvider = Provider<List<ConversationMessage>>((ref) {
  return ref.watch(analysisProvider).conversationHistory;
});

/// Provider for analysis loading state
final analysisLoadingProvider = Provider<bool>((ref) {
  return ref.watch(analysisProvider).isLoading;
});

/// Provider for analysis error
final analysisErrorProvider = Provider<ApiError?>((ref) {
  return ref.watch(analysisProvider).error;
});

/// Provider for session ID
final sessionIdProvider = Provider<String?>((ref) {
  return ref.watch(analysisProvider).sessionId;
});
