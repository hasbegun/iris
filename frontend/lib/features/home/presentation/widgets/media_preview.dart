import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/media_provider.dart';
import 'image_display_widget.dart';
import 'video_player_widget.dart';

/// Widget to preview selected media (image or video)
class MediaPreview extends ConsumerWidget {
  const MediaPreview({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final mediaItem = ref.watch(selectedMediaProvider);

    if (mediaItem == null) {
      return _buildEmptyState(context);
    }

    return Container(
      height: 400,
      margin: const EdgeInsets.all(16),
      child: mediaItem.isImage
          ? ImageDisplayWidget(
              mediaItem: mediaItem,
              onRemove: () => ref.read(mediaProvider.notifier).clearMedia(),
            )
          : VideoPlayerWidget(
              mediaItem: mediaItem,
              onRemove: () => ref.read(mediaProvider.notifier).clearMedia(),
            ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return Container(
      height: 300,
      margin: const EdgeInsets.all(16),
      child: Card(
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                Icons.image_outlined,
                size: 64,
                color: Theme.of(context).colorScheme.primary.withOpacity(0.5),
              ),
              const SizedBox(height: 16),
              Text(
                'No media selected',
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: Theme.of(context)
                          .colorScheme
                          .onSurface
                          .withOpacity(0.6),
                    ),
              ),
              const SizedBox(height: 8),
              Text(
                'Select an image or video to analyze',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context)
                          .colorScheme
                          .onSurface
                          .withOpacity(0.4),
                    ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}