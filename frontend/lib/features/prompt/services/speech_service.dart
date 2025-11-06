import 'package:flutter/material.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

/// Service for speech-to-text functionality
class SpeechService {
  final stt.SpeechToText _speech = stt.SpeechToText();
  bool _isInitialized = false;

  /// Initialize speech recognition
  Future<bool> initialize() async {
    if (_isInitialized) return true;

    try {
      _isInitialized = await _speech.initialize(
        onError: (error) => debugPrint('Speech error: $error'),
        onStatus: (status) => debugPrint('Speech status: $status'),
      );
      return _isInitialized;
    } catch (e) {
      debugPrint('Failed to initialize speech recognition: $e');
      return false;
    }
  }

  /// Check if speech recognition is available
  bool get isAvailable => _isInitialized && _speech.isAvailable;

  /// Check if currently listening
  bool get isListening => _speech.isListening;

  /// Start listening for speech
  Future<void> startListening({
    required Function(String) onResult,
    String localeId = 'en_US',
  }) async {
    if (!_isInitialized) {
      final initialized = await initialize();
      if (!initialized) {
        throw Exception('Speech recognition not available');
      }
    }

    await _speech.listen(
      onResult: (result) {
        onResult(result.recognizedWords);
      },
      localeId: localeId,
      listenOptions: stt.SpeechListenOptions(
        listenMode: stt.ListenMode.confirmation,
        cancelOnError: true,
        partialResults: true,
      ),
    );
  }

  /// Stop listening
  Future<void> stopListening() async {
    if (_speech.isListening) {
      await _speech.stop();
    }
  }

  /// Cancel listening
  Future<void> cancelListening() async {
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

  /// Dispose resources
  void dispose() {
    _speech.stop();
  }
}
