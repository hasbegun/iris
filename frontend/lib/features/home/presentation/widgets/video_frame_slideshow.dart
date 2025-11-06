import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../api/models/detection.dart';
import '../../../api/providers/analysis_provider.dart';
import 'interactive_detection_overlay.dart';
import 'interactive_segmentation_overlay.dart';

/// Visualization mode for video frames
enum VideoVisualizationMode {
  detection,
  segmentation,
}

/// Widget to display video frame slideshow with detections and segmentation
class VideoFrameSlideshow extends ConsumerStatefulWidget {
  final VideoFramesMetadata videoFramesMetadata;
  final String sessionId;
  final VoidCallback? onRequestSegmentation;

  const VideoFrameSlideshow({
    super.key,
    required this.videoFramesMetadata,
    required this.sessionId,
    this.onRequestSegmentation,
  });

  @override
  ConsumerState<VideoFrameSlideshow> createState() => _VideoFrameSlideshowState();
}

class _VideoFrameSlideshowState extends ConsumerState<VideoFrameSlideshow> {
  int _currentFrameIndex = 0;
  bool _isLoading = false;
  Uint8List? _currentFrameBytes;
  double _minConfidence = 0.0;
  bool _showLabels = true;
  List<int> _framesWithDetections = [];
  VideoVisualizationMode _visualizationMode = VideoVisualizationMode.detection;
  double _opacity = 0.5;
  bool _pendingSegmentationSwitch = false;

  @override
  void initState() {
    super.initState();

    // Build list of frames that have detections
    _framesWithDetections = [];
    for (int i = 0; i < widget.videoFramesMetadata.frames.length; i++) {
      if (widget.videoFramesMetadata.frames[i].detections.isNotEmpty) {
        _framesWithDetections.add(i);
      }
    }

    // Start with first frame that has detections, or frame 0 if none
    final startFrame = _framesWithDetections.isNotEmpty ? _framesWithDetections.first : 0;
    _loadFrameImage(startFrame);

    // Set default confidence threshold
    if (widget.videoFramesMetadata.frames.isNotEmpty) {
      double minConf = 1.0;
      for (var frame in widget.videoFramesMetadata.frames) {
        for (var det in frame.detections) {
          if (det.confidence < minConf) {
            minConf = det.confidence;
          }
        }
      }
      _minConfidence = minConf;
    }
  }

  @override
  void didUpdateWidget(VideoFrameSlideshow oldWidget) {
    super.didUpdateWidget(oldWidget);

    // Check if segments just became available and we're waiting to switch
    if (_pendingSegmentationSwitch) {
      final currentFrame = widget.videoFramesMetadata.frames[_currentFrameIndex];
      if (currentFrame.hasSegments) {
        debugPrint('[VideoFrameSlideshow] Segments loaded, auto-switching to segmentation mode');
        setState(() {
          _visualizationMode = VideoVisualizationMode.segmentation;
          _pendingSegmentationSwitch = false;
        });
      }
    }
  }

  @override
  void dispose() {
    super.dispose();
  }

