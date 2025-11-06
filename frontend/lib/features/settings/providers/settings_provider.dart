import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../shared/providers/service_providers.dart';
import '../models/app_settings.dart';

/// Settings state notifier
class SettingsNotifier extends StateNotifier<AppSettings> {
  final Ref _ref;

  SettingsNotifier(this._ref) : super(AppSettings.defaults()) {
    _loadSettings();
  }

  /// Load settings from storage
  Future<void> _loadSettings() async {
    try {
      final storageService = _ref.read(storageServiceProvider);
      final settings = await storageService.loadSettings();
      state = settings;
    } catch (e) {
      // Keep default settings on error
      debugPrint('Error loading settings: $e');
    }
  }

  /// Update backend URL
  Future<void> updateBackendUrl(String url) async {
    state = state.copyWith(backendUrl: url);
    await _saveSettings();
  }

  /// Update vision model
  Future<void> updateVisionModel(String model) async {
    state = state.copyWith(visionModel: model);
    await _saveSettings();
  }

  /// Update chat model
  Future<void> updateChatModel(String model) async {
    state = state.copyWith(chatModel: model);
    await _saveSettings();
  }

  /// Toggle developer mode
  Future<void> toggleDevMode(bool enabled) async {
    state = state.copyWith(devMode: enabled);
    await _saveSettings();
  }

  /// Update locale
  Future<void> updateLocale(Locale locale) async {
    state = state.copyWith(locale: locale);
    await _saveSettings();
  }

  /// Update theme mode
  Future<void> updateThemeMode(ThemeMode mode) async {
    state = state.copyWith(themeMode: mode);
    await _saveSettings();
  }

  /// Update STT language
  Future<void> updateSttLanguage(String language) async {
    state = state.copyWith(sttLanguage: language);
    await _saveSettings();
  }

  /// Update TTS voice
  Future<void> updateTtsVoice(String voice) async {
    state = state.copyWith(ttsVoice: voice);
    await _saveSettings();
  }

  /// Update TTS rate
  Future<void> updateTtsRate(double rate) async {
    state = state.copyWith(ttsRate: rate);
    await _saveSettings();
  }

  /// Reset to defaults
  Future<void> resetToDefaults() async {
    state = AppSettings.defaults();
    await _saveSettings();
  }

  /// Save current settings to storage
  Future<void> _saveSettings() async {
    try {
      final storageService = _ref.read(storageServiceProvider);
      await storageService.saveSettings(state);
    } catch (e) {
      debugPrint('Error saving settings: $e');
    }
  }
}

/// Provider for app settings
final settingsProvider = StateNotifierProvider<SettingsNotifier, AppSettings>((ref) {
  return SettingsNotifier(ref);
});

/// Provider for current theme mode
final themeModeProvider = Provider<ThemeMode>((ref) {
  return ref.watch(settingsProvider).themeMode;
});

/// Provider for current locale
final localeProvider = Provider<Locale>((ref) {
  return ref.watch(settingsProvider).locale;
});

/// Provider for developer mode
final devModeProvider = Provider<bool>((ref) {
  return ref.watch(settingsProvider).devMode;
});
