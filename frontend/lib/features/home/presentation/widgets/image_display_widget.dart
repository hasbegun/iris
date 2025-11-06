import 'package:flutter/material.dart';
import '../../models/media_item.dart';

/// Widget to display a selected image
class ImageDisplayWidget extends StatelessWidget {
  final MediaItem mediaItem;
  final VoidCallback? onRemove;

  const ImageDisplayWidget({
    super.key,
    required this.mediaItem,
    this.onRemove,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      clipBehavior: Clip.antiAlias,
      child: Stack(
        children: [
          // Image
          Center(
            child: Image.file(
              mediaItem.file,
              fit: BoxFit.contain,
              errorBuilder: (context, error, stackTrace) {
                return Container(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.error, color: Colors.red, size: 48),
                      const SizedBox(height: 8),
                      Text(
                        'Failed to load image',
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ],
                  ),
                );
              },
            ),
          ),

          // Remove button (top-right)
          if (onRemove != null)
            Positioned(
              top: 8,
              right: 8,
              child: Material(
                color: Colors.black.withOpacity(0.5),
                shape: const CircleBorder(),
                child: InkWell(
                  onTap: onRemove,
                  customBorder: const CircleBorder(),
                  child: const Padding(
                    padding: EdgeInsets.all(8),
                    child: Icon(
                      Icons.close,
                      color: Colors.white,
                      size: 20,
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
