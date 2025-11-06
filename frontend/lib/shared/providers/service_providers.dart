import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/storage_service.dart';

/// Provider for SharedPreferences instance
final sharedPreferencesProvider = Provider<SharedPreferences>((ref) {
  throw UnimplementedError('SharedPreferences must be overridden');
});

/// Provider for StorageService
final storageServiceProvider = Provider<StorageService>((ref) {
  final prefs = ref.watch(sharedPreferencesProvider);
  return StorageService(prefs);
});
