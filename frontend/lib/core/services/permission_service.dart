import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';

/// Service to handle app permissions
class PermissionService {
  /// Request camera permission
  Future<bool> requestCameraPermission() async {
    final status = await Permission.camera.request();
    return status.isGranted;
  }

  /// Request photo library permission
  Future<bool> requestPhotoLibraryPermission() async {
    final status = await Permission.photos.request();
    return status.isGranted;
  }

  /// Request microphone permission
  Future<bool> requestMicrophonePermission() async {
    final status = await Permission.microphone.request();
    return status.isGranted;
  }

  /// Check if camera permission is granted
  Future<bool> isCameraPermissionGranted() async {
    return await Permission.camera.isGranted;
  }

  /// Check if photo library permission is granted
  Future<bool> isPhotoLibraryPermissionGranted() async {
    return await Permission.photos.isGranted;
  }

  /// Check if microphone permission is granted
  Future<bool> isMicrophonePermissionGranted() async {
    return await Permission.microphone.isGranted;
  }

  /// Request permission with user-friendly dialog
  Future<bool> requestPermissionWithDialog({
    required BuildContext context,
    required Permission permission,
    required String title,
    required String message,
  }) async {
    // Check current status
    final status = await permission.status;

    if (status.isGranted) {
      return true;
    }

    if (status.isPermanentlyDenied) {
      // Show dialog to open app settings
      if (context.mounted) {
        final shouldOpenSettings = await _showPermissionDialog(
          context: context,
          title: '$title - Permission Denied',
          message: '$message\n\nPlease enable this permission in Settings.',
          confirmText: 'Open Settings',
        );

        if (shouldOpenSettings == true) {
          await openAppSettings();
        }
      }
      return false;
    }

    // Request permission
    final result = await permission.request();
    return result.isGranted;
  }

  /// Show permission dialog
  Future<bool?> _showPermissionDialog({
    required BuildContext context,
    required String title,
    required String message,
    String confirmText = 'OK',
  }) async {
    return showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(confirmText),
          ),
        ],
      ),
    );
  }

  /// Request camera permission with dialog
  Future<bool> requestCameraWithDialog(BuildContext context) async {
    return requestPermissionWithDialog(
      context: context,
      permission: Permission.camera,
      title: 'Camera Access',
      message: 'Iris needs access to your camera to take photos for vision analysis.',
    );
  }

  /// Request photo library permission with dialog
  Future<bool> requestPhotoLibraryWithDialog(BuildContext context) async {
    return requestPermissionWithDialog(
      context: context,
      permission: Permission.photos,
      title: 'Photo Library Access',
      message: 'Iris needs access to your photo library to select images and videos for vision analysis.',
    );
  }

  /// Request microphone permission with dialog
  Future<bool> requestMicrophoneWithDialog(BuildContext context) async {
    return requestPermissionWithDialog(
      context: context,
      permission: Permission.microphone,
      title: 'Microphone Access',
      message: 'Iris needs access to your microphone to enable voice input for prompts.',
    );
  }
}
