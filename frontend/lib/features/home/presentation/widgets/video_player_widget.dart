import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';
import '../../models/media_item.dart';

/// Widget to display and play a selected video
class VideoPlayerWidget extends StatefulWidget {
  final MediaItem mediaItem;
  final VoidCallback? onRemove;

  const VideoPlayerWidget({
    super.key,
    required this.mediaItem,
    this.onRemove,
  });

  @override
  State<VideoPlayerWidget> createState() => _VideoPlayerWidgetState();
}

class _VideoPlayerWidgetState extends State<VideoPlayerWidget> {
  late VideoPlayerController _controller;
  bool _isInitialized = false;
  bool _hasError = false;
  String? _errorMessage;
  bool _showControls = true;

  @override
  void initState() {
    super.initState();
    _initializeVideo();
  }

  Future<void> _initializeVideo() async {
    try {
      _controller = VideoPlayerController.file(widget.mediaItem.file);
      await _controller.initialize();

      // Listen to video position changes to update UI
      _controller.addListener(() {
        if (mounted) {
          setState(() {});
        }
      });

      if (mounted) {
        setState(() {
          _isInitialized = true;
        });
      }
    } catch (e) {
      debugPrint('Error initializing video: $e');
      if (mounted) {
        setState(() {
          _hasError = true;
          _errorMessage = e.toString();
        });
      }
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  String _formatDuration(Duration duration) {
    String twoDigits(int n) => n.toString().padLeft(2, '0');
    final minutes = twoDigits(duration.inMinutes.remainder(60));
    final seconds = twoDigits(duration.inSeconds.remainder(60));
    return '$minutes:$seconds';
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      clipBehavior: Clip.antiAlias,
      child: Stack(
        children: [
          // Video or loading/error state
          if (_hasError)
            _buildErrorWidget()
          else if (!_isInitialized)
            _buildLoadingWidget()
          else
            _buildVideoPlayer(),

          // Remove button (top-right)
          if (widget.onRemove != null)
            Positioned(
              top: 8,
              right: 8,
              child: Material(
                color: Colors.black.withOpacity(0.5),
                shape: const CircleBorder(),
                child: InkWell(
                  onTap: widget.onRemove,
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

          // Play/Pause button (center)
          if (_isInitialized && !_controller.value.isPlaying)
            Center(
              child: Material(
                color: Colors.black.withOpacity(0.5),
                shape: const CircleBorder(),
                child: InkWell(
                  onTap: () {
                    setState(() {
                      _controller.play();
                    });
                  },
                  customBorder: const CircleBorder(),
                  child: const Padding(
                    padding: EdgeInsets.all(16),
                    child: Icon(
                      Icons.play_arrow,
                      color: Colors.white,
                      size: 48,
                    ),
                  ),
                ),
              ),
            ),

          // Video controls (bottom)
          if (_isInitialized)
            Positioned(
              left: 0,
              right: 0,
              bottom: 0,
              child: _buildVideoControls(),
            ),
        ],
      ),
    );
  }

  Widget _buildVideoControls() {
    final position = _controller.value.position;
    final duration = _controller.value.duration;
    final isPlaying = _controller.value.isPlaying;

    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            Colors.transparent,
            Colors.black.withOpacity(0.7),
          ],
        ),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Progress slider
          SliderTheme(
            data: SliderThemeData(
              trackHeight: 2,
              thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 6),
              overlayShape: const RoundSliderOverlayShape(overlayRadius: 12),
              activeTrackColor: Theme.of(context).colorScheme.primary,
              inactiveTrackColor: Colors.white.withOpacity(0.3),
              thumbColor: Theme.of(context).colorScheme.primary,
              overlayColor: Theme.of(context).colorScheme.primary.withOpacity(0.3),
            ),
            child: Slider(
              value: position.inMilliseconds.toDouble().clamp(0, duration.inMilliseconds.toDouble()),
              min: 0,
              max: duration.inMilliseconds.toDouble(),
              onChanged: (value) {
                _controller.seekTo(Duration(milliseconds: value.toInt()));
              },
            ),
          ),
          // Time display and play/pause button
          Row(
            children: [
              // Play/Pause button
              IconButton(
                onPressed: () {
                  setState(() {
                    if (isPlaying) {
                      _controller.pause();
                    } else {
                      _controller.play();
                    }
                  });
                },
                icon: Icon(
                  isPlaying ? Icons.pause : Icons.play_arrow,
                  color: Colors.white,
                  size: 24,
                ),
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(),
              ),
              const SizedBox(width: 8),
              // Time display
              Text(
                '${_formatDuration(position)} / ${_formatDuration(duration)}',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                ),
              ),
              const Spacer(),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildLoadingWidget() {
    return Container(
      color: Colors.black,
      child: const Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text(
              'Loading video...',
              style: TextStyle(color: Colors.white),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorWidget() {
    return Container(
      color: Colors.black,
      padding: const EdgeInsets.all(16),
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error, color: Colors.red, size: 48),
            const SizedBox(height: 16),
            const Text(
              'Failed to load video',
              style: TextStyle(color: Colors.white, fontSize: 16),
            ),
            if (_errorMessage != null) ...[
              const SizedBox(height: 8),
              Text(
                _errorMessage!,
                style: TextStyle(
                  color: Colors.white.withOpacity(0.7),
                  fontSize: 12,
                ),
                textAlign: TextAlign.center,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildVideoPlayer() {
    return Center(
      child: AspectRatio(
        aspectRatio: _controller.value.aspectRatio,
        child: VideoPlayer(_controller),
      ),
    );
  }
}
