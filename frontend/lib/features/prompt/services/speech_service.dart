import 'dart:async';
import 'package:flutter/material.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

/// Result from speech recognition with confidence score
class SpeechResult {
  final String text;
  final double confidence;
  final bool isFinal;

  const SpeechResult({
    required this.text,
    required this.confidence,
    required this.isFinal,
  });
}

/// Service for speech-to-text functionality
class SpeechService {
  final stt.SpeechToText _speech = stt.SpeechToText();
  bool _isInitialized = false;
  Timer? _timeoutTimer;

  /// Default timeout for speech recognition (30 seconds)
  static const Duration defaultTimeout = Duration(seconds: 30);

  /// Initialize speech recognition
  /// The speech_to_text package handles permissions internally when initialize is called
  Future<bool> initialize() async {
    if (_isInitialized) return true;

    debugPrint('[SpeechService] Initializing speech recognition...');

    try {
      debugPrint('[SpeechService] Calling speech.initialize() - this will request permissions if needed');
      _isInitialized = await _speech.initialize(
        onError: (error) {
          debugPrint('[SpeechService] Speech error: $error');
        },
        onStatus: (status) {
          debugPrint('[SpeechService] Speech status: $status');
        },
        debugLogging: true,
      );
      debugPrint('[SpeechService] Initialize result: $_isInitialized');

      if (_isInitialized) {
        debugPrint('[SpeechService] Speech recognition available: ${_speech.isAvailable}');
      } else {
        debugPrint('[SpeechService] Speech recognition initialization failed - permissions may have been denied');
      }

      return _isInitialized;
    } catch (e) {
      debugPrint('[SpeechService] Failed to initialize speech recognition: $e');
      return false;
    }
  }

  /// Check if speech recognition is available
  bool get isAvailable => _isInitialized && _speech.isAvailable;

  /// Check if currently listening
  bool get isListening => _speech.isListening;

  /// Start listening for speech with enhanced features
  Future<void> startListening({
    required Function(SpeechResult) onResult,
    Function(String)? onError,
    VoidCallback? onTimeout,
    String localeId = 'en_US',
    Duration? timeout,
  }) async {
    if (!_isInitialized) {
      final initialized = await initialize();
      if (!initialized) {
        onError?.call('Speech recognition not available on this device');
        throw Exception('Speech recognition not available');
      }
    }

    // Setup timeout
    final timeoutDuration = timeout ?? defaultTimeout;
    _timeoutTimer?.cancel();
    _timeoutTimer = Timer(timeoutDuration, () {
      if (_speech.isListening) {
        stopListening();
        onTimeout?.call();
      }
    });

    try {
      await _speech.listen(
        onResult: (result) {
          onResult(SpeechResult(
            text: result.recognizedWords,
            confidence: result.confidence,
            isFinal: result.finalResult,
          ));
        },
        localeId: localeId,
        listenOptions: stt.SpeechListenOptions(
          listenMode: stt.ListenMode.confirmation,
          cancelOnError: true,
          partialResults: true,
        ),
      );
    } catch (e) {
      _timeoutTimer?.cancel();
      final errorMsg = _getUserFriendlyError(e.toString());
      onError?.call(errorMsg);
      rethrow;
    }
  }

  /// Stop listening and clear timeout
  Future<void> stopListening() async {
    _timeoutTimer?.cancel();
    if (_speech.isListening) {
      await _speech.stop();
    }
  }

  /// Cancel listening and clear timeout
  Future<void> cancelListening() async {
    _timeoutTimer?.cancel();
    if (_speech.isListening) {
      await _speech.cancel();
    }
  }

  /// Get available locales
  Future<List<stt.LocaleName>> getLocales() async {
    if (!_isInitialized) {
      await initialize();
    }
    return _speech.locales();
  }

  /// Get English locales available on the device
  Future<List<stt.LocaleName>> getEnglishLocales() async {
    final locales = await getLocales();
    return locales
        .where((locale) => locale.localeId.startsWith('en_'))
        .toList();
  }

  /// Convert error to user-friendly message
  String _getUserFriendlyError(String error) {
    if (error.contains('permission')) {
      return 'Microphone permission denied. Please enable it in settings.';
    } else if (error.contains('network')) {
      return 'Network error. Speech recognition requires internet connection.';
    } else if (error.contains('not available')) {
      return 'Speech recognition is not available on this device.';
    } else if (error.contains('busy')) {
      return 'Speech recognition is busy. Please try again.';
    } else {
      return 'Failed to recognize speech. Please try again.';
    }
  }

  /// Dispose resources
  void dispose() {
    _timeoutTimer?.cancel();
    _speech.stop();
  }
}
