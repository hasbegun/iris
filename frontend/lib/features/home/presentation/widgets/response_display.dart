import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../../../api/models/vision_response.dart';
import '../../../settings/providers/settings_provider.dart';
import '../../../tts/providers/tts_provider.dart';
import 'highlighted_text_display.dart';
import 'interactive_detection_overlay.dart';
import 'interactive_segmentation_overlay.dart';
import 'detection_control_panel.dart';
import 'segmentation_control_panel.dart';
import 'video_frame_slideshow.dart';

/// Visualization mode type
enum VisualizationMode {
  detection,     // Show bounding boxes
  segmentation,  // Show segmentation masks
}

/// Rendering mode for visualization
enum RenderMode {
  interactive,    // Client-side drawn (default)
  serverRendered, // Pre-annotated image from backend
}

/// Widget to display vision analysis response
class ResponseDisplay extends ConsumerStatefulWidget {
  final VisionResponse response;
  final Uint8List? imageBytes; // Original image for client-side box rendering
  final VoidCallback? onRequestSegmentation; // Callback when user wants segmentation

  const ResponseDisplay({
    super.key,
    required this.response,
    this.imageBytes, // Optional, for interactive detection rendering
    this.onRequestSegmentation, // Optional callback for requesting segmentation
  });

  @override
  ConsumerState<ResponseDisplay> createState() => _ResponseDisplayState();
}

class _ResponseDisplayState extends ConsumerState<ResponseDisplay> {
  VisualizationMode _visualizationMode = VisualizationMode.detection;
  RenderMode _renderMode = RenderMode.interactive;
  double _minConfidence = 0.0;
  Set<String> _filteredClasses = {};
  bool _showLabels = true;
  bool _isPanelCollapsed = false;

  // Segmentation-specific controls
  double _opacity = 0.5;
  bool _fillStyle = true;

  @override
  void initState() {
    super.initState();
    // Set default confidence threshold to minimum detected confidence
    if (widget.response.detections != null && widget.response.detections!.isNotEmpty) {
      _minConfidence = widget.response.detections!
          .map((d) => d.confidence)
          .reduce((a, b) => a < b ? a : b);
    }
  }

