import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:iris/l10n/app_localizations.dart';
import '../../../core/providers/permission_provider.dart';
import '../../api/providers/analysis_provider.dart';
import '../../prompt/providers/prompt_provider.dart';
import '../../prompt/presentation/widgets/prompt_input_widget.dart';
import '../providers/media_provider.dart';
import 'widgets/media_preview.dart';
import 'widgets/response_display.dart';

/// Home screen - main interface for vision analysis
class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final mediaError = ref.watch(mediaErrorProvider);
    final isMediaLoading = ref.watch(mediaLoadingProvider);

    final selectedMedia = ref.watch(selectedMediaProvider);
    final promptText = ref.watch(promptTextProvider);
    final analysisError = ref.watch(analysisErrorProvider);
    final analysisLoading = ref.watch(analysisLoadingProvider);
    final conversationHistory = ref.watch(conversationHistoryProvider);

    final isLoading = isMediaLoading || analysisLoading;

    // Show media error snackbar if present
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

    // Show analysis error snackbar if present
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
          SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Media Preview
                const MediaPreview(),

                // Media Selection Buttons
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text(
                        'Select Media',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: ElevatedButton.icon(
                              onPressed: isLoading
                                  ? null
                                  : () {
                                      // image_picker handles permissions automatically
                                      ref
                                          .read(mediaProvider.notifier)
                                          .pickImageFromGallery();
                                    },
                              icon: const Icon(Icons.photo_library),
                              label: Text(l10n.selectImage),
                              style: ElevatedButton.styleFrom(
                                padding: const EdgeInsets.symmetric(vertical: 16),
                              ),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: ElevatedButton.icon(
                              onPressed: isLoading
                                  ? null
                                  : () {
                                      // image_picker handles permissions automatically
                                      ref
                                          .read(mediaProvider.notifier)
                                          .pickVideoFromGallery();
                                    },
                              icon: const Icon(Icons.video_library),
                              label: Text(l10n.selectVideo),
                              style: ElevatedButton.styleFrom(
                                padding: const EdgeInsets.symmetric(vertical: 16),
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      OutlinedButton.icon(
                        onPressed: isLoading
                            ? null
                            : () {
                                // image_picker handles camera permissions automatically
                                ref
                                    .read(mediaProvider.notifier)
                                    .pickImageFromCamera();
                              },
                        icon: const Icon(Icons.camera_alt),
                        label: const Text('Take Photo'),
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 16),
                        ),
                      ),
                    ],
                  ),
                ),

                // Prompt Input
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: PromptInputWidget(
                    onSubmit: () async {
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

                      // Check if prompt has text
                      if (promptText.trim().isEmpty) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('Please enter a question'),
                            backgroundColor: Colors.orange,
                          ),
                        );
                        return;
                      }

                      // Submit to backend
                      await ref.read(analysisProvider.notifier).analyzeMedia(
                            mediaItem: selectedMedia,
                            prompt: promptText,
                          );
                    },
                  ),
                ),

                // Conversation History
                if (conversationHistory.isNotEmpty)
                  ...conversationHistory.asMap().entries.map((entry) {
                    final index = entry.key;
                    final message = entry.value;
                    return Padding(
                      padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
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
              ],
            ),
          ),

          // Loading overlay
          if (isLoading)
            Container(
              color: Colors.black.withValues(alpha: 0.3),
              child: Center(
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const CircularProgressIndicator(),
                        const SizedBox(height: 16),
                        Text(
                          analysisLoading
                              ? l10n.processing
                              : 'Loading media...',
                        ),
                      ],
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
