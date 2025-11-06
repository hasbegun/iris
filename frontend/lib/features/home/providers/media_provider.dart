import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import '../models/media_item.dart';
import '../../api/providers/analysis_provider.dart';

/// Media state
class MediaState {
  final MediaItem? mediaItem;
  final bool isLoading;
  final String? error;

  const MediaState({
    this.mediaItem,
    this.isLoading = false,
    this.error,
  });

  MediaState copyWith({
    MediaItem? mediaItem,
    bool? isLoading,
    String? error,
    bool clearMedia = false,
    bool clearError = false,
  }) {
    return MediaState(
      mediaItem: clearMedia ? null : (mediaItem ?? this.mediaItem),
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
    );
  }
}

/// Media provider notifier
class MediaNotifier extends StateNotifier<MediaState> {
  final ImagePicker _picker = ImagePicker();
  final Ref _ref;

  MediaNotifier(this._ref) : super(const MediaState());

  /// Pick image from gallery
  Future<void> pickImageFromGallery() async {
    try {
      state = state.copyWith(isLoading: true, clearError: true);

      final XFile? xFile = await _picker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 1920,
        maxHeight: 1080,
        imageQuality: 85,
      );

      if (xFile == null) {
        state = state.copyWith(isLoading: false);
        return;
      }

      await _handleSelectedFile(xFile, MediaType.image);
    } catch (e) {
      debugPrint('Error picking image: $e');
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to pick image: ${e.toString()}',
      );
    }
  }

  /// Pick image from camera
  Future<void> pickImageFromCamera() async {
    try {
      state = state.copyWith(isLoading: true, clearError: true);

      final XFile? xFile = await _picker.pickImage(
        source: ImageSource.camera,
        maxWidth: 1920,
        maxHeight: 1080,
        imageQuality: 85,
      );

      if (xFile == null) {
        state = state.copyWith(isLoading: false);
        return;
      }

      await _handleSelectedFile(xFile, MediaType.image);
    } catch (e) {
      debugPrint('Error taking photo: $e');
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to take photo: ${e.toString()}',
      );
    }
  }

  /// Pick video from gallery
  Future<void> pickVideoFromGallery() async {
    try {
      state = state.copyWith(isLoading: true, clearError: true);

      final XFile? xFile = await _picker.pickVideo(
        source: ImageSource.gallery,
        maxDuration: const Duration(seconds: 60), // 1 minute max
      );

      if (xFile == null) {
        state = state.copyWith(isLoading: false);
        return;
      }

      await _handleSelectedFile(xFile, MediaType.video);
    } catch (e) {
      debugPrint('Error picking video: $e');
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to pick video: ${e.toString()}',
      );
    }
  }

  /// Handle selected file
  Future<void> _handleSelectedFile(XFile xFile, MediaType type) async {
    try {
      final file = File(xFile.path);
      final fileSize = await file.length();
      final fileName = xFile.name;

      // Check file size (20MB max for images, 100MB for videos)
      final maxSize = type == MediaType.image ? 20 * 1024 * 1024 : 100 * 1024 * 1024;

      // Debug logging
      final fileSizeMB = fileSize / (1024 * 1024);
      final maxSizeMB = maxSize / (1024 * 1024);
      debugPrint('File size check: ${fileSizeMB.toStringAsFixed(2)}MB / ${maxSizeMB.toStringAsFixed(0)}MB (type: $type)');

      if (fileSize > maxSize) {
        final actualSizeMB = (fileSize / (1024 * 1024)).toStringAsFixed(2);
        final maxDisplayMB = (maxSize / (1024 * 1024)).toStringAsFixed(0);
        debugPrint('❌ File too large: $actualSizeMB MB > $maxDisplayMB MB');
        state = state.copyWith(
          isLoading: false,
          error: 'File too large ($actualSizeMB MB). Max size: $maxDisplayMB MB',
        );
        return;
      }

      debugPrint('✅ File size OK: ${fileSizeMB.toStringAsFixed(2)}MB');

      final mediaItem = MediaItem(
        file: file,
        type: type,
        fileName: fileName,
        fileSizeBytes: fileSize,
      );

      // Clear conversation when new media is selected
      _ref.read(analysisProvider.notifier).startNewSession();
      debugPrint('New media selected - conversation cleared');

      state = state.copyWith(
        mediaItem: mediaItem,
        isLoading: false,
        clearError: true,
      );

      debugPrint('Selected media: $mediaItem');
    } catch (e) {
      debugPrint('Error handling file: $e');
      state = state.copyWith(
        isLoading: false,
        error: 'Failed to process file: ${e.toString()}',
      );
    }
  }

  /// Clear selected media
  void clearMedia() {
    state = state.copyWith(clearMedia: true, clearError: true);
  }

  /// Clear error
  void clearError() {
    state = state.copyWith(clearError: true);
  }
}

/// Provider for media management
final mediaProvider = StateNotifierProvider<MediaNotifier, MediaState>((ref) {
  return MediaNotifier(ref);
});

/// Provider for selected media item
final selectedMediaProvider = Provider<MediaItem?>((ref) {
  return ref.watch(mediaProvider).mediaItem;
});

/// Provider for media loading state
final mediaLoadingProvider = Provider<bool>((ref) {
  return ref.watch(mediaProvider).isLoading;
});

/// Provider for media error
final mediaErrorProvider = Provider<String?>((ref) {
  return ref.watch(mediaProvider).error;
});
