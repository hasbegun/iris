import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:iris/l10n/app_localizations.dart';
import '../../../../core/providers/permission_provider.dart';
import '../../providers/prompt_provider.dart';

/// Widget for prompt input with text and voice support
class PromptInputWidget extends ConsumerStatefulWidget {
  final VoidCallback? onSubmit;

  const PromptInputWidget({
    super.key,
    this.onSubmit,
  });

  @override
  ConsumerState<PromptInputWidget> createState() => _PromptInputWidgetState();
}

class _PromptInputWidgetState extends ConsumerState<PromptInputWidget> {
  late TextEditingController _controller;
  final FocusNode _focusNode = FocusNode();

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController();
  }

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  Future<void> _handleMicrophonePress() async {
    final permissionService = ref.read(permissionServiceProvider);
    final isRecording = ref.read(isRecordingProvider);

    if (isRecording) {
      // Stop recording
      await ref.read(promptProvider.notifier).stopRecording();
      return;
    }

    // Request microphone permission
    final granted = await permissionService.requestMicrophoneWithDialog(context);
    if (!granted) return;

    // Start recording
    await ref.read(promptProvider.notifier).startRecording();
  }

  void _handleSubmit() {
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    // Update provider state
    ref.read(promptProvider.notifier).updateText(text);

    // Clear text field
    _controller.clear();
    _focusNode.unfocus();

    // Call callback
    widget.onSubmit?.call();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final promptText = ref.watch(promptTextProvider);
    final isRecording = ref.watch(isRecordingProvider);
    final isListening = ref.watch(isListeningProvider);

    // Update text field when speech recognition updates
    if (isRecording && promptText != _controller.text) {
      _controller.text = promptText;
      _controller.selection = TextSelection.fromPosition(
        TextPosition(offset: _controller.text.length),
      );
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        border: Border.all(
          color: Theme.of(context).colorScheme.outline.withValues(alpha: 0.3),
        ),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Input row with text field and buttons
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              // Microphone button
              _MicrophoneButton(
                isRecording: isRecording,
                isListening: isListening,
                onPressed: _handleMicrophonePress,
              ),
              const SizedBox(width: 12),

              // Text field
              Expanded(
                child: TextField(
                  controller: _controller,
                  focusNode: _focusNode,
                  decoration: InputDecoration(
                    hintText: l10n.promptHint,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 12,
                    ),
                  ),
                  maxLines: null,
                  minLines: 1,
                  textInputAction: TextInputAction.send,
                  onSubmitted: (_) => _handleSubmit(),
                  enabled: !isRecording,
                ),
              ),
              const SizedBox(width: 12),

              // Send button
              FilledButton(
                onPressed: _controller.text.trim().isEmpty ? null : _handleSubmit,
                style: FilledButton.styleFrom(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 24,
                    vertical: 16,
                  ),
                ),
                child: const Icon(Icons.send),
              ),
            ],
          ),

          // Recording indicator
          if (isRecording) ...[
            const SizedBox(height: 12),
            _RecordingIndicator(
              isListening: isListening,
              listeningText: l10n.listening,
              startingText: l10n.starting,
            ),
          ],
        ],
      ),
    );
  }
}

/// Microphone button with recording animation
class _MicrophoneButton extends StatelessWidget {
  final bool isRecording;
  final bool isListening;
  final VoidCallback onPressed;

  const _MicrophoneButton({
    required this.isRecording,
    required this.isListening,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: isRecording
            ? Theme.of(context).colorScheme.error.withValues(alpha: 0.1)
            : Theme.of(context).colorScheme.primary.withValues(alpha: 0.1),
      ),
      child: IconButton(
        onPressed: onPressed,
        icon: Icon(
          isRecording ? Icons.stop : Icons.mic,
          color: isRecording
              ? Theme.of(context).colorScheme.error
              : Theme.of(context).colorScheme.primary,
        ),
        iconSize: 28,
        padding: const EdgeInsets.all(12),
      ),
    );
  }
}

/// Recording indicator with animation
class _RecordingIndicator extends StatefulWidget {
  final bool isListening;
  final String listeningText;
  final String startingText;

  const _RecordingIndicator({
    required this.isListening,
    required this.listeningText,
    required this.startingText,
  });

  @override
  State<_RecordingIndicator> createState() => _RecordingIndicatorState();
}

class _RecordingIndicatorState extends State<_RecordingIndicator>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1000),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _animationController,
      builder: (context, child) {
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.error.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Row(
            children: [
              Icon(
                Icons.fiber_manual_record,
                color: Theme.of(context).colorScheme.error,
                size: 16,
              ),
              const SizedBox(width: 8),
              Text(
                widget.isListening ? widget.listeningText : widget.startingText,
                style: TextStyle(
                  color: Theme.of(context).colorScheme.error,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(width: 8),
              SizedBox(
                width: 16,
                height: 16,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(
                    Theme.of(context)
                        .colorScheme
                        .error
                        .withValues(alpha: _animationController.value),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
