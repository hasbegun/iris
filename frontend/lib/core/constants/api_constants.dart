/// API endpoints and configuration constants
class ApiConstants {
  // Default backend URL (can be overridden in settings)
  // Use network IP for Android/iOS devices (localhost won't work on physical devices)
  static const String defaultBackendUrl = 'http://192.168.4.10:9000';

  // API Endpoints
  static const String visionAnalyzeEndpoint = '/api/vision/analyze';
  static const String agentAnalyzeEndpoint = '/api/agent/analyze';
  static const String visionStreamEndpoint = '/api/vision/stream';
  static const String chatEndpoint = '/api/chat';
  static const String healthEndpoint = '/api/health';

  // Timeouts
  static const Duration connectTimeout = Duration(seconds: 30);
  static const Duration receiveTimeout = Duration(seconds: 120);
  static const Duration sendTimeout = Duration(seconds: 60);

  // Retry configuration
  static const int maxRetries = 3;
  static const Duration retryDelay = Duration(seconds: 2);
}