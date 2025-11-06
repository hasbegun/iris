/// API error response
class ApiError {
  final String message;
  final int? statusCode;
  final String? detail;

  const ApiError({
    required this.message,
    this.statusCode,
    this.detail,
  });

  factory ApiError.fromJson(Map<String, dynamic> json) {
    return ApiError(
      message: json['message'] as String? ?? json['detail'] as String? ?? 'Unknown error',
      statusCode: json['status_code'] as int?,
      detail: json['detail'] as String?,
    );
  }

  factory ApiError.fromException(dynamic error) {
    return ApiError(
      message: error.toString(),
    );
  }

  @override
  String toString() => message;
}
