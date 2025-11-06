import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/prompt_state.dart';
import '../services/speech_service.dart';

/// Prompt provider notifier
class PromptNotifier extends StateNotifier<PromptState> {
  final SpeechService _speechService;

  PromptNotifier(this._speechService) : super(const PromptState());

  /// Update prompt text
  void updateText(String text) {
    state = state.copyWith(text: text, clearError: true);
  }

  /// Clear prompt text
  void clearText() {
    state = state.copyWith(text: '', clearError: true);
  }

  /// Start voice recording with enhanced error handling
  /// Note: Permissions should be requested via PermissionService before calling this
  Future<void> startRecording() async {
    try {
      state = state.copyWith(isRecording: true, clearError: true);

      // Initialize speech service if needed
      final initialized = await _speechService.initialize();
      if (!initialized) {
        state = state.copyWith(
          isRecording: false,
          error: 'Speech recognition not available. Please check permissions in Settings.',
        );
        return;
      }

      // Start listening with callbacks
      state = state.copyWith(isListening: true);
      await _speechService.startListening(
        onResult: (result) {
          state = state.copyWith(
            text: result.text,
            confidence: result.confidence,
            isFinalResult: result.isFinal,
          );
        },
        onError: (errorMsg) {
          state = state.copyWith(
            isRecording: false,
            isListening: false,
            error: errorMsg,
          );
        },
        onTimeout: () {
          state = state.copyWith(
            isRecording: false,
            isListening: false,
            error: 'Recording timeout. Please try again.',
          );
        },
      );
    } catch (e) {
      debugPrint('Error starting recording: $e');
      state = state.copyWith(
        isRecording: false,
        isListening: false,
        error: 'Failed to start recording. Please check your microphone permissions.',
      );
    }
  }

  /// Stop voice recording
  Future<void> stopRecording() async {
    try {
      await _speechService.stopListening();
      state = state.copyWith(
        isRecording: false,
        isListening: false,
        clearError: true,
      );
    } catch (e) {
      debugPrint('Error stopping recording: $e');
      state = state.copyWith(
        isRecording: false,
        isListening: false,
        error: 'Failed to stop recording',
      );
    }
  }

  /// Cancel voice recording
  Future<void> cancelRecording() async {
    try {
      await _speechService.cancelListening();
      state = state.copyWith(
        isRecording: false,
        isListening: false,
        text: '', // Clear text on cancel
        confidence: 0.0,
        isFinalResult: false,
        clearError: true,
      );
    } catch (e) {
      debugPrint('Error canceling recording: $e');
      state = state.copyWith(
        isRecording: false,
        isListening: false,
        confidence: 0.0,
        isFinalResult: false,
      );
    }
  }

  /// Clear error
  void clearError() {
    state = state.copyWith(clearError: true);
  }

  @override
  void dispose() {
    _speechService.dispose();
    super.dispose();
  }
}

/// Provider for speech service
final speechServiceProvider = Provider<SpeechService>((ref) {
  return SpeechService();
});

/// Provider for prompt management
final promptProvider = StateNotifierProvider<PromptNotifier, PromptState>((ref) {
  final speechService = ref.watch(speechServiceProvider);
  return PromptNotifier(speechService);
});

/// Provider for prompt text
final promptTextProvider = Provider<String>((ref) {
  return ref.watch(promptProvider).text;
});

/// Provider for recording state
final isRecordingProvider = Provider<bool>((ref) {
  return ref.watch(promptProvider).isRecording;
});

/// Provider for listening state
final isListeningProvider = Provider<bool>((ref) {
  return ref.watch(promptProvider).isListening;
});

/// Provider for prompt error
final promptErrorProvider = Provider<String?>((ref) {
  return ref.watch(promptProvider).error;
});

/// Provider for speech confidence
final speechConfidenceProvider = Provider<double>((ref) {
  return ref.watch(promptProvider).confidence;
});

/// Provider for confidence level string
final confidenceLevelProvider = Provider<String>((ref) {
  return ref.watch(promptProvider).confidenceLevel;
});
