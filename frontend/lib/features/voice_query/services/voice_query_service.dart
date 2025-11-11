import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../../api/services/api_service.dart';
import '../../api/models/voice_query_response.dart';
import '../../api/models/api_error.dart';
import '../../speech/services/speech_service.dart';
import '../../tts/services/tts_service.dart';

/// Service to orchestrate voice query workflow:
/// 1. Capture camera frame
/// 2. Listen to user's voice query
/// 3. Send to backend for analysis
/// 4. Speak response back to user
class VoiceQueryService {
  final ApiService _apiService;
  final SpeechService _speechService;
  final TtsService _ttsService;

  VoiceQueryService({
    required ApiService apiService,
    required SpeechService speechService,
    required TtsService ttsService,
  })  : _apiService = apiService,
        _speechService = speechService,
        _ttsService = ttsService;

  /// Process a complete voice query workflow
  ///
  /// Args:
  ///   frameImage: Camera frame to analyze
  ///   sessionId: Optional session ID for conversation context
  ///   onListening: Callback when speech recognition starts
  ///   onProcessing: Callback when sending to backend
  ///   onResponse: Callback when response is received
  ///   onError: Callback on error
  ///   onSpeakingStart: Callback when TTS starts speaking
  ///   onSpeakingComplete: Callback when TTS completes speaking
  ///   shouldSpeak: Whether to speak the response back (default: true)
  ///
  /// Returns:
  ///   VoiceQueryResponse or null if cancelled/error
  Future<VoiceQueryResponse?> processVoiceQuery({
    required Uint8List frameImage,
    String? sessionId,
    VoidCallback? onListening,
    VoidCallback? onProcessing,
    Function(VoiceQueryResponse)? onResponse,
    Function(String)? onError,
    VoidCallback? onSpeakingStart,
    VoidCallback? onSpeakingComplete,
    bool shouldSpeak = true,
  }) async {
    try {
      // Stop any ongoing TTS first
      await _ttsService.stop();

      // Step 1: Listen for voice query
      debugPrint('[VoiceQueryService] Starting voice query workflow');
      onListening?.call();

      final query = await listenForQuery();

      if (query == null || query.isEmpty) {
        debugPrint('[VoiceQueryService] No query captured');
        onError?.call('No voice input detected');
        return null;
      }

      debugPrint('[VoiceQueryService] Captured query: "$query"');

      // Step 2: Send to backend for analysis
      onProcessing?.call();

      final response = await _apiService.voiceQuery(
        imageBytes: frameImage,
        query: query,
        sessionId: sessionId,
        verifyWithDetection: true,
      );

      debugPrint('[VoiceQueryService] Received response: "${response.response}"');
      onResponse?.call(response);

      // Step 3: Speak response back to user
      if (shouldSpeak && response.response.isNotEmpty) {
        await _speakText(
          response.response,
          onStart: onSpeakingStart,
          onComplete: onSpeakingComplete,
        );
      }

      return response;
    } on ApiError catch (e) {
      debugPrint('[VoiceQueryService] API error: ${e.message}');
      onError?.call(e.message);
      if (shouldSpeak) {
        await _speakText('Sorry, there was an error: ${e.message}');
      }
      return null;
    } catch (e) {
      debugPrint('[VoiceQueryService] Unexpected error: $e');
      onError?.call(e.toString());
      if (shouldSpeak) {
        await _speakText('Sorry, an error occurred');
      }
      return null;
    }
  }

  /// Listen for voice query using speech recognition
  ///
  /// Returns:
  ///   Transcribed query text or null if cancelled/error
  Future<String?> listenForQuery() async {
    try {
      // Initialize speech recognition
      if (!await _speechService.initialize()) {
        debugPrint('[VoiceQueryService] Speech service initialization failed');
        return null;
      }

      // Set up callback to capture text
      String? capturedText;
      bool isComplete = false;

      // Set callbacks
      _speechService.onPartialResult = (text) {
        debugPrint('[VoiceQueryService] Partial result: "$text"');
        capturedText = text;
      };

      _speechService.onCommandRecognized = (result) {
        debugPrint('[VoiceQueryService] Final result: "${result.rawText}"');
        capturedText = result.rawText;
        isComplete = true;
      };

      _speechService.onError = (error) {
        debugPrint('[VoiceQueryService] Speech error: $error');
        isComplete = true;
      };

      // Start listening
      final started = await _speechService.startListening();
      if (!started) {
        debugPrint('[VoiceQueryService] Failed to start listening');
        return null;
      }

      // Wait for speech to complete or timeout after 10 seconds
      final startTime = DateTime.now();
      while (!isComplete && DateTime.now().difference(startTime).inSeconds < 10) {
        await Future.delayed(const Duration(milliseconds: 100));
      }

      // Stop listening
      await _speechService.stopListening();

      return capturedText;
    } catch (e) {
      debugPrint('[VoiceQueryService] Error during speech recognition: $e');
      return null;
    }
  }

  /// Speak text using TTS (internal method)
  Future<void> _speakText(
    String text, {
    VoidCallback? onStart,
    VoidCallback? onComplete,
  }) async {
    try {
      // Set up TTS callbacks
      _ttsService.onStart = () {
        debugPrint('[VoiceQueryService] TTS started');
        onStart?.call();
      };

      _ttsService.onComplete = () {
        debugPrint('[VoiceQueryService] TTS completed');
        onComplete?.call();
      };

      await _ttsService.speak(text);
    } catch (e) {
      debugPrint('[VoiceQueryService] Error speaking text: $e');
      // Call complete callback even on error to reset state
      onComplete?.call();
    }
  }

  /// Check if speech recognition is available
  Future<bool> isSpeechAvailable() async {
    return await _speechService.initialize();
  }

  /// Check if TTS is available
  Future<bool> isTtsAvailable() async {
    // TTS is usually always available, but we can add checks if needed
    return true;
  }

  /// Dispose resources
  void dispose() {
    _speechService.dispose();
    _ttsService.dispose();
  }
}