  void _copyToClipboard(BuildContext context, String text) {
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Copied to clipboard'),
        duration: Duration(seconds: 2),
      ),
    );
  }

  /// Check if we can render interactive detections
  bool get _canRenderInteractive {
    final canRender = widget.imageBytes != null &&
        widget.response.hasDetections &&
        widget.response.detections != null &&
        widget.response.imageMetadata != null &&
        widget.response.detections!.isNotEmpty;

    debugPrint('[ResponseDisplay] _canRenderInteractive check:');
    debugPrint('  - imageBytes != null: ${widget.imageBytes != null}');
    debugPrint('  - imageBytes length: ${widget.imageBytes?.length ?? 0}');
    debugPrint('  - hasDetections: ${widget.response.hasDetections}');
    debugPrint('  - detections != null: ${widget.response.detections != null}');
    debugPrint('  - detections count: ${widget.response.detections?.length ?? 0}');
    debugPrint('  - imageMetadata != null: ${widget.response.imageMetadata != null}');
    debugPrint('  - imageMetadata: ${widget.response.imageMetadata}');
    debugPrint('  - Can render: $canRender');

    return canRender;
  }

  /// Check if we can render interactive segmentation
  bool get _canRenderSegmentation {
    final canRender = widget.imageBytes != null &&
        widget.response.hasSegments &&
        widget.response.segments != null &&
        widget.response.imageMetadata != null &&
        widget.response.segments!.isNotEmpty;

    debugPrint('[ResponseDisplay] _canRenderSegmentation check:');
    debugPrint('  - imageBytes != null: ${widget.imageBytes != null}');
    debugPrint('  - hasSegments: ${widget.response.hasSegments}');
    debugPrint('  - segments != null: ${widget.response.segments != null}');
    debugPrint('  - segments count: ${widget.response.segments?.length ?? 0}');
    debugPrint('  - imageMetadata != null: ${widget.response.imageMetadata != null}');
    debugPrint('  - Can render: $canRender');

    return canRender;
  }

  /// Build visualization (detection or segmentation, interactive or server-rendered)
  Widget? _buildVisualization(BuildContext context, String backendUrl) {
    // Check if we have any visualization data
    final hasDetection = _canRenderInteractive || widget.response.hasAnnotatedImage;
    final hasSegmentation = _canRenderSegmentation;

    if (!hasDetection && !hasSegmentation) {
      return null;
    }

    // Determine which mode to use
    // If user selected a mode that's available, use it
    // Otherwise, fall back to whatever is available
    VisualizationMode effectiveMode = _visualizationMode;
    if (_visualizationMode == VisualizationMode.detection && !hasDetection && hasSegmentation) {
      effectiveMode = VisualizationMode.segmentation;
    } else if (_visualizationMode == VisualizationMode.segmentation && !hasSegmentation && hasDetection) {
      effectiveMode = VisualizationMode.detection;
    }

    return Container(
      margin: const EdgeInsets.only(top: 8),
      decoration: BoxDecoration(
        border: Border.all(
          color: Theme.of(context).colorScheme.outlineVariant,
          width: 1,
        ),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Header with mode toggle
          _buildVisualizationHeader(context),

          // Main visualization based on selected mode
          if (effectiveMode == VisualizationMode.detection) ...[
            // Detection mode
            if (_renderMode == RenderMode.interactive && _canRenderInteractive)
              _buildInteractiveVisualization(context)
            else
              _buildServerRenderedImage(context, backendUrl),

            // Detection control panel (only for interactive mode)
            if (_renderMode == RenderMode.interactive && _canRenderInteractive)
              DetectionControlPanel(
                detections: widget.response.detections!,
                minConfidence: _minConfidence,
                filteredClasses: _filteredClasses,
                showLabels: _showLabels,
                onConfidenceChanged: (value) {
                  setState(() {
                    _minConfidence = value;
                  });
                },
                onFilteredClassesChanged: (classes) {
                  setState(() {
                    _filteredClasses = classes;
                  });
                },
                onShowLabelsChanged: (value) {
                  setState(() {
                    _showLabels = value;
                  });
                },
                isCollapsed: _isPanelCollapsed,
                onToggleCollapse: () {
                  setState(() {
                    _isPanelCollapsed = !_isPanelCollapsed;
                  });
                },
              ),
          ] else ...[
            // Segmentation mode
            if (_renderMode == RenderMode.interactive && _canRenderSegmentation)
              _buildInteractiveSegmentationVisualization(context)
            else
              _buildServerRenderedImage(context, backendUrl),

            // Segmentation control panel (only for interactive mode)
            if (_renderMode == RenderMode.interactive && _canRenderSegmentation)
              SegmentationControlPanel(
                segments: widget.response.segments!,
                minConfidence: _minConfidence,
                filteredClasses: _filteredClasses,
                showLabels: _showLabels,
                opacity: _opacity,
                fillStyle: _fillStyle,
                onConfidenceChanged: (value) {
                  setState(() {
                    _minConfidence = value;
                  });
                },
                onFilteredClassesChanged: (classes) {
                  setState(() {
                    _filteredClasses = classes;
                  });
                },
                onShowLabelsChanged: (value) {
                  setState(() {
                    _showLabels = value;
                  });
                },
                onOpacityChanged: (value) {
                  setState(() {
                    _opacity = value;
                  });
                },
                onFillStyleChanged: (value) {
                  setState(() {
                    _fillStyle = value;
                  });
                },
                isCollapsed: _isPanelCollapsed,
                onToggleCollapse: () {
                  setState(() {
                    _isPanelCollapsed = !_isPanelCollapsed;
                  });
                },
              ),
          ],
        ],
      ),
    );
  }

  /// Build visualization header with mode toggle
  Widget _buildVisualizationHeader(BuildContext context) {
    // Check what modes are available
    final hasDetection = _canRenderInteractive || widget.response.hasAnnotatedImage;
    final hasSegmentation = _canRenderSegmentation;

    return Container(
      padding: const EdgeInsets.all(6),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: const BorderRadius.vertical(
          top: Radius.circular(11),
        ),
      ),
      child: Row(
        children: [
          Icon(
            Icons.image,
            size: 14,
            color: Theme.of(context).colorScheme.primary,
          ),
          const SizedBox(width: 6),
          Text(
            'Visual Analysis',
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.w600,
                  fontSize: 12,
                ),
          ),
          const SizedBox(width: 8),

          // Wrap buttons in Flexible to prevent overflow
          Flexible(
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Visualization mode toggle (Detection vs Segmentation)
                // Always show if we have any visualization data
                if (hasDetection || hasSegmentation) ...[
                  Flexible(
                    child: SegmentedButton<VisualizationMode>(
              segments: [
                ButtonSegment(
                  value: VisualizationMode.detection,
                  icon: const Icon(Icons.crop_square, size: 16),
                  enabled: hasDetection,
                ),
                ButtonSegment(
                  value: VisualizationMode.segmentation,
                  icon: Icon(
                    Icons.colorize,
                    size: 16,
                    color: hasSegmentation ? null : Theme.of(context).colorScheme.onSurfaceVariant.withOpacity(0.6),
                  ),
                  // Keep enabled so it can be clicked
                  enabled: true,
                ),
              ],
              selected: {_visualizationMode},
              onSelectionChanged: (Set<VisualizationMode> newSelection) {
                final newMode = newSelection.first;

                // If switching to segmentation mode but no segmentation data available
                if (newMode == VisualizationMode.segmentation && !hasSegmentation) {
                  debugPrint('[ResponseDisplay] Segmentation requested but not available - triggering callback');
                  // Trigger callback to request segmentation
                  widget.onRequestSegmentation?.call();
                  return; // Don't change mode yet
                }

                // Normal mode switch
                setState(() {
                  _visualizationMode = newMode;
                });
              },
              style: ButtonStyle(
                visualDensity: VisualDensity.compact,
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  /// Build interactive visualization with detection boxes
  Widget _buildInteractiveVisualization(BuildContext context) {
    // Determine max height based on orientation
    final orientation = MediaQuery.of(context).orientation;
    final maxHeight = orientation == Orientation.portrait ? 300.0 : 400.0;

    return Container(
      constraints: BoxConstraints(
        maxHeight: maxHeight,
      ),
      padding: const EdgeInsets.symmetric(vertical: 1), // Reduced padding
      child: InteractiveDetectionOverlay(
        imageBytes: widget.imageBytes!,
        detections: widget.response.detections!,
        imageMetadata: widget.response.imageMetadata!,
        minConfidence: _minConfidence,
        filteredClasses: _filteredClasses,
        showLabels: _showLabels,
      ),
    );
  }

  /// Build interactive segmentation visualization
  Widget _buildInteractiveSegmentationVisualization(BuildContext context) {
    // Determine max height based on orientation
    final orientation = MediaQuery.of(context).orientation;
    final maxHeight = orientation == Orientation.portrait ? 300.0 : 400.0;

    return Container(
      constraints: BoxConstraints(
        maxHeight: maxHeight,
      ),
      padding: const EdgeInsets.symmetric(vertical: 1),
      child: InteractiveSegmentationOverlay(
        imageBytes: widget.imageBytes!,
        segments: widget.response.segments!,
        imageMetadata: widget.response.imageMetadata!,
        minConfidence: _minConfidence,
        filteredClasses: _filteredClasses,
        showLabels: _showLabels,
        opacity: _opacity,
        fillStyle: _fillStyle,
      ),
    );
  }

  /// Build server-rendered annotated image
  Widget _buildServerRenderedImage(BuildContext context, String backendUrl) {
    // Safety check
    if (!widget.response.hasAnnotatedImage || widget.response.annotatedImageUrl == null) {
      return Container(
        height: 200,
        padding: const EdgeInsets.all(16),
        alignment: Alignment.center,
        child: Text(
          'No visualization available',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
        ),
      );
    }

    // Construct full URL
    final imageUrl = '$backendUrl${widget.response.annotatedImageUrl}';

    return ClipRRect(
      borderRadius: const BorderRadius.vertical(
        bottom: Radius.circular(11),
      ),
      child: CachedNetworkImage(
        imageUrl: imageUrl,
        placeholder: (context, url) => Container(
          height: 200,
          alignment: Alignment.center,
          child: const CircularProgressIndicator(),
        ),
        errorWidget: (context, url, error) => Container(
          height: 200,
          padding: const EdgeInsets.all(16),
          alignment: Alignment.center,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.error_outline,
                color: Theme.of(context).colorScheme.error,
                size: 40,
              ),
              const SizedBox(height: 8),
              Text(
                'Failed to load annotated image',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Theme.of(context).colorScheme.error,
                    ),
              ),
            ],
          ),
        ),
        fit: BoxFit.contain,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isPlaying = ref.watch(ttsIsPlayingProvider);
    final isPaused = ref.watch(ttsIsPausedProvider);
    final currentText = ref.watch(ttsCurrentTextProvider);
    final devMode = ref.watch(devModeProvider);
    final backendUrl = ref.watch(settingsProvider).backendUrl;

    // Check if this response is currently being read
    final isThisResponsePlaying = isPlaying && currentText == widget.response.response;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header with title and action buttons
            Row(
              children: [
                Icon(
                  Icons.smart_toy,
                  color: Theme.of(context).colorScheme.primary,
                  size: 20,
                ),
                const SizedBox(width: 8),
                Text(
                  'Response',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const Spacer(),
                // Read aloud button
                IconButton(
                  icon: Icon(
                    isThisResponsePlaying
                        ? (isPaused ? Icons.play_arrow : Icons.stop)
                        : Icons.volume_up,
                    size: 18,
                  ),
                  onPressed: () {
                    if (isThisResponsePlaying) {
                      if (isPaused) {
                        // Resume
                        ref.read(ttsProvider.notifier).speak(widget.response.response);
                      } else {
                        // Stop
                        ref.read(ttsProvider.notifier).stop();
                      }
                    } else {
                      // Start reading
                      ref.read(ttsProvider.notifier).speak(widget.response.response);
                    }
                  },
                  tooltip: isThisResponsePlaying
                      ? (isPaused ? 'Resume' : 'Stop reading')
                      : 'Read aloud',
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                ),
                const SizedBox(width: 8),
                // Copy button
                IconButton(
                  icon: const Icon(Icons.copy, size: 18),
                  onPressed: () => _copyToClipboard(context, widget.response.response),
                  tooltip: 'Copy to clipboard',
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(),
                ),
              ],
            ),

            const SizedBox(height: 12),

            // Response text (scrollable with TTS highlighting)
            Container(
              constraints: const BoxConstraints(
                maxHeight: 300, // Max height before scrolling
              ),
              child: SingleChildScrollView(
                child: HighlightedTextDisplay(
                  text: widget.response.response,
                  style: Theme.of(context).textTheme.bodyLarge,
                  enableHighlight: isThisResponsePlaying,
                ),
              ),
            ),

            // Video frames slideshow (if available)
            if (widget.response.hasVideoFrames && widget.response.videoFrames != null)
              VideoFrameSlideshow(
                videoFramesMetadata: widget.response.videoFrames!,
                sessionId: widget.response.sessionId,
                onRequestSegmentation: widget.onRequestSegmentation,
              )
            // Visualization (detection or segmentation, interactive or server-rendered)
            else if (_buildVisualization(context, backendUrl) != null)
              _buildVisualization(context, backendUrl)!,

            // Metadata (only shown in dev mode)
            if (devMode) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.surfaceContainerHighest,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _MetadataRow(
                      icon: Icons.memory,
                      label: 'Model',
                      value: widget.response.modelUsed,
                    ),
                    const SizedBox(height: 8),
                    _MetadataRow(
                      icon: Icons.timer,
                      label: 'Processing Time',
                      value: '${widget.response.processingTime.toStringAsFixed(2)}s',
                    ),
                    const SizedBox(height: 8),
                    _MetadataRow(
                      icon: Icons.tag,
                      label: 'Session ID',
                      value: widget.response.sessionId.substring(0, 8),
                    ),
                    if (widget.response.hasDetections) ...[
                      const SizedBox(height: 8),
                      _MetadataRow(
                        icon: Icons.grid_on,
                        label: 'Detections',
                        value: '${widget.response.totalDetections} objects',
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// Metadata row widget
class _MetadataRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _MetadataRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(
          icon,
          size: 16,
          color: Theme.of(context).colorScheme.onSurfaceVariant,
        ),
        const SizedBox(width: 8),
        Text(
          '$label: ',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
                fontWeight: FontWeight.w500,
              ),
        ),
        Expanded(
          child: Text(
            value,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    );
  }
}