  Future<void> _loadFrameImage(int frameIndex) async {
    if (frameIndex < 0 || frameIndex >= widget.videoFramesMetadata.framesCount) {
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      // Fetch frame image from backend
      final apiService = ref.read(apiServiceProvider);
      final frameBytes = await apiService.fetchFrameByIndex(
        widget.sessionId,
        frameIndex,
      );

      if (mounted) {
        setState(() {
          _currentFrameBytes = frameBytes;
          _currentFrameIndex = frameIndex;
          _isLoading = false;
        });
      }
    } catch (e) {
      debugPrint('[VideoFrameSlideshow] Error loading frame $frameIndex: $e');
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  void _goToPreviousFrame() {
    // Find previous frame with detections
    final currentIndexInList = _framesWithDetections.indexOf(_currentFrameIndex);
    if (currentIndexInList > 0) {
      final newIndex = _framesWithDetections[currentIndexInList - 1];
      _loadFrameImage(newIndex);
    }
  }

  void _goToNextFrame() {
    // Find next frame with detections
    final currentIndexInList = _framesWithDetections.indexOf(_currentFrameIndex);
    if (currentIndexInList >= 0 && currentIndexInList < _framesWithDetections.length - 1) {
      final newIndex = _framesWithDetections[currentIndexInList + 1];
      _loadFrameImage(newIndex);
    }
  }

  @override
  Widget build(BuildContext context) {
    final currentFrame = widget.videoFramesMetadata.frames[_currentFrameIndex];

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
          // Header with mode toggle and frame info
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.3),
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(12),
                topRight: Radius.circular(12),
              ),
            ),
            child: Column(
              children: [
                // Mode toggle switch
                Center(
                  child: _buildToggleSwitch(context, currentFrame),
                ),
                const SizedBox(height: 8),
                // Frame info
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Frame ${_currentFrameIndex + 1} / ${widget.videoFramesMetadata.framesCount}' +
                          (_framesWithDetections.length < widget.videoFramesMetadata.framesCount
                              ? ' (${_framesWithDetections.length} with detections)'
                              : ''),
                      style: Theme.of(context).textTheme.titleSmall,
                    ),
                    Text(
                      currentFrame.formattedTimestamp,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Theme.of(context).colorScheme.primary,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          // Frame display with detections or segmentation
          AspectRatio(
            aspectRatio: currentFrame.imageMetadata.aspectRatio,
            child: _isLoading || _currentFrameBytes == null
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const CircularProgressIndicator(),
                        const SizedBox(height: 8),
                        Text(
                          'Loading frame...',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  )
                : _visualizationMode == VideoVisualizationMode.detection
                    ? InteractiveDetectionOverlay(
                        imageBytes: _currentFrameBytes!,
                        detections: currentFrame.detections
                            .where((d) => d.confidence >= _minConfidence)
                            .toList(),
                        imageMetadata: currentFrame.imageMetadata,
                        showLabels: _showLabels,
                      )
                    : InteractiveSegmentationOverlay(
                        imageBytes: _currentFrameBytes!,
                        segments: currentFrame.segments!
                            .where((s) => s.confidence >= _minConfidence)
                            .toList(),
                        imageMetadata: currentFrame.imageMetadata,
                        showLabels: _showLabels,
                        opacity: _opacity,
                      ),
          ),

          // Controls
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surfaceVariant.withOpacity(0.3),
              borderRadius: const BorderRadius.only(
                bottomLeft: Radius.circular(12),
                bottomRight: Radius.circular(12),
              ),
            ),
            child: Column(
              children: [
                // Detection summary for this frame
                if (currentFrame.detections.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: _buildDetectionSummaryChips(currentFrame),
                    ),
                  ),

                // Navigation controls
                Row(
                  children: [
                    // Previous button
                    IconButton(
                      onPressed: _framesWithDetections.indexOf(_currentFrameIndex) > 0
                          ? _goToPreviousFrame
                          : null,
                      icon: const Icon(Icons.arrow_back),
                      tooltip: 'Previous frame',
                    ),

                    // Frame indicators - centered and properly spaced
                    Expanded(
                      child: Center(
                        child: SingleChildScrollView(
                          scrollDirection: Axis.horizontal,
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: List.generate(
                              _framesWithDetections.length,
                              (index) {
                                final frameIndex = _framesWithDetections[index];
                                return GestureDetector(
                                  onTap: () {
                                    _loadFrameImage(frameIndex);
                                  },
                                  child: Container(
                                    width: 10,
                                    height: 10,
                                    margin: const EdgeInsets.symmetric(horizontal: 5),
                                    decoration: BoxDecoration(
                                      shape: BoxShape.circle,
                                      color: frameIndex == _currentFrameIndex
                                          ? Theme.of(context).colorScheme.primary
                                          : Theme.of(context).colorScheme.outlineVariant.withOpacity(0.5),
                                      border: Border.all(
                                        color: frameIndex == _currentFrameIndex
                                            ? Theme.of(context).colorScheme.primary
                                            : Theme.of(context).colorScheme.outlineVariant,
                                        width: 1,
                                      ),
                                    ),
                                  ),
                                );
                              },
                            ),
                          ),
                        ),
                      ),
                    ),

                    // Next button
                    IconButton(
                      onPressed: _framesWithDetections.indexOf(_currentFrameIndex) <
                              _framesWithDetections.length - 1
                          ? _goToNextFrame
                          : null,
                      icon: const Icon(Icons.arrow_forward),
                      tooltip: 'Next frame',
                    ),
                  ],
                ),

                // Options
                const SizedBox(height: 8),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    // Show/hide labels toggle
                    IconButton(
                      onPressed: () {
                        setState(() {
                          _showLabels = !_showLabels;
                        });
                      },
                      icon: Icon(_showLabels ? Icons.label : Icons.label_off),
                      tooltip: _showLabels ? 'Hide labels' : 'Show labels',
                    ),

                    const SizedBox(width: 16),

                    // Confidence threshold slider
                    Expanded(
                      child: Row(
                        children: [
                          const Icon(Icons.tune, size: 20),
                          Expanded(
                            child: Slider(
                              value: _minConfidence,
                              min: 0.0,
                              max: 1.0,
                              divisions: 20,
                              label: '${(_minConfidence * 100).round()}%',
                              onChanged: (value) {
                                setState(() {
                                  _minConfidence = value;
                                });
                              },
                            ),
                          ),
                          Text(
                            '${(_minConfidence * 100).round()}%',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ],
                      ),
                    ),
                  ],
                ),

