import 'dart:typed_data';
import '../../api/models/voice_query_response.dart';

/// State for voice query workflow
class VoiceQueryState {
  final bool isListening;
  final bool isProcessing;
  final bool isSpeaking;
  final String? lastQuery;
  final VoiceQueryResponse? lastResponse;
  final String? error;
  final List<VoiceQueryResponse> queryHistory;
  final Uint8List? currentFrame;
  final String? sessionId;

  const VoiceQueryState({
    this.isListening = false,
    this.isProcessing = false,
    this.isSpeaking = false,
    this.lastQuery,
    this.lastResponse,
    this.error,
    this.queryHistory = const [],
    this.currentFrame,
    this.sessionId,
  });

  /// Check if currently active (listening, processing, or speaking)
  bool get isActive => isListening || isProcessing || isSpeaking;

  /// Check if idle (not active and no error)
  bool get isIdle => !isActive && error == null;

  /// Check if has error
  bool get hasError => error != null;

  /// Check if has history
  bool get hasHistory => queryHistory.isNotEmpty;

  /// Get current status text
  String get statusText {
    if (isListening) return 'Listening...';
    if (isProcessing) return 'Analyzing...';
    if (isSpeaking) return 'Speaking...';
    if (hasError) return 'Error: $error';
    if (lastResponse != null) return 'Response received';
    return 'Ready';
  }

  /// Copy with modifications
  VoiceQueryState copyWith({
    bool? isListening,
    bool? isProcessing,
    bool? isSpeaking,
    String? lastQuery,
    VoiceQueryResponse? lastResponse,
    String? error,
    bool clearError = false,
    List<VoiceQueryResponse>? queryHistory,
    Uint8List? currentFrame,
    String? sessionId,
  }) {
    return VoiceQueryState(
      isListening: isListening ?? this.isListening,
      isProcessing: isProcessing ?? this.isProcessing,
      isSpeaking: isSpeaking ?? this.isSpeaking,
      lastQuery: lastQuery ?? this.lastQuery,
      lastResponse: lastResponse ?? this.lastResponse,
      error: clearError ? null : (error ?? this.error),
      queryHistory: queryHistory ?? this.queryHistory,
      currentFrame: currentFrame ?? this.currentFrame,
      sessionId: sessionId ?? this.sessionId,
    );
  }
}
