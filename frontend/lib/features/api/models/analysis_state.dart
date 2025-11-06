import 'conversation_message.dart';
import 'api_error.dart';

/// State for vision analysis
class AnalysisState {
  final List<ConversationMessage> conversationHistory;
  final bool isLoading;
  final ApiError? error;
  final String? sessionId;
  final String? currentMediaHash;

  const AnalysisState({
    this.conversationHistory = const [],
    this.isLoading = false,
    this.error,
    this.sessionId,
    this.currentMediaHash,
  });

  AnalysisState copyWith({
    List<ConversationMessage>? conversationHistory,
    bool? isLoading,
    ApiError? error,
    String? sessionId,
    String? currentMediaHash,
    bool clearError = false,
  }) {
    return AnalysisState(
      conversationHistory: conversationHistory ?? this.conversationHistory,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      sessionId: sessionId ?? this.sessionId,
      currentMediaHash: currentMediaHash ?? this.currentMediaHash,
    );
  }

  bool get hasMessages => conversationHistory.isNotEmpty;
  bool get hasError => error != null;
}
