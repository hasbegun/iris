import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../../features/settings/models/app_settings.dart';

/// Service for persisting application settings
class StorageService {
  static const String _settingsKey = 'app_settings';

  final SharedPreferences _prefs;

  StorageService(this._prefs);

  /// Load settings from storage
  Future<AppSettings> loadSettings() async {
    try {
      final jsonString = _prefs.getString(_settingsKey);
      if (jsonString == null) {
        return AppSettings.defaults();
      }

      final json = jsonDecode(jsonString) as Map<String, dynamic>;
      return AppSettings.fromJson(json);
    } catch (e) {
      // If there's any error loading, return defaults
      return AppSettings.defaults();
    }
  }

  /// Save settings to storage
  Future<bool> saveSettings(AppSettings settings) async {
    try {
      final jsonString = jsonEncode(settings.toJson());
      return await _prefs.setString(_settingsKey, jsonString);
    } catch (e) {
      return false;
    }
  }

  /// Clear all settings
  Future<bool> clearSettings() async {
    return await _prefs.remove(_settingsKey);
  }

  /// Save a single value
  Future<bool> saveString(String key, String value) async {
    return await _prefs.setString(key, value);
  }

  /// Get a single value
  String? getString(String key) {
    return _prefs.getString(key);
  }

  /// Save boolean value
  Future<bool> saveBool(String key, bool value) async {
    return await _prefs.setBool(key, value);
  }

  /// Get boolean value
  bool? getBool(String key) {
    return _prefs.getBool(key);
  }

  /// Save double value
  Future<bool> saveDouble(String key, double value) async {
    return await _prefs.setDouble(key, value);
  }

  /// Get double value
  double? getDouble(String key) {
    return _prefs.getDouble(key);
  }
}