                // Opacity slider for segmentation mode
                if (_visualizationMode == VideoVisualizationMode.segmentation) ...[
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.opacity, size: 20),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Slider(
                          value: _opacity,
                          min: 0.1,
                          max: 1.0,
                          divisions: 9,
                          label: '${(_opacity * 100).round()}%',
                          onChanged: (value) {
                            setState(() {
                              _opacity = value;
                            });
                          },
                        ),
                      ),
                      Text(
                        '${(_opacity * 100).round()}%',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  List<Widget> _buildDetectionSummaryChips(VideoFrame frame) {
    // Group detections by class
    final Map<String, int> classCounts = {};
    for (final detection in frame.detections) {
      if (detection.confidence >= _minConfidence) {
        classCounts[detection.className] = (classCounts[detection.className] ?? 0) + 1;
      }
    }

    return classCounts.entries.map((entry) {
      return Chip(
        avatar: CircleAvatar(
          backgroundColor: Theme.of(context).colorScheme.primary,
          child: Text(
            '${entry.value}',
            style: TextStyle(
              color: Theme.of(context).colorScheme.onPrimary,
              fontSize: 10,
            ),
          ),
        ),
        label: Text(entry.key),
        materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
      );
    }).toList();
  }

  /// Build toggle switch for Detection/Segmentation modes
  Widget _buildToggleSwitch(BuildContext context, VideoFrame currentFrame) {
    final colorScheme = Theme.of(context).colorScheme;
    final isDetectionMode = _visualizationMode == VideoVisualizationMode.detection;
    final hasDetections = currentFrame.detections.isNotEmpty;
    final hasSegments = currentFrame.hasSegments;
    final canRequestSegmentation = widget.onRequestSegmentation != null;

    return Container(
      decoration: BoxDecoration(
        color: colorScheme.surfaceVariant,
        borderRadius: BorderRadius.circular(25),
        border: Border.all(
          color: colorScheme.outline.withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Detection option
          _buildToggleOption(
            context: context,
            label: 'Detection',
            icon: Icons.crop_free,
            isSelected: isDetectionMode,
            isEnabled: hasDetections,
            onTap: hasDetections
                ? () {
                    debugPrint('[VideoFrameSlideshow] Switching to Detection mode');
                    setState(() {
                      _visualizationMode = VideoVisualizationMode.detection;
                    });
                  }
                : null,
          ),
          // Segmentation option
          _buildToggleOption(
            context: context,
            label: 'Segmentation',
            icon: Icons.workspaces_outlined,
            isSelected: !isDetectionMode,
            isEnabled: hasSegments || canRequestSegmentation,
            onTap: (hasSegments || canRequestSegmentation)
                ? () {
                    debugPrint('[VideoFrameSlideshow] Switching to Segmentation mode');

                    // If no segments exist, trigger enrichment
                    if (!hasSegments && canRequestSegmentation) {
                      debugPrint('[VideoFrameSlideshow] Requesting segmentation enrichment');
                      setState(() {
                        _pendingSegmentationSwitch = true;
                      });
                      widget.onRequestSegmentation!();
                      return;
                    }

                    // Otherwise, just switch the mode
                    setState(() {
                      _visualizationMode = VideoVisualizationMode.segmentation;
                    });
                  }
                : null,
          ),
        ],
      ),
    );
  }

  /// Build a single option in the toggle switch
  Widget _buildToggleOption({
    required BuildContext context,
    required String label,
    required IconData icon,
    required bool isSelected,
    required bool isEnabled,
    required VoidCallback? onTap,
  }) {
    final colorScheme = Theme.of(context).colorScheme;

    return Tooltip(
      message: !isEnabled ? 'Tap to load $label data' : label,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(25),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
            decoration: BoxDecoration(
              color: isSelected
                  ? colorScheme.primary
                  : Colors.transparent,
              borderRadius: BorderRadius.circular(25),
              boxShadow: isSelected
                  ? [
                      BoxShadow(
                        color: colorScheme.primary.withOpacity(0.3),
                        blurRadius: 8,
                        offset: const Offset(0, 2),
                      )
                    ]
                  : null,
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  icon,
                  size: 18,
                  color: isEnabled
                      ? (isSelected ? colorScheme.onPrimary : colorScheme.onSurfaceVariant)
                      : colorScheme.onSurfaceVariant.withOpacity(0.3),
                ),
                const SizedBox(width: 6),
                Text(
                  label,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                    color: isEnabled
                        ? (isSelected ? colorScheme.onPrimary : colorScheme.onSurfaceVariant)
                        : colorScheme.onSurfaceVariant.withOpacity(0.3),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
