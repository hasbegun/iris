/// Prompt input state
class PromptState {
  final String text;
  final bool isRecording;
  final bool isListening;
  final String? error;

  const PromptState({
    this.text = '',
    this.isRecording = false,
    this.isListening = false,
    this.error,
  });

  PromptState copyWith({
    String? text,
    bool? isRecording,
    bool? isListening,
    String? error,
    bool clearError = false,
  }) {
    return PromptState(
      text: text ?? this.text,
      isRecording: isRecording ?? this.isRecording,
      isListening: isListening ?? this.isListening,
      error: clearError ? null : (error ?? this.error),
    );
  }

  bool get hasText => text.trim().isNotEmpty;
}
