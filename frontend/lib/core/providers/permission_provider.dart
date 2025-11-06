import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/permission_service.dart';

/// Provider for permission service
final permissionServiceProvider = Provider<PermissionService>((ref) {
  return PermissionService();
});
