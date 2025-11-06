import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:iris/l10n/app_localizations.dart';
import 'package:permission_handler/permission_handler.dart';
import '../../../prompt/providers/prompt_provider.dart' show
    promptProvider,
    promptTextProvider,
    isRecordingProvider,
    isListeningProvider,
    speechConfidenceProvider,
    promptErrorProvider;

/// Compact Gemini-style prompt input widget
class CompactPromptInput extends ConsumerStatefulWidget {
  final Function(String)? onSubmit;
  final VoidCallback? onAttachMedia;
  final VoidCallback? onCancel;
  final bool isLoading;

  const CompactPromptInput({
    super.key,
    this.onSubmit,
    this.onAttachMedia,
    this.onCancel,
    this.isLoading = false,
  });

  @override
  ConsumerState<CompactPromptInput> createState() => _CompactPromptInputState();
}

class _CompactPromptInputState extends ConsumerState<CompactPromptInput> {
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
    final isRecording = ref.read(isRecordingProvider);

    if (isRecording) {
      await ref.read(promptProvider.notifier).stopRecording();
      return;
    }

    // Start recording - speech_to_text will request permissions internally if needed
    debugPrint('[CompactPromptInput] Starting recording...');
    await ref.read(promptProvider.notifier).startRecording();
  }

  void _handleSubmit() {
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    // Update provider with the text
    ref.read(promptProvider.notifier).updateText(text);

    // Clear the input
    _controller.clear();
    _focusNode.unfocus();

    // Call the submit callback with the text
    widget.onSubmit?.call(text);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final promptText = ref.watch(promptTextProvider);
    final isRecording = ref.watch(isRecordingProvider);
    final isListening = ref.watch(isListeningProvider);
    final confidence = ref.watch(speechConfidenceProvider);
    final error = ref.watch(promptErrorProvider);

    // Update text field when speech recognition updates
    if (isRecording && promptText != _controller.text) {
      _controller.text = promptText;
      _controller.selection = TextSelection.fromPosition(
        TextPosition(offset: _controller.text.length),
      );
    }

    final hasText = _controller.text.trim().isNotEmpty;

    return Container(
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        border: Border(
          top: BorderSide(
            color: Theme.of(context).colorScheme.outlineVariant,
            width: 1,
          ),
        ),
      ),
      child: SafeArea(
        top: false,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Recording indicator with confidence
            if (isRecording)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                color: Theme.of(context).colorScheme.errorContainer,
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.fiber_manual_record,
                      color: Theme.of(context).colorScheme.error,
                      size: 16,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      isListening ? l10n.listening : l10n.starting,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.onErrorContainer,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    if (confidence > 0) ...[
                      const SizedBox(width: 12),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: _getConfidenceColor(confidence, context),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          '${(confidence * 100).toInt()}%',
                          style: TextStyle(
                            color: Theme.of(context).colorScheme.onPrimary,
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),

            // Error indicator
            if (error != null && !isRecording)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                color: Theme.of(context).colorScheme.errorContainer,
                child: Row(
                  children: [
                    Icon(
                      Icons.error_outline,
                      color: Theme.of(context).colorScheme.error,
                      size: 16,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        error,
                        style: TextStyle(
                          color: Theme.of(context).colorScheme.onErrorContainer,
                          fontSize: 13,
                        ),
                      ),
                    ),
                    // Show Settings button if error is about permissions
                    if (error.toLowerCase().contains('settings') ||
                        error.toLowerCase().contains('permission'))
                      TextButton(
                        onPressed: () {
                          openAppSettings();
                        },
                        style: TextButton.styleFrom(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          minimumSize: Size.zero,
                          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                        ),
                        child: const Text(
                          'Settings',
                          style: TextStyle(fontSize: 12),
                        ),
                      ),
                    IconButton(
                      icon: const Icon(Icons.close, size: 16),
                      onPressed: () => ref.read(promptProvider.notifier).clearError(),
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                    ),
                  ],
                ),
              ),

            // Input row
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  // Attach media button
                  IconButton(
                    onPressed: widget.isLoading ? null : widget.onAttachMedia,
                    icon: const Icon(Icons.add_circle_outline),
                    tooltip: 'Attach media',
                    iconSize: 28,
                  ),

                  // Text input
                  Expanded(
                    child: Container(
                      decoration: BoxDecoration(
                        color: Theme.of(context).colorScheme.surfaceContainerHighest,
                        borderRadius: BorderRadius.circular(24),
                      ),
                      child: TextField(
                        controller: _controller,
                        focusNode: _focusNode,
                        decoration: InputDecoration(
                          hintText: l10n.promptHint,
                          border: InputBorder.none,
                          contentPadding: const EdgeInsets.symmetric(
                            horizontal: 20,
                            vertical: 12,
                          ),
                        ),
                        maxLines: null,
                        minLines: 1,
                        textInputAction: TextInputAction.send,
                        onSubmitted: (_) => _handleSubmit(),
                        onChanged: (_) => setState(() {}),
                        enabled: !isRecording && !widget.isLoading,
                      ),
                    ),
                  ),

                  const SizedBox(width: 4),

                  // Voice, Send, or Loading button
                  if (widget.isLoading)
                    // Show spinner with cancel option during loading
                    SizedBox(
                      width: 28,
                      height: 28,
                      child: Stack(
                        alignment: Alignment.center,
                        children: [
                          const SizedBox(
                            width: 24,
                            height: 24,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          ),
                          Positioned.fill(
                            child: Material(
                              color: Colors.transparent,
                              child: InkWell(
                                onTap: widget.onCancel,
                                customBorder: const CircleBorder(),
                                child: Container(),
                              ),
                            ),
                          ),
                        ],
                      ),
                    )
                  else if (hasText)
                    IconButton(
                      onPressed: _handleSubmit,
                      icon: const Icon(Icons.send),
                      tooltip: l10n.send,
                      iconSize: 28,
                    )
                  else
                    IconButton(
                      onPressed: _handleMicrophonePress,
                      icon: Icon(
                        isRecording ? Icons.stop : Icons.mic,
                      ),
                      tooltip: isRecording ? 'Stop recording' : 'Voice input',
                      iconSize: 28,
                      color: isRecording
                          ? Theme.of(context).colorScheme.error
                          : null,
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Get color based on confidence level
  Color _getConfidenceColor(double confidence, BuildContext context) {
    if (confidence >= 0.8) {
      return Colors.green.shade700;
    } else if (confidence >= 0.5) {
      return Colors.orange.shade700;
    } else {
      return Colors.red.shade700;
    }
  }
}
