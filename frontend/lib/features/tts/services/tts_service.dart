import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';

/// Text-to-speech service
class TtsService {
  final FlutterTts _tts = FlutterTts();
  bool _isInitialized = false;

  // Callbacks
  Function()? onStart;
  Function()? onComplete;
  Function()? onPause;
  Function()? onContinue;
  Function()? onCancel;
  Function(String)? onError;
  Function(String, int, int)? onProgress; // text, start, end

  /// Initialize TTS
  Future<void> initialize() async {
    if (_isInitialized) return;

    try {
      // Set up handlers
      _tts.setStartHandler(() {
        debugPrint('TTS: Started speaking');
        onStart?.call();
      });

      _tts.setCompletionHandler(() {
        debugPrint('TTS: Completed speaking');
        onComplete?.call();
      });

      _tts.setPauseHandler(() {
        debugPrint('TTS: Paused');
        onPause?.call();
      });

      _tts.setContinueHandler(() {
        debugPrint('TTS: Continued');
        onContinue?.call();
      });

      _tts.setCancelHandler(() {
        debugPrint('TTS: Cancelled');
        onCancel?.call();
      });

      _tts.setErrorHandler((message) {
        debugPrint('TTS Error: $message');
        onError?.call(message);
      });

      _tts.setProgressHandler((text, start, end, word) {
        debugPrint('TTS Progress: "$word" at $start-$end');
        onProgress?.call(text, start, end);
      });

      _isInitialized = true;
    } catch (e) {
      debugPrint('Failed to initialize TTS: $e');
    }
  }

  /// Speak text
  Future<void> speak(String text) async {
    if (!_isInitialized) {
      await initialize();
    }

    try {
      await _tts.speak(text);
    } catch (e) {
      debugPrint('TTS speak error: $e');
      onError?.call(e.toString());
    }
  }

  /// Pause speaking
  Future<void> pause() async {
    try {
      await _tts.pause();
    } catch (e) {
      debugPrint('TTS pause error: $e');
    }
  }

  /// Stop speaking
  Future<void> stop() async {
    try {
      await _tts.stop();
    } catch (e) {
      debugPrint('TTS stop error: $e');
    }
  }

  /// Set language
  Future<void> setLanguage(String language) async {
    try {
      await _tts.setLanguage(language);
    } catch (e) {
      debugPrint('TTS setLanguage error: $e');
    }
  }

  /// Set speech rate (0.0 - 1.0, default 0.5)
  Future<void> setSpeechRate(double rate) async {
    try {
      await _tts.setSpeechRate(rate);
    } catch (e) {
      debugPrint('TTS setSpeechRate error: $e');
    }
  }

  /// Set volume (0.0 - 1.0, default 1.0)
  Future<void> setVolume(double volume) async {
    try {
      await _tts.setVolume(volume);
    } catch (e) {
      debugPrint('TTS setVolume error: $e');
    }
  }

  /// Set pitch (0.5 - 2.0, default 1.0)
  Future<void> setPitch(double pitch) async {
    try {
      await _tts.setPitch(pitch);
    } catch (e) {
      debugPrint('TTS setPitch error: $e');
    }
  }

  /// Get available languages
  Future<List<String>> getLanguages() async {
    try {
      final languages = await _tts.getLanguages;
      return List<String>.from(languages);
    } catch (e) {
      debugPrint('TTS getLanguages error: $e');
      return [];
    }
  }

  /// Get available voices
  Future<List<Map<String, String>>> getVoices() async {
    try {
      final voices = await _tts.getVoices;
      return List<Map<String, String>>.from(
        voices.map((voice) => Map<String, String>.from(voice)),
      );
    } catch (e) {
      debugPrint('TTS getVoices error: $e');
      return [];
    }
  }

  /// Set voice by name
  Future<void> setVoice(Map<String, String> voice) async {
    try {
      await _tts.setVoice(voice);
    } catch (e) {
      debugPrint('TTS setVoice error: $e');
    }
  }

  /// Check if currently speaking
  Future<bool> isSpeaking() async {
    try {
      final speaking = await _tts.awaitSpeakCompletion(false);
      return speaking;
    } catch (e) {
      return false;
    }
  }

  /// Dispose resources
  void dispose() {
    _tts.stop();
  }
}
