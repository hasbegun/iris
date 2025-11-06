/// Prompt input state
class PromptState {
  final String text;
  final bool isRecording;
  final bool isListening;
  final String? error;
  final double confidence;
  final bool isFinalResult;

  const PromptState({
    this.text = '',
    this.isRecording = false,
    this.isListening = false,
    this.error,
    this.confidence = 0.0,
    this.isFinalResult = false,
  });

  PromptState copyWith({
    String? text,
    bool? isRecording,
    bool? isListening,
    String? error,
    bool clearError = false,
    double? confidence,
    bool? isFinalResult,
  }) {
    return PromptState(
      text: text ?? this.text,
      isRecording: isRecording ?? this.isRecording,
      isListening: isListening ?? this.isListening,
      error: clearError ? null : (error ?? this.error),
      confidence: confidence ?? this.confidence,
      isFinalResult: isFinalResult ?? this.isFinalResult,
    );
  }

  bool get hasText => text.trim().isNotEmpty;

  /// Get confidence level as a string
  String get confidenceLevel {
    if (confidence >= 0.8) return 'high';
    if (confidence >= 0.5) return 'medium';
    return 'low';
  }

  /// Check if confidence is acceptable
  bool get hasGoodConfidence => confidence >= 0.5;
}
