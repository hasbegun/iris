import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../api/providers/analysis_provider.dart';
import '../../api/models/voice_query_response.dart';
import '../../speech/services/speech_service.dart';
import '../../tts/services/tts_service.dart';
import '../services/voice_query_service.dart';
import '../models/voice_query_state.dart';

/// Provider for speech service
final speechServiceProvider = Provider<SpeechService>((ref) {
  return SpeechService();
});

/// Provider for TTS service
final ttsServiceProvider = Provider<TtsService>((ref) {
  return TtsService();
});

/// Provider for voice query service
final voiceQueryServiceProvider = Provider<VoiceQueryService>((ref) {
  final apiService = ref.watch(apiServiceProvider);
  final speechService = ref.watch(speechServiceProvider);
  final ttsService = ref.watch(ttsServiceProvider);

  return VoiceQueryService(
    apiService: apiService,
    speechService: speechService,
    ttsService: ttsService,
  );
});

/// Voice query state notifier
class VoiceQueryNotifier extends StateNotifier<VoiceQueryState> {
  final VoiceQueryService _voiceQueryService;
  final TtsService _ttsService;

  VoiceQueryNotifier(this._voiceQueryService, this._ttsService)
      : super(const VoiceQueryState());

  /// Start voice query workflow
  ///
  /// Captures current frame, listens for voice, sends to backend,
  /// and speaks response
  Future<void> startVoiceQuery({
    required Uint8List currentFrame,
    String? sessionId,
    bool shouldSpeak = true,
  }) async {
    try {
      // Store current frame
      state = state.copyWith(
        currentFrame: currentFrame,
        sessionId: sessionId,
        isListening: true,
        clearError: true,
      );

      debugPrint('[VoiceQueryProvider] Starting voice query');

      // Process voice query
      final response = await _voiceQueryService.processVoiceQuery(
        frameImage: currentFrame,
        sessionId: sessionId,
        shouldSpeak: shouldSpeak,
        onListening: () {
          state = state.copyWith(isListening: true);
        },
        onProcessing: () {
          state = state.copyWith(isListening: false, isProcessing: true);
        },
        onResponse: (response) {
          state = state.copyWith(
            isProcessing: false,
            lastResponse: response,
            lastQuery: response.query,
            sessionId: response.sessionId,
          );
        },
        onError: (error) {
          state = state.copyWith(
            isListening: false,
            isProcessing: false,
            isSpeaking: false,
            error: error,
          );
        },
        onSpeakingStart: () {
          debugPrint('[VoiceQueryProvider] TTS started speaking');
          state = state.copyWith(isSpeaking: true);
        },
        onSpeakingComplete: () {
          debugPrint('[VoiceQueryProvider] TTS completed speaking');
          state = state.copyWith(isSpeaking: false);
        },
      );

      if (response != null) {
        // Add to history
        final updatedHistory = [...state.queryHistory, response];
        state = state.copyWith(
          queryHistory: updatedHistory,
          lastResponse: response,
          lastQuery: response.query,
        );

        debugPrint('[VoiceQueryProvider] Voice query completed successfully');
      }
    } catch (e) {
      debugPrint('[VoiceQueryProvider] Error in voice query: $e');
      state = state.copyWith(
        isListening: false,
        isProcessing: false,
        isSpeaking: false,
        error: e.toString(),
      );
    }
  }

  /// Stop TTS speaking
  Future<void> stopSpeaking() async {
    debugPrint('[VoiceQueryProvider] Stopping TTS');
    await _ttsService.stop();
    state = state.copyWith(isSpeaking: false);
  }

  /// Cancel current voice query
  void cancelVoiceQuery() {
    debugPrint('[VoiceQueryProvider] Cancelling voice query');
    state = state.copyWith(
      isListening: false,
      isProcessing: false,
      isSpeaking: false,
      clearError: true,
    );
  }

  /// Clear error
  void clearError() {
    state = state.copyWith(clearError: true);
  }

  /// Clear history
  void clearHistory() {
    state = state.copyWith(
      queryHistory: [],
      lastResponse: null,
      lastQuery: null,
    );
  }

  /// Check if services are available
  Future<bool> checkServicesAvailable() async {
    final speechAvailable = await _voiceQueryService.isSpeechAvailable();
    final ttsAvailable = await _voiceQueryService.isTtsAvailable();
    return speechAvailable && ttsAvailable;
  }
}

/// Voice query provider
final voiceQueryProvider =
    StateNotifierProvider<VoiceQueryNotifier, VoiceQueryState>((ref) {
  final service = ref.watch(voiceQueryServiceProvider);
  final ttsService = ref.watch(ttsServiceProvider);
  return VoiceQueryNotifier(service, ttsService);
});
