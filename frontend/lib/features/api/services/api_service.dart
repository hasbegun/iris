import 'dart:io';
import 'dart:typed_data';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:http_parser/http_parser.dart';
import '../models/vision_response.dart';
import '../models/api_error.dart';
import '../models/detection.dart';
import '../models/voice_query_response.dart';

/// Service for backend API communication
class ApiService {
  late Dio _dio;
  String _baseUrl;

  ApiService(this._baseUrl) {
    _dio = Dio(BaseOptions(
      baseUrl: _baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 60),
      headers: {
        'Accept': 'application/json',
      },
    ));

    // Add logging interceptor
    _dio.interceptors.add(LogInterceptor(
      requestBody: true,
      responseBody: true,
      logPrint: (obj) => debugPrint(obj.toString()),
    ));
  }

  /// Update base URL
  void updateBaseUrl(String newUrl) {
    _baseUrl = newUrl;
    _dio.options.baseUrl = newUrl;
  }

  /// Analyze image with prompt using AI agent
  Future<VisionResponse> analyzeImage({
    required File imageFile,
    required String prompt,
    String? sessionId,
  }) async {
    try {
      final formData = FormData.fromMap({
        'image': await MultipartFile.fromFile(
          imageFile.path,
          filename: imageFile.path.split('/').last,
          contentType: MediaType('image', _getImageExtension(imageFile.path)),
        ),
        'prompt': prompt,
        if (sessionId != null) 'session_id': sessionId,
      });

      final response = await _dio.post(
        '/api/agent/analyze',  // Changed from /api/vision/analyze to use agent
        data: formData,
      );

      return VisionResponse.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleDioError(e);
    } catch (e) {
      throw ApiError.fromException(e);
    }
  }

  /// Analyze video with prompt using AI agent
  /// Note: Currently agent endpoint expects 'image' parameter, so we send video as 'image'
  Future<VisionResponse> analyzeVideo({
    required File videoFile,
    required String prompt,
    String? sessionId,
  }) async {
    try {
      final formData = FormData.fromMap({
        'image': await MultipartFile.fromFile(  // Agent endpoint expects 'image' parameter
          videoFile.path,
          filename: videoFile.path.split('/').last,
          contentType: MediaType('video', _getVideoExtension(videoFile.path)),
        ),
        'prompt': prompt,
        if (sessionId != null) 'session_id': sessionId,
      });

      final response = await _dio.post(
        '/api/agent/analyze',  // Changed from /api/vision/analyze to use agent
        data: formData,
      );

      return VisionResponse.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleDioError(e);
    } catch (e) {
      throw ApiError.fromException(e);
    }
  }

  /// Fetch image bytes from backend (for video frame visualization)
  Future<Uint8List?> fetchImageBytes(String sessionId) async {
    try {
      debugPrint('[ApiService] Fetching image bytes for session: $sessionId');

      final response = await _dio.get(
        '/api/agent/session/$sessionId/frame',
        options: Options(responseType: ResponseType.bytes),
      );

      if (response.statusCode == 200 && response.data != null) {
        final bytes = Uint8List.fromList(response.data as List<int>);
        debugPrint('[ApiService] Fetched ${bytes.length} bytes for session frame');
        return bytes;
      }

      return null;
    } catch (e) {
      debugPrint('[ApiService] Failed to fetch image bytes: $e');
      return null;
    }
  }

  /// Fetch specific video frame by index (for slideshow)
  Future<Uint8List?> fetchFrameByIndex(String sessionId, int frameIndex) async {
    try {
      debugPrint('[ApiService] Fetching frame $frameIndex for session: $sessionId');

      final response = await _dio.get(
        '/api/agent/session/$sessionId/frame',
        queryParameters: {'frame_index': frameIndex},
        options: Options(responseType: ResponseType.bytes),
      );

      if (response.statusCode == 200 && response.data != null) {
        final bytes = Uint8List.fromList(response.data as List<int>);
        debugPrint('[ApiService] Fetched ${bytes.length} bytes for frame $frameIndex');
        return bytes;
      }

      return null;
    } catch (e) {
      debugPrint('[ApiService] Failed to fetch frame $frameIndex: $e');
      return null;
    }
  }

  /// Fetch video frames metadata (for slideshow)
  Future<VideoFramesMetadata?> fetchVideoFramesMetadata(String sessionId) async {
    try {
      debugPrint('[ApiService] Fetching video frames metadata for session: $sessionId');

      final response = await _dio.get(
        '/api/agent/session/$sessionId/video-frames',
      );

      if (response.statusCode == 200 && response.data != null) {
        final metadata = VideoFramesMetadata.fromJson(response.data as Map<String, dynamic>);
        debugPrint('[ApiService] Fetched metadata for ${metadata.framesCount} frames');
        return metadata;
      }

      return null;
    } catch (e) {
      debugPrint('[ApiService] Failed to fetch video frames metadata: $e');
      return null;
    }
  }

  /// Detect objects in image (returns JSON with bounding boxes)
  Future<DetectionResponse> detectImage({
    required File imageFile,
    double confidence = 0.5,
    List<String>? classes,
  }) async {
    try {
      final formData = FormData.fromMap({
        'image': await MultipartFile.fromFile(
          imageFile.path,
          filename: imageFile.path.split('/').last,
          contentType: MediaType('image', _getImageExtension(imageFile.path)),
        ),
        'confidence': confidence,
        if (classes != null && classes.isNotEmpty)
          'classes': classes.join(','),
      });

      final response = await _dio.post(
        '/api/detect',
        data: formData,
      );

      return DetectionResponse.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleDioError(e);
    } catch (e) {
      throw ApiError.fromException(e);
    }
  }

  /// Detect objects in image (returns annotated JPEG)
  Future<Uint8List> detectImageAnnotated({
    required File imageFile,
    double confidence = 0.5,
    List<String>? classes,
    int lineWidth = 3,
    int fontSize = 20,
  }) async {
    try {
      final formData = FormData.fromMap({
        'image': await MultipartFile.fromFile(
          imageFile.path,
          filename: imageFile.path.split('/').last,
          contentType: MediaType('image', _getImageExtension(imageFile.path)),
        ),
        'confidence': confidence,
        if (classes != null && classes.isNotEmpty)
          'classes': classes.join(','),
        'line_width': lineWidth,
        'font_size': fontSize,
      });

      final response = await _dio.post(
        '/api/detect-annotated',
        data: formData,
        options: Options(responseType: ResponseType.bytes),
      );

      return Uint8List.fromList(response.data as List<int>);
    } on DioException catch (e) {
      throw _handleDioError(e);
    } catch (e) {
      throw ApiError.fromException(e);
    }
  }

  /// Segment objects in image (returns JSON with polygon masks)
  Future<SegmentationResponse> segmentImage({
    required File imageFile,
    double confidence = 0.5,
    List<String>? classes,
  }) async {
    try {
      final formData = FormData.fromMap({
        'image': await MultipartFile.fromFile(
          imageFile.path,
          filename: imageFile.path.split('/').last,
          contentType: MediaType('image', _getImageExtension(imageFile.path)),
        ),
        'confidence': confidence,
        if (classes != null && classes.isNotEmpty)
          'classes': classes.join(','),
      });

      final response = await _dio.post(
        '/api/segment',
        data: formData,
      );

      return SegmentationResponse.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleDioError(e);
    } catch (e) {
      throw ApiError.fromException(e);
    }
  }

  /// Segment objects in image from bytes (returns JSON with polygon masks)
  Future<SegmentationResponse> segmentImageFromBytes({
    required Uint8List imageBytes,
    double confidence = 0.5,
    List<String>? classes,
    String filename = 'image.jpg',
  }) async {
    try {
      final formData = FormData.fromMap({
        'image': MultipartFile.fromBytes(
          imageBytes,
          filename: filename,
          contentType: MediaType('image', _getImageExtension(filename)),
        ),
        'confidence': confidence,
        if (classes != null && classes.isNotEmpty)
          'classes': classes.join(','),
      });

      final response = await _dio.post(
        '/api/segment',
        data: formData,
      );

      return SegmentationResponse.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleDioError(e);
    } catch (e) {
      throw ApiError.fromException(e);
    }
  }

  /// Segment objects in image (returns annotated JPEG with masks)
  Future<Uint8List> segmentImageAnnotated({
    required File imageFile,
    double confidence = 0.5,
    List<String>? classes,
    double opacity = 0.5,
    int lineWidth = 2,
    int fontSize = 20,
  }) async {
    try {
      final formData = FormData.fromMap({
        'image': await MultipartFile.fromFile(
          imageFile.path,
          filename: imageFile.path.split('/').last,
          contentType: MediaType('image', _getImageExtension(imageFile.path)),
        ),
        'confidence': confidence,
        if (classes != null && classes.isNotEmpty)
          'classes': classes.join(','),
        'opacity': opacity,
        'line_width': lineWidth,
        'font_size': fontSize,
      });

      final response = await _dio.post(
        '/api/segment-annotated',
        data: formData,
        options: Options(responseType: ResponseType.bytes),
      );

      return Uint8List.fromList(response.data as List<int>);
    } on DioException catch (e) {
      throw _handleDioError(e);
    } catch (e) {
      throw ApiError.fromException(e);
    }
  }

  /// Enrich video frames with segmentation data
  Future<VideoFramesMetadata> segmentVideoFrames({
    required String sessionId,
    double confidence = 0.7,
  }) async {
    try {
      debugPrint('[ApiService] Enriching video frames with segmentation for session: $sessionId');

      final response = await _dio.post(
        '/api/agent/session/$sessionId/segment-video-frames',
        data: {
          'confidence': confidence,
        },
      );

      if (response.statusCode == 200 && response.data != null) {
        final responseData = response.data as Map<String, dynamic>;
        final metadata = VideoFramesMetadata.fromJson(
          responseData['video_frames_metadata'] as Map<String, dynamic>,
        );
        debugPrint('[ApiService] Enriched ${metadata.framesCount} frames with segmentation');
        return metadata;
      }

      throw ApiError(message: 'Failed to enrich video frames with segmentation');
    } on DioException catch (e) {
      throw _handleDioError(e);
    } catch (e) {
      throw ApiError.fromException(e);
    }
  }

  /// Voice query: Analyze frame with voice query and hallucination prevention
  Future<VoiceQueryResponse> voiceQuery({
    required Uint8List imageBytes,
    required String query,
    String? sessionId,
    bool verifyWithDetection = true,
    double confidence = 0.7,
  }) async {
    try {
      final formData = FormData.fromMap({
        'image': MultipartFile.fromBytes(
          imageBytes,
          filename: 'frame.jpg',
          contentType: MediaType('image', 'jpeg'),
        ),
        'query': query,
        if (sessionId != null) 'session_id': sessionId,
        'verify_with_detection': verifyWithDetection,
        'confidence': confidence,
      });

      final response = await _dio.post(
        '/api/voice-query/analyze',
        data: formData,
      );

      return VoiceQueryResponse.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleDioError(e);
    } catch (e) {
      throw ApiError.fromException(e);
    }
  }

  /// Check backend health
  Future<bool> checkHealth() async {
    try {
      final response = await _dio.get('/health');
      return response.statusCode == 200;
    } catch (e) {
      debugPrint('Health check failed: $e');
      return false;
    }
  }

  /// Get image file extension
  String _getImageExtension(String path) {
    final extension = path.split('.').last.toLowerCase();
    switch (extension) {
      case 'jpg':
      case 'jpeg':
        return 'jpeg';
      case 'png':
        return 'png';
      case 'webp':
        return 'webp';
      default:
        return 'jpeg';
    }
  }

  /// Get video file extension
  String _getVideoExtension(String path) {
    final extension = path.split('.').last.toLowerCase();
    switch (extension) {
      case 'mp4':
        return 'mp4';
      case 'mov':
        return 'quicktime';
      case 'avi':
        return 'x-msvideo';
      default:
        return 'mp4';
    }
  }

  /// Handle Dio errors
  ApiError _handleDioError(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return ApiError(
          message: 'Connection timeout. Please check your network.',
          statusCode: error.response?.statusCode,
        );

      case DioExceptionType.badResponse:
        final statusCode = error.response?.statusCode;
        final data = error.response?.data;

        String message = 'Server error occurred';
        if (data is Map<String, dynamic>) {
          // Handle FastAPI validation errors (detail can be a list or string)
          final detail = data['detail'];
          if (detail is String) {
            message = detail;
          } else if (detail is List) {
            // Extract validation error messages
            final errors = detail.map((e) {
              if (e is Map<String, dynamic>) {
                final field = (e['loc'] as List?)?.join('.') ?? 'field';
                final msg = e['msg'] ?? 'validation error';
                return '$field: $msg';
              }
              return e.toString();
            }).join(', ');
            message = errors.isNotEmpty ? errors : message;
          } else {
            message = data['message'] as String? ?? message;
          }
        }

        return ApiError(
          message: message,
          statusCode: statusCode,
          detail: data.toString(),
        );

      case DioExceptionType.cancel:
        return const ApiError(message: 'Request cancelled');

      case DioExceptionType.connectionError:
        return ApiError(
          message: 'Cannot connect to server at $_baseUrl. Please check your settings.',
          statusCode: error.response?.statusCode,
        );

      default:
        return ApiError(
          message: error.message ?? 'Unknown error occurred',
          statusCode: error.response?.statusCode,
        );
    }
  }
}
