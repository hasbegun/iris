import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/tts_state.dart';
import '../services/tts_service.dart';

/// TTS provider notifier
class TtsNotifier extends StateNotifier<TtsState> {
  final TtsService _ttsService;

  TtsNotifier(this._ttsService) : super(const TtsState()) {
    _initialize();
  }

  /// Initialize TTS service with callbacks
  Future<void> _initialize() async {
    await _ttsService.initialize();

    // Set up callbacks
    _ttsService.onStart = () {
      state = state.copyWith(playbackState: TtsPlaybackState.playing);
    };

    _ttsService.onComplete = () {
      state = state.copyWith(
        playbackState: TtsPlaybackState.stopped,
        clearCurrentText: true,
        currentWordStart: 0,
        currentWordEnd: 0,
      );
    };

    _ttsService.onPause = () {
      state = state.copyWith(playbackState: TtsPlaybackState.paused);
    };

    _ttsService.onContinue = () {
      state = state.copyWith(playbackState: TtsPlaybackState.playing);
    };

    _ttsService.onCancel = () {
      state = state.copyWith(
        playbackState: TtsPlaybackState.stopped,
        clearCurrentText: true,
        currentWordStart: 0,
        currentWordEnd: 0,
      );
    };

    _ttsService.onError = (message) {
      state = state.copyWith(
        playbackState: TtsPlaybackState.stopped,
        error: message,
      );
    };

    _ttsService.onProgress = (text, start, end) {
      state = state.copyWith(
        currentWordStart: start,
        currentWordEnd: end,
      );
    };

    // Set default values
    await _ttsService.setSpeechRate(state.speechRate);
    await _ttsService.setVolume(state.volume);
    await _ttsService.setPitch(state.pitch);
  }

  /// Speak text
  Future<void> speak(String text) async {
    try {
      state = state.copyWith(
        currentText: text,
        clearError: true,
      );
      await _ttsService.speak(text);
    } catch (e) {
      debugPrint('Error speaking: $e');
      state = state.copyWith(
        playbackState: TtsPlaybackState.stopped,
        error: e.toString(),
      );
    }
  }

  /// Pause speaking
  Future<void> pause() async {
    await _ttsService.pause();
  }

  /// Stop speaking
  Future<void> stop() async {
    await _ttsService.stop();
    state = state.copyWith(
      playbackState: TtsPlaybackState.stopped,
      clearCurrentText: true,
      currentWordStart: 0,
      currentWordEnd: 0,
    );
  }

  /// Set speech rate
  Future<void> setSpeechRate(double rate) async {
    await _ttsService.setSpeechRate(rate);
    state = state.copyWith(speechRate: rate);
  }

  /// Set volume
  Future<void> setVolume(double volume) async {
    await _ttsService.setVolume(volume);
    state = state.copyWith(volume: volume);
  }

  /// Set pitch
  Future<void> setPitch(double pitch) async {
    await _ttsService.setPitch(pitch);
    state = state.copyWith(pitch: pitch);
  }

  /// Set language
  Future<void> setLanguage(String language) async {
    await _ttsService.setLanguage(language);
  }

  /// Clear error
  void clearError() {
    state = state.copyWith(clearError: true);
  }

  @override
  void dispose() {
    _ttsService.dispose();
    super.dispose();
  }
}

/// Provider for TTS service
final ttsServiceProvider = Provider<TtsService>((ref) {
  return TtsService();
});

/// Provider for TTS management
final ttsProvider = StateNotifierProvider<TtsNotifier, TtsState>((ref) {
  final ttsService = ref.watch(ttsServiceProvider);
  return TtsNotifier(ttsService);
});

/// Provider for TTS playback state
final ttsPlaybackStateProvider = Provider<TtsPlaybackState>((ref) {
  return ref.watch(ttsProvider).playbackState;
});

/// Provider for TTS is playing
final ttsIsPlayingProvider = Provider<bool>((ref) {
  return ref.watch(ttsProvider).isPlaying;
});

/// Provider for TTS is paused
final ttsIsPausedProvider = Provider<bool>((ref) {
  return ref.watch(ttsProvider).isPaused;
});

/// Provider for TTS current text
final ttsCurrentTextProvider = Provider<String?>((ref) {
  return ref.watch(ttsProvider).currentText;
});

/// Provider for TTS error
final ttsErrorProvider = Provider<String?>((ref) {
  return ref.watch(ttsProvider).error;
});

/// Provider for TTS current word position
final ttsCurrentWordPositionProvider = Provider<({int start, int end})>((ref) {
  final state = ref.watch(ttsProvider);
  return (start: state.currentWordStart, end: state.currentWordEnd);
});
