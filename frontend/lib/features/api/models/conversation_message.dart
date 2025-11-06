import 'dart:typed_data';
import 'vision_response.dart';

/// A single message in the conversation history
class ConversationMessage {
  final String prompt;
  final VisionResponse response;
  final DateTime timestamp;
  final Uint8List? imageBytes; // Original image for client-side box rendering

  const ConversationMessage({
    required this.prompt,
    required this.response,
    required this.timestamp,
    this.imageBytes, // Optional, backward compatible
  });

  ConversationMessage copyWith({
    String? prompt,
    VisionResponse? response,
    DateTime? timestamp,
    Uint8List? imageBytes,
  }) {
    return ConversationMessage(
      prompt: prompt ?? this.prompt,
      response: response ?? this.response,
      timestamp: timestamp ?? this.timestamp,
      imageBytes: imageBytes ?? this.imageBytes,
    );
  }
}
