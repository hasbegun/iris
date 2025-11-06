import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:camera/camera.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:image/image.dart' as img;
import 'package:iris/l10n/app_localizations.dart';
import '../../../speech/services/speech_service.dart';
import '../../providers/live_camera_provider.dart';
import 'live_detection_overlay.dart';
import 'live_segmentation_overlay.dart';

// ============================================================================
// ISOLATE-COMPATIBLE TOP-LEVEL FUNCTIONS
// These functions must be top-level to be used with compute() for Isolates
// ============================================================================

/// Data class for YUV conversion parameters
class YuvConversionParams {
  final Uint8List yPlane;
  final Uint8List uvPlane;
  final int width;
  final int height;
  final int yRowStride;
  final int uvRowStride;
  final int uvPixelStride;
  final int sensorOrientation;
  final TargetPlatform platform;

  YuvConversionParams({
    required this.yPlane,
    required this.uvPlane,
    required this.width,
    required this.height,
    required this.yRowStride,
    required this.uvRowStride,
    required this.uvPixelStride,
    required this.sensorOrientation,
    required this.platform,
  });
}

/// Top-level function for YUV to RGB conversion (runs in Isolate)
img.Image convertYUV420InIsolate(YuvConversionParams params) {
  final image = img.Image(width: params.width, height: params.height);

  // Convert YUV420 to RGB using ITU-R BT.601 standard
  for (int row = 0; row < params.height; row++) {
    for (int col = 0; col < params.width; col++) {
      final int yIndex = row * params.yRowStride + col;
      if (yIndex >= params.yPlane.length) continue;
      final int y = params.yPlane[yIndex];

      final int uvRow = row ~/ 2;
      final int uvCol = col ~/ 2;
      final int uvIndex = uvRow * params.uvRowStride + uvCol * params.uvPixelStride;

      int u = 128, v = 128;

      if (uvIndex < params.uvPlane.length - 1) {
        v = params.uvPlane[uvIndex];
        u = params.uvPlane[uvIndex + 1];
      }

      // ITU-R BT.601 standard conversion using integer math
      final int c = y - 16;
      final int d = u - 128;
      final int e = v - 128;

      final int r = ((298 * c + 409 * e + 128) >> 8).clamp(0, 255);
      final int g = ((298 * c - 100 * d - 208 * e + 128) >> 8).clamp(0, 255);
      final int b = ((298 * c + 516 * d + 128) >> 8).clamp(0, 255);

      image.setPixelRgba(col, row, r, g, b, 255);
    }
  }

  // Apply rotation based on camera sensor orientation
  if (params.platform == TargetPlatform.android) {
    if (params.sensorOrientation == 90) {
      return img.copyRotate(image, angle: 90);
    } else if (params.sensorOrientation == 270) {
      return img.copyRotate(image, angle: 270);
    } else if (params.sensorOrientation == 180) {
      return img.copyRotate(image, angle: 180);
    }
  }

  return image;
}

/// Top-level function for JPEG encoding (runs in Isolate)
Uint8List encodeJpegInIsolate(img.Image image) {
  // Reduced quality from 90 to 65 for faster encoding and smaller payload
  return Uint8List.fromList(img.encodeJpg(image, quality: 65));
}

/// Widget for live camera with real-time object detection and voice commands
class LiveCameraWidget extends ConsumerStatefulWidget {
  const LiveCameraWidget({super.key});

  @override
  ConsumerState<LiveCameraWidget> createState() => _LiveCameraWidgetState();
}

class _LiveCameraWidgetState extends ConsumerState<LiveCameraWidget> with WidgetsBindingObserver {
  CameraController? _cameraController;
  final SpeechService _speechService = SpeechService();
  bool _isInitialized = false;
  bool _isDetecting = false;
  bool _isListening = false;
  String? _errorMessage;
  String _currentCommand = '';
  String _partialCommand = '';
  bool _isProcessingFrame = false;
  DateTime? _lastFrameTime;
  int _adaptiveFrameInterval = 200; // Start at 200ms (~5 FPS)
  static const int _minFrameInterval = 100; // Max 10 FPS
  static const int _maxFrameInterval = 500; // Min 2 FPS
  static const int _targetProcessingTime = 150; // Target total time per frame

