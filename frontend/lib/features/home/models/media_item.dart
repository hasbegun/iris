import 'dart:io';

/// Type of media
enum MediaType {
  image,
  video,
}

/// Media item model representing selected image or video
class MediaItem {
  final File file;
  final MediaType type;
  final String fileName;
  final int fileSizeBytes;
  final DateTime selectedAt;

  MediaItem({
    required this.file,
    required this.type,
    required this.fileName,
    required this.fileSizeBytes,
    DateTime? selectedAt,
  }) : selectedAt = selectedAt ?? DateTime.now();

  /// Check if media is an image
  bool get isImage => type == MediaType.image;

  /// Check if media is a video
  bool get isVideo => type == MediaType.video;

  /// Get file size in MB
  double get fileSizeMB => fileSizeBytes / (1024 * 1024);

  /// Get file extension
  String get extension => fileName.split('.').last.toLowerCase();

  @override
  String toString() {
    return 'MediaItem(type: $type, fileName: $fileName, size: ${fileSizeMB.toStringAsFixed(2)}MB)';
  }
}
