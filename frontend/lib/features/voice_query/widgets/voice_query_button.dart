import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_hooks/flutter_hooks.dart';
import 'package:hooks_riverpod/hooks_riverpod.dart';
import '../providers/voice_query_provider.dart';

/// Voice query button with push-to-talk interaction
///
/// User holds button to speak, releases to process
class VoiceQueryButton extends HookConsumerWidget {
  final Uint8List? currentFrame;
  final String? sessionId;
  final VoidCallback? onQueryStart;
  final VoidCallback? onQueryComplete;

  const VoiceQueryButton({
    super.key,
    this.currentFrame,
    this.sessionId,
    this.onQueryStart,
    this.onQueryComplete,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final voiceQueryState = ref.watch(voiceQueryProvider);
    final voiceQueryNotifier = ref.read(voiceQueryProvider.notifier);

    // Animation controllers
    final animationController = useAnimationController(
      duration: const Duration(milliseconds: 1500),
    );

    final scaleAnimation = useAnimation(
      Tween<double>(begin: 1.0, end: 1.2).animate(
        CurvedAnimation(
          parent: animationController,
          curve: Curves.easeInOut,
        ),
      ),
    );

    // Start/stop animation based on state
    useEffect(() {
      if (voiceQueryState.isListening) {
        animationController.repeat(reverse: true);
      } else {
        animationController.stop();
        animationController.reset();
      }
      return null;
    }, [voiceQueryState.isListening]);

    // Handle long press
    final handleLongPressStart = useCallback(() async {
      // Notify caller that query is starting (they can capture a frame)
      onQueryStart?.call();

      // Wait a brief moment for frame capture if needed
      await Future.delayed(const Duration(milliseconds: 100));

      if (currentFrame == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('No camera frame available. Please start detection first.'),
            duration: Duration(seconds: 2),
          ),
        );
        return;
      }

      voiceQueryNotifier.startVoiceQuery(
        currentFrame: currentFrame!,
        sessionId: sessionId,
        shouldSpeak: true,
      );
    }, [currentFrame, sessionId]);

    final handleLongPressEnd = useCallback(() {
      // Query already started, just wait for completion
      if (voiceQueryState.lastResponse != null) {
        onQueryComplete?.call();
      }
    }, [voiceQueryState.lastResponse]);

    // Determine button appearance based on state
    Color buttonColor;
    IconData buttonIcon;
    String tooltip;

    if (voiceQueryState.isListening) {
      buttonColor = Colors.red;
      buttonIcon = Icons.mic;
      tooltip = 'Listening...';
    } else if (voiceQueryState.isProcessing) {
      buttonColor = Colors.orange;
      buttonIcon = Icons.query_stats;
      tooltip = 'Analyzing...';
    } else if (voiceQueryState.isSpeaking) {
      buttonColor = Colors.green;
      buttonIcon = Icons.volume_up;
      tooltip = 'Speaking...';
    } else if (voiceQueryState.hasError) {
      buttonColor = Colors.red.shade700;
      buttonIcon = Icons.error_outline;
      tooltip = 'Error occurred';
    } else {
      buttonColor = Colors.blue;
      buttonIcon = Icons.mic_none;
      tooltip = 'Hold to speak';
    }

    return Stack(
      alignment: Alignment.center,
      children: [
        // Pulsing ring during listening
        if (voiceQueryState.isListening)
          Transform.scale(
            scale: scaleAnimation,
            child: Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(
                  color: buttonColor.withOpacity(0.5),
                  width: 3,
                ),
              ),
            ),
          ),

        // Main button
        GestureDetector(
          onLongPressStart: (_) => handleLongPressStart(),
          onLongPressEnd: (_) => handleLongPressEnd(),
          child: Tooltip(
            message: tooltip,
            child: Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(
                color: buttonColor,
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color: buttonColor.withOpacity(0.4),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Icon(
                buttonIcon,
                color: Colors.white,
                size: 32,
              ),
            ),
          ),
        ),

        // Processing indicator
        if (voiceQueryState.isProcessing)
          const SizedBox(
            width: 64,
            height: 64,
            child: CircularProgressIndicator(
              color: Colors.white,
              strokeWidth: 3,
            ),
          ),
      ],
    );
  }
}

/// Voice query status indicator
///
/// Shows current status and last response
class VoiceQueryStatusIndicator extends HookConsumerWidget {
  const VoiceQueryStatusIndicator({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final voiceQueryState = ref.watch(voiceQueryProvider);

    if (!voiceQueryState.isActive && voiceQueryState.lastResponse == null) {
      return const SizedBox.shrink();
    }

    return Container(
      margin: const EdgeInsets.all(16),
      constraints: const BoxConstraints(
        maxHeight: 200, // Limit max height
      ),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.7),
        borderRadius: BorderRadius.circular(12),
      ),
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(12),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Status
            Row(
              children: [
                Icon(
                  voiceQueryState.isListening
                      ? Icons.mic
                      : voiceQueryState.isProcessing
                          ? Icons.query_stats
                          : voiceQueryState.isSpeaking
                              ? Icons.volume_up
                              : Icons.check_circle,
                  color: Colors.white,
                  size: 16,
                ),
                const SizedBox(width: 8),
                Text(
                  voiceQueryState.statusText,
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                // Stop button when speaking
                if (voiceQueryState.isSpeaking) ...[
                  const Spacer(),
                  InkWell(
                    onTap: () {
                      ref.read(voiceQueryProvider.notifier).stopSpeaking();
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 6,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.red.withOpacity(0.8),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            Icons.stop,
                            color: Colors.white,
                            size: 14,
                          ),
                          SizedBox(width: 4),
                          Text(
                            'Stop',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ],
            ),

            // Last query
            if (voiceQueryState.lastQuery != null) ...[
              const SizedBox(height: 8),
              Text(
                'Q: ${voiceQueryState.lastQuery}',
                style: const TextStyle(
                  color: Colors.white70,
                  fontSize: 12,
                ),
              ),
            ],

            // Last response (scrollable)
            if (voiceQueryState.lastResponse != null) ...[
              const SizedBox(height: 4),
              Text(
                'A: ${voiceQueryState.lastResponse!.response}',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                ),
              ),
            ],

            // Error
            if (voiceQueryState.hasError) ...[
              const SizedBox(height: 8),
              Row(
                children: [
                  const Icon(Icons.error, color: Colors.redAccent, size: 16),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      voiceQueryState.error!,
                      style: const TextStyle(
                        color: Colors.redAccent,
                        fontSize: 12,
                      ),
                    ),
                  ),
                ],
              ),
            ],

            // Detected objects
            if (voiceQueryState.lastResponse?.hasDetections == true) ...[
              const SizedBox(height: 8),
              Wrap(
                spacing: 4,
                children: voiceQueryState.lastResponse!.detectedObjects!
                    .map((obj) => Chip(
                          label: Text(
                            obj,
                            style: const TextStyle(fontSize: 10),
                          ),
                          backgroundColor: Colors.blue.withOpacity(0.3),
                          padding: EdgeInsets.zero,
                          materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                        ))
                    .toList(),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