  // Frame queue for Phase 3 optimization
  CameraImage? _queuedFrame;
  DateTime? _queuedFrameTime;
  int _droppedFramesCount = 0;
  static const int _maxQueueAge = 100; // Drop queued frames older than 100ms

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initializeCamera();
    // Don't request permissions on init - only when user clicks microphone
    _setupSpeechServiceCallbacks();
  }

  @override
  void dispose() {
    debugPrint('[LiveCamera] Disposing widget...');
    WidgetsBinding.instance.removeObserver(this);

    // Stop image stream without calling setState
    try {
      if (_cameraController != null && _cameraController!.value.isStreamingImages) {
        _cameraController!.stopImageStream();
        debugPrint('[LiveCamera] Stopped image stream');
      }
    } catch (e) {
      debugPrint('[LiveCamera] Error stopping image stream: $e');
    }

    // Update state variables directly without setState (widget is disposing)
    _isDetecting = false;
    _currentCommand = '';
    _isProcessingFrame = false;
    _lastFrameTime = null;
    _adaptiveFrameInterval = 200;
    _queuedFrame = null;
    _queuedFrameTime = null;
    _droppedFramesCount = 0;

    // Update provider state
    try {
      ref.read(liveCameraProvider.notifier).stopDetection();
    } catch (e) {
      debugPrint('[LiveCamera] Error updating provider during dispose: $e');
    }

    // Dispose camera controller
    _cameraController?.dispose().then((_) {
      debugPrint('[LiveCamera] Camera controller disposed');
    }).catchError((e) {
      debugPrint('[LiveCamera] Error disposing camera controller: $e');
    });
    _cameraController = null;

    // Dispose speech service
    _speechService.dispose();

    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    super.didChangeAppLifecycleState(state);

    // Re-check permissions when app comes back from background
    if (state == AppLifecycleState.resumed) {
      debugPrint('[LiveCamera] App resumed, re-checking permissions...');
      if (_errorMessage != null) {
        // Only retry if there was a permission error
        _initializeCamera();
      }
    }
  }

  /// Setup speech service callbacks (without requesting permissions)
  void _setupSpeechServiceCallbacks() {
    debugPrint('[LiveCamera] Setting up speech service callbacks...');

    // Set up callbacks
    _speechService.onCommandRecognized = (command) {
      debugPrint('[LiveCamera] Command recognized: $command');
      _handleVoiceCommand(command);
    };

    _speechService.onPartialResult = (text) {
      setState(() {
        _partialCommand = text;
      });
    };

    _speechService.onError = (error) {
      if (mounted) {
        final l10n = AppLocalizations.of(context)!;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.speechError(error))),
        );
      }
    };

    _speechService.onListeningStart = () {
      if (mounted) {
        setState(() {
          _isListening = true;
        });
      }
    };

    _speechService.onListeningStop = () {
      if (mounted) {
        setState(() {
          _isListening = false;
          _partialCommand = '';
        });
      }
    };

    debugPrint('[LiveCamera] Speech service callbacks configured');
  }

  /// Handle recognized voice command
  void _handleVoiceCommand(VoiceCommandResult command) {
    final l10n = AppLocalizations.of(context)!;

    switch (command.command) {
      case VoiceCommand.find:
        if (command.target != null) {
          _startDetection(command.target!);
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(l10n.findingObject(command.target!))),
          );
        }
        break;

      case VoiceCommand.stop:
        _stopDetection();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.detectionStopped)),
        );
        break;

      case VoiceCommand.pause:
        // TODO: Implement pause functionality
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.pauseNotImplemented)),
        );
        break;

      case VoiceCommand.resume:
        // TODO: Implement resume functionality
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.resumeNotImplemented)),
        );
        break;

      case VoiceCommand.unknown:
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.unknownCommand(command.rawText))),
        );
        break;
    }
  }

  /// Initialize camera
  Future<void> _initializeCamera() async {
    try {
      debugPrint('[LiveCamera] Starting camera initialization...');

      // Get available cameras first (this will trigger permission request if needed)
      final cameras = await availableCameras();
      debugPrint('[LiveCamera] Found ${cameras.length} cameras');

      if (cameras.isEmpty) {
        final l10n = AppLocalizations.of(context)!;
        setState(() {
          _errorMessage = l10n.noCamerasAvailable;
        });
        return;
      }

      // Use back camera by default
      final camera = cameras.firstWhere(
        (camera) => camera.lensDirection == CameraLensDirection.back,
        orElse: () => cameras.first,
      );
      debugPrint('[LiveCamera] Using camera: ${camera.name} (${camera.lensDirection})');

      // Initialize camera controller
      // Use medium resolution for better Android compatibility
      // Use YUV420 format for image streaming (JPEG causes issues on Android)
      _cameraController = CameraController(
        camera,
        ResolutionPreset.medium,  // Changed from high to medium for better compatibility
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.yuv420,  // Changed from jpeg to yuv420 for streaming
      );

      debugPrint('[LiveCamera] Initializing camera controller...');
      await _cameraController!.initialize();
      debugPrint('[LiveCamera] Camera controller initialized successfully');

      if (mounted) {
        setState(() {
          _isInitialized = true;
          _errorMessage = null; // Clear any previous errors
        });
      }
    } on CameraException catch (e) {
      debugPrint('[LiveCamera] CameraException: ${e.code} - ${e.description}');

      if (mounted) {
        final l10n = AppLocalizations.of(context)!;
        // Handle specific camera errors
        if (e.code == 'CameraAccessDenied' || e.description?.contains('permission') == true) {
          setState(() {
            _errorMessage = l10n.cameraPermissionDenied;
          });
        } else {
          setState(() {
            _errorMessage = l10n.cameraError(e.description ?? e.code);
          });
        }
      }
    } catch (e) {
      debugPrint('[LiveCamera] Error initializing camera: $e');

      if (mounted) {
        final l10n = AppLocalizations.of(context)!;
        final errorStr = e.toString().toLowerCase();
        // Check if it's a permission-related error
        if (errorStr.contains('permission') || errorStr.contains('denied') || errorStr.contains('authorized')) {
          setState(() {
            _errorMessage = l10n.cameraPermissionDenied;
          });
        } else {
          setState(() {
            _errorMessage = l10n.cameraInitializationFailed(e.toString());
          });
        }
      }
    }
  }

  /// Start detection
  void _startDetection(String command) {
    if (!_isInitialized || _cameraController == null) {
      return;
    }

    setState(() {
      _isDetecting = true;
      _currentCommand = command;
    });

    // Update provider state
    ref.read(liveCameraProvider.notifier).startDetection(command);

    // Start camera image stream for real-time detection
    try {
      // Ensure no existing stream is running
      if (_cameraController!.value.isStreamingImages) {
        debugPrint('[LiveCamera] Stopping existing stream before starting new one');
        _cameraController!.stopImageStream();
      }

      _cameraController!.startImageStream((CameraImage image) {
        _processImageStream(image);
      });
      debugPrint('[LiveCamera] Started image stream for detection: $command');
    } catch (e, stackTrace) {
      debugPrint('[LiveCamera] ❌ Error starting image stream: $e');
      debugPrint('[LiveCamera] Stack trace: $stackTrace');

      if (mounted) {
        final l10n = AppLocalizations.of(context)!;
        setState(() {
          _isDetecting = false;
          _currentCommand = '';
        });

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(l10n.cameraStreamFailed(e.toString())),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 5),
          ),
        );
      }
    }
  }

  /// Stop detection
  void _stopDetection() {
    try {
      if (_cameraController != null && _cameraController!.value.isStreamingImages) {
        _cameraController!.stopImageStream();
        debugPrint('[LiveCamera] Stopped image stream');
      }
    } catch (e) {
      debugPrint('[LiveCamera] Error stopping image stream: $e');
    }

    // Only call setState if widget is still mounted
    if (mounted) {
      setState(() {
        _isDetecting = false;
        _currentCommand = '';
        _isProcessingFrame = false;
        _lastFrameTime = null;  // Reset frame throttling
        _adaptiveFrameInterval = 200;  // Reset to default
        _queuedFrame = null;  // Clear queued frame
        _queuedFrameTime = null;
        _droppedFramesCount = 0;  // Reset dropped frames counter
      });
    } else {
      // If not mounted, update state variables directly without setState
      _isDetecting = false;
      _currentCommand = '';
      _isProcessingFrame = false;
      _lastFrameTime = null;
      _adaptiveFrameInterval = 200;
      _queuedFrame = null;
      _queuedFrameTime = null;
      _droppedFramesCount = 0;
    }

    // Update provider state
    ref.read(liveCameraProvider.notifier).stopDetection();

    debugPrint('[LiveCamera] Stopped detection');
  }

  /// Process frames from camera image stream with adaptive frame rate and smart queue
  void _processImageStream(CameraImage image) {
    final now = DateTime.now();

    // If already processing, queue this frame (Phase 3 optimization)
    if (_isProcessingFrame) {
      // Drop old queued frame if exists and queue new one
      if (_queuedFrame != null) {
        _droppedFramesCount++;
        debugPrint('[LiveCamera] Dropped queued frame (total dropped: $_droppedFramesCount)');
      }
      _queuedFrame = image;
      _queuedFrameTime = now;
      debugPrint('[LiveCamera] Queued frame for processing');
      return;
    }

    // Use adaptive frame interval (dynamically adjusted based on processing time)
    if (_lastFrameTime != null && now.difference(_lastFrameTime!).inMilliseconds < _adaptiveFrameInterval) {
      return;
    }

    _lastFrameTime = now;
    _processFrame(image);
  }

  /// Process a single frame (extracted for reuse with queued frames)
  void _processFrame(CameraImage image) {
    _isProcessingFrame = true;

    debugPrint('[LiveCamera] Processing frame (adaptive interval: ${_adaptiveFrameInterval}ms): ${image.width}x${image.height}, format: ${image.format.group}');

    // Process frame in background
    final frameStartTime = DateTime.now();
    _convertAndDetect(image).then((_) {
      if (mounted) {
        // Calculate total processing time
        final totalProcessingTime = DateTime.now().difference(frameStartTime).inMilliseconds;

        // Adjust frame interval based on processing time (adaptive frame rate)
        _updateAdaptiveFrameRate(totalProcessingTime);

        debugPrint('[LiveCamera] Frame processed successfully in ${totalProcessingTime}ms, next interval: ${_adaptiveFrameInterval}ms');

        // Check if there's a queued frame to process (Phase 3 optimization)
        _processQueuedFrame();
      }
      _isProcessingFrame = false;
    }).catchError((e, stackTrace) {
      if (mounted) {
        debugPrint('[LiveCamera] Error processing frame: $e');
        debugPrint('[LiveCamera] Stack trace: $stackTrace');
      }
      _isProcessingFrame = false;

      // Check queued frame even after error
      if (mounted) {
        _processQueuedFrame();
      }
    });
  }

  /// Process queued frame if available and not too old
  void _processQueuedFrame() {
    if (_queuedFrame != null && _queuedFrameTime != null) {
      final now = DateTime.now();
      final age = now.difference(_queuedFrameTime!).inMilliseconds;

      if (age < _maxQueueAge) {
        // Frame is fresh enough, process it
        debugPrint('[LiveCamera] Processing queued frame (age: ${age}ms)');
        final frame = _queuedFrame!;
        _queuedFrame = null;
        _queuedFrameTime = null;
        _lastFrameTime = now;
        _processFrame(frame);
      } else {
        // Frame is too old, drop it
        debugPrint('[LiveCamera] Dropped stale queued frame (age: ${age}ms)');
        _queuedFrame = null;
        _queuedFrameTime = null;
        _droppedFramesCount++;
      }
    }
  }

  /// Update adaptive frame rate based on processing time
  void _updateAdaptiveFrameRate(int processingTimeMs) {
    // If processing is faster than target, decrease interval (increase FPS)
    // If processing is slower than target, increase interval (decrease FPS)

    if (processingTimeMs < _targetProcessingTime) {
      // Processing is fast, we can capture frames more frequently
      final adjustment = (_targetProcessingTime - processingTimeMs) ~/ 2;
      _adaptiveFrameInterval = (_adaptiveFrameInterval - adjustment).clamp(_minFrameInterval, _maxFrameInterval);
    } else if (processingTimeMs > _targetProcessingTime) {
      // Processing is slow, we need to capture frames less frequently
      final adjustment = (processingTimeMs - _targetProcessingTime) ~/ 2;
      _adaptiveFrameInterval = (_adaptiveFrameInterval + adjustment).clamp(_minFrameInterval, _maxFrameInterval);
    }

    debugPrint('[LiveCamera] Adaptive FPS: ${(1000 / _adaptiveFrameInterval).toStringAsFixed(1)} FPS (interval: ${_adaptiveFrameInterval}ms, processing: ${processingTimeMs}ms)');
  }

  /// Convert CameraImage to JPEG bytes and run detection
  /// Now uses Isolates for YUV conversion and JPEG encoding (Phase 1 optimization)
  Future<void> _convertAndDetect(CameraImage image) async {
    try {
      // Check if widget is still mounted before processing
      if (!mounted) {
        debugPrint('[LiveCamera] Widget disposed, skipping frame processing');
        return;
      }

      final startTime = DateTime.now();
      debugPrint('[LiveCamera] Converting camera image...');

      // Convert CameraImage to image package format using Isolate
      final img.Image convertedImage = await _convertCameraImageAsync(image);
      final conversionTime = DateTime.now().difference(startTime).inMilliseconds;
      debugPrint('[LiveCamera] Image converted in ${conversionTime}ms: ${convertedImage.width}x${convertedImage.height}');

      // Check again before encoding (expensive operation)
      if (!mounted) {
        debugPrint('[LiveCamera] Widget disposed during conversion, skipping');
        return;
      }

      // Encode to JPEG using Isolate (reduced quality to 65 for performance)
      final encodingStartTime = DateTime.now();
      final Uint8List jpegBytes = await compute(encodeJpegInIsolate, convertedImage);
      final encodingTime = DateTime.now().difference(encodingStartTime).inMilliseconds;
      debugPrint('[LiveCamera] JPEG encoded in ${encodingTime}ms: ${jpegBytes.length} bytes');

      // Final check before sending to provider
      if (!mounted) {
        debugPrint('[LiveCamera] Widget disposed before sending to provider, skipping');
        return;
      }

      // Send to provider for detection
      final totalTime = DateTime.now().difference(startTime).inMilliseconds;
      debugPrint('[LiveCamera] Total client processing: ${totalTime}ms (conversion: ${conversionTime}ms, encoding: ${encodingTime}ms)');
      debugPrint('[LiveCamera] Sending to provider...');
      await ref.read(liveCameraProvider.notifier).processFrame(jpegBytes);

      // Check if still mounted before logging (to avoid console spam)
      if (mounted) {
        debugPrint('[LiveCamera] Frame sent to provider');
      }
    } catch (e, stackTrace) {
      debugPrint('[LiveCamera] Error converting/detecting frame: $e');
      debugPrint('[LiveCamera] Stack trace: $stackTrace');
    }
  }

  /// Convert CameraImage to img.Image asynchronously using Isolate
  Future<img.Image> _convertCameraImageAsync(CameraImage cameraImage) async {
    // Create image from YUV format using Isolate
    if (cameraImage.format.group == ImageFormatGroup.yuv420) {
      // Prepare parameters for Isolate
      final params = YuvConversionParams(
        yPlane: cameraImage.planes[0].bytes,
        uvPlane: cameraImage.planes[1].bytes,
        width: cameraImage.width,
        height: cameraImage.height,
        yRowStride: cameraImage.planes[0].bytesPerRow,
        uvRowStride: cameraImage.planes[1].bytesPerRow,
        uvPixelStride: cameraImage.planes[1].bytesPerPixel ?? 1,
        sensorOrientation: _cameraController?.description.sensorOrientation ?? 0,
        platform: defaultTargetPlatform,
      );

      // Run conversion in Isolate
      return await compute(convertYUV420InIsolate, params);
    } else if (cameraImage.format.group == ImageFormatGroup.bgra8888) {
      // BGRA conversion is fast, no need for Isolate
      return _convertBGRA8888ToImage(cameraImage);
    } else {
      throw Exception('Unsupported image format: ${cameraImage.format.group}');
    }
  }

  /// Convert CameraImage to img.Image (legacy synchronous method, kept for compatibility)
  img.Image _convertCameraImage(CameraImage cameraImage) {
    // Create image from YUV format
    if (cameraImage.format.group == ImageFormatGroup.yuv420) {
      return _convertYUV420ToImage(cameraImage);
    } else if (cameraImage.format.group == ImageFormatGroup.bgra8888) {
      return _convertBGRA8888ToImage(cameraImage);
    } else {
      throw Exception('Unsupported image format: ${cameraImage.format.group}');
    }
  }

  /// Convert YUV420 to img.Image
  img.Image _convertYUV420ToImage(CameraImage cameraImage) {
    final int width = cameraImage.width;
    final int height = cameraImage.height;

    debugPrint('[LiveCamera] Converting YUV420 image: ${width}x${height}, ${cameraImage.planes.length} planes');

    // Create image - will be filled with RGB values
    final image = img.Image(width: width, height: height);

    // Get Y plane (full resolution)
    final yPlane = cameraImage.planes[0].bytes;
    final yRowStride = cameraImage.planes[0].bytesPerRow;

    // Get UV plane(s) - half resolution (subsampled)
    final uvPlane = cameraImage.planes[1].bytes;
    final uvRowStride = cameraImage.planes[1].bytesPerRow;
    final uvPixelStride = cameraImage.planes[1].bytesPerPixel ?? 1;

    debugPrint('[LiveCamera] Y stride: $yRowStride, UV stride: $uvRowStride, UV pixel stride: $uvPixelStride');

    // Convert YUV420 to RGB
    // For NV21 format (Android): Y plane + VU interleaved plane
    for (int row = 0; row < height; row++) {
      for (int col = 0; col < width; col++) {
        // Get Y value for this pixel
        final int yIndex = row * yRowStride + col;
        if (yIndex >= yPlane.length) continue;
        final int y = yPlane[yIndex];

        // Get UV values (subsampled - one UV pair for every 2x2 block of Y values)
        final int uvRow = row ~/ 2;
        final int uvCol = col ~/ 2;
        final int uvIndex = uvRow * uvRowStride + uvCol * uvPixelStride;

        int u = 128, v = 128; // Default neutral values

        // NV21 format: V and U are interleaved (VUVUVU...)
        if (uvIndex < uvPlane.length - 1) {
          v = uvPlane[uvIndex];     // V comes first in NV21
          u = uvPlane[uvIndex + 1]; // U comes second
        }

        // YUV to RGB conversion (ITU-R BT.601 standard)
        // Using integer math for performance
        final int c = y - 16;
        final int d = u - 128;
        final int e = v - 128;

        final int r = ((298 * c + 409 * e + 128) >> 8).clamp(0, 255);
        final int g = ((298 * c - 100 * d - 208 * e + 128) >> 8).clamp(0, 255);
        final int b = ((298 * c + 516 * d + 128) >> 8).clamp(0, 255);

        image.setPixelRgba(col, row, r, g, b, 255);
      }
    }

    // Apply rotation based on camera sensor orientation
    // Android back cameras are typically mounted at 90 degrees
    if (defaultTargetPlatform == TargetPlatform.android && _cameraController != null) {
      final sensorOrientation = _cameraController!.description.sensorOrientation;
      debugPrint('[LiveCamera] Camera sensor orientation: $sensorOrientation degrees');

      // Rotate based on sensor orientation
      // Most Android back cameras need 90 degree rotation
      if (sensorOrientation == 90) {
        debugPrint('[LiveCamera] Rotating image 90 degrees clockwise');
        return img.copyRotate(image, angle: 90);
      } else if (sensorOrientation == 270) {
        debugPrint('[LiveCamera] Rotating image 270 degrees');
        return img.copyRotate(image, angle: 270);
      } else if (sensorOrientation == 180) {
        debugPrint('[LiveCamera] Rotating image 180 degrees');
        return img.copyRotate(image, angle: 180);
      }
    }

    debugPrint('[LiveCamera] No rotation applied');
    return image;
  }

  /// Convert BGRA8888 to img.Image
  img.Image _convertBGRA8888ToImage(CameraImage cameraImage) {
    final image = img.Image.fromBytes(
      width: cameraImage.width,
      height: cameraImage.height,
      bytes: cameraImage.planes[0].bytes.buffer,
      order: img.ChannelOrder.bgra,
    );
    return image;
  }

  /// Toggle voice command listening
  Future<void> _toggleVoiceCommand() async {
    if (_isListening) {
      // Stop listening
      await _speechService.stopListening();
      return;
    }

    // Initialize speech service - this will request permissions internally if needed
    debugPrint('[LiveCamera] Initializing speech service...');
    final initialized = await _speechService.initialize();

    if (!initialized) {
      debugPrint('[LiveCamera] Speech initialization failed - permissions may have been denied');
      if (mounted) {
        final l10n = AppLocalizations.of(context)!;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(l10n.speechError('Speech recognition not available. Please enable microphone and speech recognition in Settings.')),
            action: SnackBarAction(
              label: 'Settings',
              onPressed: () => openAppSettings(),
            ),
          ),
        );
      }
      return;
    }

    // Permissions granted - start listening
    debugPrint('[LiveCamera] Speech initialized, starting listening...');
    await _speechService.startListening();
  }

  /// Build toggle switch for detection/segmentation mode
  Widget _buildToggleSwitch(BuildContext context, LiveCameraState liveCameraState) {
    final l10n = AppLocalizations.of(context)!;
    final colorScheme = Theme.of(context).colorScheme;
    final isDetectionMode = liveCameraState.visualizationMode == LiveVisualizationMode.detection;

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
          _buildToggleOption(
            context: context,
            label: l10n.detection,
            icon: Icons.category,
            isSelected: isDetectionMode,
            onTap: () {
              ref.read(liveCameraProvider.notifier).switchMode(LiveVisualizationMode.detection);
            },
          ),
          _buildToggleOption(
            context: context,
            label: l10n.segmentation,
            icon: Icons.polyline,
            isSelected: !isDetectionMode,
            onTap: () {
              ref.read(liveCameraProvider.notifier).switchMode(LiveVisualizationMode.segmentation);
            },
          ),
        ],
      ),
    );
  }

  /// Build individual toggle option
  Widget _buildToggleOption({
    required BuildContext context,
    required String label,
    required IconData icon,
    required bool isSelected,
    required VoidCallback onTap,
  }) {
    final colorScheme = Theme.of(context).colorScheme;

    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: isSelected ? colorScheme.primary : Colors.transparent,
          borderRadius: BorderRadius.circular(25),
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: colorScheme.primary.withOpacity(0.3),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ]
              : null,
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              size: 18,
              color: isSelected ? colorScheme.onPrimary : colorScheme.onSurfaceVariant,
            ),
            const SizedBox(width: 6),
            Text(
              label,
              style: TextStyle(
                color: isSelected ? colorScheme.onPrimary : colorScheme.onSurfaceVariant,
                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                fontSize: 14,
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// Build opacity slider for segmentation mode
  Widget _buildOpacitySlider(BuildContext context, LiveCameraState liveCameraState) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.6),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.opacity, color: Colors.white, size: 20),
          const SizedBox(width: 8),
          SizedBox(
            width: 120,
            child: Slider(
              value: liveCameraState.opacity,
              min: 0.1,
              max: 1.0,
              divisions: 9,
              label: '${(liveCameraState.opacity * 100).toInt()}%',
              onChanged: (value) {
                ref.read(liveCameraProvider.notifier).setOpacity(value);
              },
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      backgroundColor: Colors.black,
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text(
          l10n.liveCamera,
          style: const TextStyle(
            color: Colors.white,
            shadows: [Shadow(color: Colors.black, blurRadius: 4)],
          ),
        ),
        iconTheme: const IconThemeData(
          color: Colors.white,
          shadows: [Shadow(color: Colors.black, blurRadius: 4)],
        ),
        actions: [
          // Voice command button
          IconButton(
            icon: Icon(
              _isListening ? Icons.mic : Icons.mic_none,
              color: _isListening ? Colors.red : Colors.white,
              shadows: const [Shadow(color: Colors.black, blurRadius: 4)],
            ),
            onPressed: _toggleVoiceCommand,
            tooltip: _isListening ? l10n.stopListening : l10n.voiceCommand,
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    final l10n = AppLocalizations.of(context)!;

    // Error state
    if (_errorMessage != null) {
      final isPermissionError = _errorMessage!.toLowerCase().contains('permission') ||
                                 _errorMessage!.toLowerCase().contains('denied');

      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                isPermissionError ? Icons.no_photography : Icons.error_outline,
                size: 64,
                color: Colors.red,
              ),
              const SizedBox(height: 16),
              Text(
                _errorMessage!,
                style: Theme.of(context).textTheme.bodyLarge,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),

              // Show buttons
              if (isPermissionError) ...[
                // For permission errors, show both buttons
                ElevatedButton.icon(
                  onPressed: () async {
                    await openAppSettings();
                  },
                  icon: const Icon(Icons.settings),
                  label: Text(l10n.openSettings),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                  ),
                ),
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  onPressed: () {
                    setState(() {
                      _errorMessage = null;
                    });
                    _initializeCamera();
                  },
                  icon: const Icon(Icons.refresh),
                  label: Text(l10n.retry),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                  ),
                ),
                const SizedBox(height: 16),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.blue.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.blue.withOpacity(0.3)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.info_outline, size: 20, color: Colors.blue),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          l10n.retryInstructions,
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ),
                    ],
                  ),
                ),
              ] else ...[
                // For other errors, just show retry
                ElevatedButton.icon(
                  onPressed: () {
                    setState(() {
                      _errorMessage = null;
                    });
                    _initializeCamera();
                  },
                  icon: const Icon(Icons.refresh),
                  label: Text(l10n.retry),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                  ),
                ),
              ],
            ],
          ),
        ),
      );
    }

    // Loading state
    if (!_isInitialized || _cameraController == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const CircularProgressIndicator(),
            const SizedBox(height: 16),
            Text(l10n.initializingCamera),
          ],
        ),
      );
    }

    // Camera preview with overlay
    final liveCameraState = ref.watch(liveCameraProvider);
    debugPrint('[LiveCamera] BUILD - _isDetecting: $_isDetecting');
    debugPrint('[LiveCamera] BUILD - visualizationMode: ${liveCameraState.visualizationMode}');
    debugPrint('[LiveCamera] BUILD - hasSegments: ${liveCameraState.hasSegments}');
    debugPrint('[LiveCamera] BUILD - segments.length: ${liveCameraState.segments.length}');

    final size = MediaQuery.of(context).size;
    final deviceRatio = size.width / size.height;
    final cameraRatio = _cameraController!.value.aspectRatio;

    // Calculate the preview size to fill screen while maintaining camera aspect ratio
    // Camera sensor is typically landscape oriented (aspectRatio > 1)
    late final double previewWidth;
    late final double previewHeight;

    if (deviceRatio < 1.0) {
      // Portrait mode: fill height, let width overflow
      previewHeight = size.height;
      previewWidth = previewHeight * cameraRatio;
    } else {
      // Landscape mode: fill width, let height overflow
      previewWidth = size.width;
      previewHeight = previewWidth / cameraRatio;
    }

    debugPrint('[LiveCamera] Device: ${size.width}x${size.height} (ratio: ${deviceRatio.toStringAsFixed(2)})');
    debugPrint('[LiveCamera] Camera ratio: ${cameraRatio.toStringAsFixed(2)}');
    debugPrint('[LiveCamera] Preview: ${previewWidth.toStringAsFixed(0)}x${previewHeight.toStringAsFixed(0)}');

    return Stack(
      fit: StackFit.expand,
      children: [
        // Camera preview - fullscreen
        Center(
          child: ClipRect(
            child: SizedBox(
              width: size.width,
              height: size.height,
              child: OverflowBox(
                alignment: Alignment.center,
                child: SizedBox(
                  width: previewWidth,
                  height: previewHeight,
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      CameraPreview(_cameraController!),

                      // Real-time overlay - conditional based on mode
                      if (_isDetecting) ...[
                        if (liveCameraState.visualizationMode == LiveVisualizationMode.detection) ...[
                          // Detection overlay
                          if (liveCameraState.hasDetections)
                            LiveDetectionOverlay(
                              detections: liveCameraState.detections,
                              imageMetadata: liveCameraState.imageMetadata,
                              cameraAspectRatio: cameraRatio,
                            ),
                        ] else ...[
                          // Segmentation overlay
                          if (liveCameraState.hasSegments)
                            Builder(
                              builder: (context) {
                                debugPrint('[LiveCamera] === RENDERING SEGMENTATION OVERLAY ===');
                                debugPrint('[LiveCamera] Segments: ${liveCameraState.segments.length}');
                                debugPrint('[LiveCamera] imageMetadata: ${liveCameraState.imageMetadata}');
                                debugPrint('[LiveCamera] hasSegments: ${liveCameraState.hasSegments}');
                                return LiveSegmentationOverlay(
                                  segments: liveCameraState.segments,
                                  imageMetadata: liveCameraState.imageMetadata,
                                  cameraAspectRatio: cameraRatio,
                                  opacity: liveCameraState.opacity,
                                );
                              },
                            ),
                        ],
                      ],
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),

        // Detection/Segmentation status banner
        if (_isDetecting)
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: SafeArea(
              bottom: false,
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      Colors.black.withOpacity(0.7),
                      Colors.transparent,
                    ],
                  ),
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      liveCameraState.visualizationMode == LiveVisualizationMode.detection
                          ? (_currentCommand.isNotEmpty ? l10n.detectingObject(_currentCommand) : l10n.detecting)
                          : (_currentCommand.isNotEmpty ? l10n.segmentingObject(_currentCommand) : l10n.segmenting),
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  if (liveCameraState.visualizationMode == LiveVisualizationMode.detection && liveCameraState.hasDetections) ...[
                    const SizedBox(height: 4),
                    Text(
                      l10n.objectsFound(liveCameraState.detectionCount),
                      style: TextStyle(
                        color: Colors.green[300],
                        fontSize: 14,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                  if (liveCameraState.visualizationMode == LiveVisualizationMode.segmentation && liveCameraState.hasSegments) ...[
                    const SizedBox(height: 4),
                    Text(
                      l10n.segmentsFound(liveCameraState.segmentCount),
                      style: TextStyle(
                        color: Colors.green[300],
                        fontSize: 14,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                  if (liveCameraState.lastInferenceTime != null) ...[
                    const SizedBox(height: 2),
                    Text(
                      '${liveCameraState.lastInferenceTime!.toStringAsFixed(0)}ms',
                      style: const TextStyle(
                        color: Colors.white70,
                        fontSize: 12,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ],
              ),
            ),
            ),
          ),

        // Voice command status
        if (_isListening)
          Positioned(
            top: 16,
            left: 0,
            right: 0,
            child: Center(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.red.withOpacity(0.8),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.mic, color: Colors.white, size: 16),
                        const SizedBox(width: 8),
                        Text(
                          l10n.listening,
                          style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                    if (_partialCommand.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Text(
                        '"$_partialCommand"',
                        style: const TextStyle(
                          color: Colors.white70,
                          fontSize: 12,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),

        // Toggle switch and opacity slider
        if (_isDetecting)
          Positioned(
            bottom: 120,
            left: 0,
            right: 0,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Toggle switch
                _buildToggleSwitch(context, liveCameraState),

                // Opacity slider (only in segmentation mode)
                if (liveCameraState.visualizationMode == LiveVisualizationMode.segmentation) ...[
                  const SizedBox(height: 12),
                  _buildOpacitySlider(context, liveCameraState),
                ],
              ],
            ),
          ),

        // Control buttons at bottom
        Positioned(
          bottom: 0,
          left: 0,
          right: 0,
          child: Container(
            padding: const EdgeInsets.all(24),
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
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // Instructions
                if (!_isDetecting)
                  Text(
                    l10n.liveCameraInstructions,
                    style: const TextStyle(
                      color: Colors.white70,
                      fontSize: 14,
                    ),
                    textAlign: TextAlign.center,
                  ),
                const SizedBox(height: 16),

                // Start/Stop button
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    if (_isDetecting)
                      ElevatedButton.icon(
                        onPressed: _stopDetection,
                        icon: const Icon(Icons.stop),
                        label: Text(l10n.stopDetection),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.red,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(
                            horizontal: 24,
                            vertical: 16,
                          ),
                        ),
                      )
                    else
                      ElevatedButton.icon(
                        onPressed: () {
                          // Start detection for all objects (empty string = detect all YOLO classes)
                          _startDetection('');
                        },
                        icon: const Icon(Icons.radar),
                        label: Text(l10n.startDetection),
                        style: ElevatedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 24,
                            vertical: 16,
                          ),
                        ),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
