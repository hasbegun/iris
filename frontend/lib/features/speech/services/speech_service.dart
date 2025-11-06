import 'package:flutter/foundation.dart';
import 'package:speech_to_text/speech_to_text.dart';
import 'package:permission_handler/permission_handler.dart';

/// Voice command types
enum VoiceCommand {
  find,     // "find [object]" - start detection
  stop,     // "stop" - stop detection
  pause,    // "pause" - pause detection
  resume,   // "resume" - resume detection
  unknown,  // Unrecognized command
}

/// Parsed voice command result
class VoiceCommandResult {
  final VoiceCommand command;
  final String? target; // For "find" commands, the object to find
  final String rawText; // Original recognized text

  const VoiceCommandResult({
    required this.command,
    this.target,
    required this.rawText,
  });

  @override
  String toString() {
    if (command == VoiceCommand.find && target != null) {
      return 'Find: $target';
    }
    return command.toString().split('.').last;
  }
}

/// Service for voice command recognition
class SpeechService {
  final SpeechToText _speech = SpeechToText();
  bool _isInitialized = false;
  bool _isListening = false;

  // Callbacks
  Function(VoiceCommandResult)? onCommandRecognized;
  Function(String)? onPartialResult;
  Function(String)? onError;
  VoidCallback? onListeningStart;
  VoidCallback? onListeningStop;

  bool get isInitialized => _isInitialized;
  bool get isListening => _isListening;

  /// Initialize speech recognition
  Future<bool> initialize() async {
    try {
      // Request microphone permission
      final micStatus = await Permission.microphone.request();
      if (!micStatus.isGranted) {
        onError?.call('Microphone permission denied');
        return false;
      }

      // Initialize speech-to-text
      _isInitialized = await _speech.initialize(
        onError: (error) {
          debugPrint('[SpeechService] Error: ${error.errorMsg}');
          onError?.call(error.errorMsg);
          _isListening = false;
          onListeningStop?.call();
        },
        onStatus: (status) {
          debugPrint('[SpeechService] Status: $status');
          if (status == 'done' || status == 'notListening') {
            _isListening = false;
            onListeningStop?.call();
          }
        },
      );

      if (!_isInitialized) {
        onError?.call('Failed to initialize speech recognition');
        return false;
      }

      debugPrint('[SpeechService] Initialized successfully');
      return true;
    } catch (e) {
      debugPrint('[SpeechService] Initialization error: $e');
      onError?.call('Failed to initialize: $e');
      return false;
    }
  }

  /// Start listening for voice commands
  Future<bool> startListening() async {
    if (!_isInitialized) {
      final initialized = await initialize();
      if (!initialized) {
        return false;
      }
    }

    if (_isListening) {
      debugPrint('[SpeechService] Already listening');
      return true;
    }

    try {
      await _speech.listen(
        onResult: (result) {
          final text = result.recognizedWords.toLowerCase().trim();
          debugPrint('[SpeechService] Recognized: $text (final: ${result.finalResult})');

          // Send partial results
          if (!result.finalResult) {
            onPartialResult?.call(text);
          } else {
            // Parse and emit final command
            final command = _parseCommand(text);
            debugPrint('[SpeechService] Parsed command: $command');
            onCommandRecognized?.call(command);
          }
        },
        listenFor: const Duration(seconds: 30),
        pauseFor: const Duration(seconds: 3),
        partialResults: true,
        cancelOnError: true,
        listenMode: ListenMode.confirmation,
      );

      _isListening = true;
      onListeningStart?.call();
      debugPrint('[SpeechService] Started listening');
      return true;
    } catch (e) {
      debugPrint('[SpeechService] Error starting listening: $e');
      onError?.call('Failed to start listening: $e');
      return false;
    }
  }

  /// Stop listening
  Future<void> stopListening() async {
    if (!_isListening) {
      return;
    }

    try {
      await _speech.stop();
      _isListening = false;
      onListeningStop?.call();
      debugPrint('[SpeechService] Stopped listening');
    } catch (e) {
      debugPrint('[SpeechService] Error stopping listening: $e');
    }
  }

  /// Parse voice command from recognized text
  VoiceCommandResult _parseCommand(String text) {
    final words = text.toLowerCase().trim().split(' ');

    if (words.isEmpty) {
      return VoiceCommandResult(
        command: VoiceCommand.unknown,
        rawText: text,
      );
    }

    final firstWord = words[0];

    // Handle "stop" command
    if (firstWord == 'stop' || text.contains('stop')) {
      return VoiceCommandResult(
        command: VoiceCommand.stop,
        rawText: text,
      );
    }

    // Handle "pause" command
    if (firstWord == 'pause' || text.contains('pause')) {
      return VoiceCommandResult(
        command: VoiceCommand.pause,
        rawText: text,
      );
    }

    // Handle "resume" command
    if (firstWord == 'resume' || text.contains('resume') || text.contains('continue')) {
      return VoiceCommandResult(
        command: VoiceCommand.resume,
        rawText: text,
      );
    }

    // Handle "find [object]" command
    // Variations: "find car", "find a car", "look for car", "detect car"
    if (firstWord == 'find' || firstWord == 'look' || firstWord == 'detect' ||
        firstWord == 'search' || text.contains('find')) {
      // Extract target object
      String? target;

      if (firstWord == 'find' && words.length > 1) {
        // "find car" or "find a car"
        target = words.skip(1).where((w) => w != 'a' && w != 'an' && w != 'the').join(' ');
      } else if (firstWord == 'look' && words.length > 2 && words[1] == 'for') {
        // "look for car"
        target = words.skip(2).where((w) => w != 'a' && w != 'an' && w != 'the').join(' ');
      } else if (firstWord == 'detect' && words.length > 1) {
        // "detect car"
        target = words.skip(1).where((w) => w != 'a' && w != 'an' && w != 'the').join(' ');
      } else if (text.contains('find')) {
        // "I want to find car"
        final findIndex = words.indexOf('find');
        if (findIndex < words.length - 1) {
          target = words.skip(findIndex + 1).where((w) => w != 'a' && w != 'an' && w != 'the').join(' ');
        }
      }

      if (target != null && target.isNotEmpty) {
        return VoiceCommandResult(
          command: VoiceCommand.find,
          target: target,
          rawText: text,
        );
      }
    }

    // Unknown command
    return VoiceCommandResult(
      command: VoiceCommand.unknown,
      rawText: text,
    );
  }

  /// Check if speech recognition is available
  Future<bool> isAvailable() async {
    return await _speech.initialize();
  }

  /// Dispose resources
  void dispose() {
    _speech.stop();
    _speech.cancel();
  }
}
