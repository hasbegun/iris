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

  /// Start voice recording
  Future<void> startRecording() async {
    try {
      state = state.copyWith(isRecording: true, clearError: true);

      // Initialize speech service if needed
      final initialized = await _speechService.initialize();
      if (!initialized) {
        state = state.copyWith(
          isRecording: false,
          error: 'Speech recognition not available',
        );
        return;
      }

      // Start listening
      state = state.copyWith(isListening: true);
      await _speechService.startListening(
        onResult: (recognizedWords) {
          state = state.copyWith(text: recognizedWords);
        },
      );
    } catch (e) {
      debugPrint('Error starting recording: $e');
      state = state.copyWith(
        isRecording: false,
        isListening: false,
        error: 'Failed to start recording: ${e.toString()}',
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
        error: 'Failed to stop recording: ${e.toString()}',
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
        clearError: true,
      );
    } catch (e) {
      debugPrint('Error canceling recording: $e');
      state = state.copyWith(
        isRecording: false,
        isListening: false,
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
