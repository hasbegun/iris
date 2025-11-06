import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../tts/providers/tts_provider.dart';

/// Widget that displays text with TTS highlighting
class HighlightedTextDisplay extends ConsumerWidget {
  final String text;
  final TextStyle? style;
  final bool enableHighlight;

  const HighlightedTextDisplay({
    super.key,
    required this.text,
    this.style,
    this.enableHighlight = true,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (!enableHighlight) {
      return SelectableText(text, style: style);
    }

    final isPlaying = ref.watch(ttsIsPlayingProvider);
    final currentText = ref.watch(ttsCurrentTextProvider);
    final wordPosition = ref.watch(ttsCurrentWordPositionProvider);

    // Only highlight if this text is currently being read
    final shouldHighlight = isPlaying && currentText == text;

    if (!shouldHighlight || wordPosition.start == 0 && wordPosition.end == 0) {
      return SelectableText(text, style: style);
    }

    // Build text spans with highlighting
    final spans = <TextSpan>[];

    // Text before highlighted word
    if (wordPosition.start > 0) {
      spans.add(TextSpan(
        text: text.substring(0, wordPosition.start),
        style: style,
      ));
    }

    // Highlighted word (bold)
    if (wordPosition.end <= text.length) {
      spans.add(TextSpan(
        text: text.substring(wordPosition.start, wordPosition.end),
        style: style?.copyWith(
          fontWeight: FontWeight.bold,
          backgroundColor: Theme.of(context).colorScheme.primaryContainer.withValues(alpha: 0.3),
        ),
      ));
    }

    // Text after highlighted word
    if (wordPosition.end < text.length) {
      spans.add(TextSpan(
        text: text.substring(wordPosition.end),
        style: style,
      ));
    }

    return SelectableText.rich(
      TextSpan(children: spans),
    );
  }
}
