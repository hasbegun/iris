import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:iris/l10n/app_localizations.dart';
import '../../api/providers/analysis_provider.dart';
import '../providers/media_provider.dart';
import 'widgets/compact_prompt_input.dart';
import 'widgets/media_action_sheet.dart';
import 'widgets/media_preview.dart';
import 'widgets/response_display.dart';

/// Redesigned home screen with Gemini-inspired UI
class HomeScreenRedesigned extends ConsumerWidget {
  const HomeScreenRedesigned({super.key});

  void _showMediaActionSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (context) => const MediaActionSheet(),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final mediaError = ref.watch(mediaErrorProvider);
    final selectedMedia = ref.watch(selectedMediaProvider);
    final analysisError = ref.watch(analysisErrorProvider);
    final analysisLoading = ref.watch(analysisLoadingProvider);
    final conversationHistory = ref.watch(conversationHistoryProvider);
    final isMediaLoading = ref.watch(mediaLoadingProvider);

    // Show media error snackbar
    if (mediaError != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(mediaError),
            backgroundColor: Colors.red,
            action: SnackBarAction(
              label: 'Dismiss',
              textColor: Colors.white,
              onPressed: () {
                ref.read(mediaProvider.notifier).clearError();
              },
            ),
          ),
        );
        ref.read(mediaProvider.notifier).clearError();
      });
    }

    // Show analysis error snackbar
    if (analysisError != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(analysisError.message),
            backgroundColor: Colors.red,
            action: SnackBarAction(
              label: 'Dismiss',
              textColor: Colors.white,
              onPressed: () {
                ref.read(analysisProvider.notifier).clearError();
              },
            ),
          ),
        );
        ref.read(analysisProvider.notifier).clearError();
      });
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.appTitle),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () {
              Navigator.pushNamed(context, '/settings');
            },
          ),
        ],
      ),
      body: Stack(
        children: [
          Column(
            children: [
              // Scrollable content area
              Expanded(
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // Media Preview (only show if media is selected)
                  if (selectedMedia != null)
                    const MediaPreview()
                  else
                    // Empty state with call to action
                    Container(
                      height: 200,
                      margin: const EdgeInsets.all(16),
                      child: Card(
                        child: InkWell(
                          onTap: () => _showMediaActionSheet(context),
                          borderRadius: BorderRadius.circular(12),
                          child: Center(
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(
                                  Icons.add_photo_alternate_outlined,
                                  size: 64,
                                  color: Theme.of(context)
                                      .colorScheme
                                      .primary
                                      .withValues(alpha: 0.5),
                                ),
                                const SizedBox(height: 16),
                                Text(
                                  'Tap to add media',
                                  style: Theme.of(context)
                                      .textTheme
                                      .titleMedium
                                      ?.copyWith(
                                        color: Theme.of(context)
                                            .colorScheme
                                            .onSurface
                                            .withValues(alpha: 0.6),
                                      ),
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  'Select images or videos to analyze',
                                  style: Theme.of(context)
                                      .textTheme
                                      .bodySmall
                                      ?.copyWith(
                                        color: Theme.of(context)
                                            .colorScheme
                                            .onSurface
                                            .withValues(alpha: 0.4),
                                      ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ),

                  // Conversation History
                  if (conversationHistory.isNotEmpty)
                    ...conversationHistory.asMap().entries.map((entry) {
                      final index = entry.key;
                      final message = entry.value;
                      return Padding(
                        padding: const EdgeInsets.fromLTRB(8, 5, 5, 8),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            // User prompt
                            Card(
                              color: Theme.of(context).colorScheme.primaryContainer,
                              child: Padding(
                                padding: const EdgeInsets.all(12),
                                child: Row(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Icon(
                                      Icons.person,
                                      color: Theme.of(context).colorScheme.onPrimaryContainer,
                                      size: 20,
                                    ),
                                    const SizedBox(width: 8),
                                    Expanded(
                                      child: Text(
                                        message.prompt,
                                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                          color: Theme.of(context).colorScheme.onPrimaryContainer,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                            const SizedBox(height: 8),
                            // AI response
                            ResponseDisplay(
                              response: message.response,
                              imageBytes: message.imageBytes,
                              onRequestSegmentation: () {
                                // Trigger segmentation enrichment for this message
                                debugPrint('[HomeScreen] Requesting segmentation for message at index $index');

                                // Detect if this is a video or image
                                final hasVideoFrames = message.response.videoFrames != null &&
                                                      message.response.videoFrames!.isValid;

                                if (hasVideoFrames) {
                                  debugPrint('[HomeScreen] Enriching with video segmentation');
                                  ref.read(analysisProvider.notifier).enrichWithVideoSegmentation(index);
                                } else {
                                  debugPrint('[HomeScreen] Enriching with image segmentation');
                                  ref.read(analysisProvider.notifier).enrichWithSegmentation(index);
                                }
                              },
                            ),
                          ],
                        ),
                      );
                    }),

                      // Add bottom padding to clear the fixed prompt input
                      const SizedBox(height: 60),
                    ],
                  ),
                ),
              ),

              // Fixed prompt input at bottom
              CompactPromptInput(
                isLoading: analysisLoading,
                onAttachMedia: () => _showMediaActionSheet(context),
                onCancel: () {
                  // TODO: Implement proper cancellation
                  // For now, just clear the loading state
                  ref.read(analysisProvider.notifier).clearError();
                },
                onSubmit: (text) async {
                  // Check if media is selected
                  if (selectedMedia == null) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(l10n.noMediaSelected),
                        backgroundColor: Colors.orange,
                      ),
                    );
                    return;
                  }

                  // Submit to backend with the provided text
                  await ref.read(analysisProvider.notifier).analyzeMedia(
                        mediaItem: selectedMedia,
                        prompt: text,
                      );
                },
              ),
            ],
          ),

          // Loading overlay (only for media loading)
          if (isMediaLoading)
            Positioned.fill(
              child: Container(
                color: Colors.black.withValues(alpha: 0.3),
                child: const Center(
                  child: Card(
                    child: Padding(
                      padding: EdgeInsets.all(24),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          CircularProgressIndicator(),
                          SizedBox(height: 16),
                          Text('Loading media...'),
                        ],
                      ),
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