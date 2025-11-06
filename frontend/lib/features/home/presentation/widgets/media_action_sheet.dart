import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:iris/l10n/app_localizations.dart';
import '../../providers/media_provider.dart';
import 'live_camera_widget.dart';

/// Bottom sheet for media selection actions
class MediaActionSheet extends ConsumerWidget {
  const MediaActionSheet({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Handle indicator
            Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.onSurfaceVariant.withValues(alpha: 0.4),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(height: 16),

            // Title
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Row(
                children: [
                  Text(
                    'Add Media',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Actions
            _MediaActionTile(
              icon: Icons.photo_library,
              title: l10n.selectImage,
              subtitle: 'Choose from gallery',
              onTap: () {
                Navigator.pop(context);
                ref.read(mediaProvider.notifier).pickImageFromGallery();
              },
            ),
            _MediaActionTile(
              icon: Icons.video_library,
              title: l10n.selectVideo,
              subtitle: 'Choose from gallery',
              onTap: () {
                Navigator.pop(context);
                ref.read(mediaProvider.notifier).pickVideoFromGallery();
              },
            ),
            _MediaActionTile(
              icon: Icons.videocam,
              title: 'Live Camera',
              subtitle: 'Real-time detection with voice commands',
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => const LiveCameraWidget(),
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _MediaActionTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const _MediaActionTile({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.primaryContainer,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Icon(
          icon,
          color: Theme.of(context).colorScheme.onPrimaryContainer,
          size: 24,
        ),
      ),
      title: Text(
        title,
        style: const TextStyle(fontWeight: FontWeight.w500),
      ),
      subtitle: Text(subtitle),
      onTap: onTap,
    );
  }
}
