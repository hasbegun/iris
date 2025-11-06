import 'package:flutter/material.dart';
import '../../../core/constants/api_constants.dart';
import '../../../core/constants/app_constants.dart';

/// Application settings model
class AppSettings {
  final String backendUrl;
  final String mlServiceUrl;  // Direct ML service URL (Phase 2 optimization)
  final bool useDirectMLConnection;  // Bypass backend proxy for live camera (Phase 2 optimization)
  final String visionModel;
  final String chatModel;
  final bool devMode;
  final Locale locale;
  final ThemeMode themeMode;
  final String sttLanguage;
  final String ttsVoice;
  final double ttsRate;

  const AppSettings({
    required this.backendUrl,
    required this.mlServiceUrl,
    required this.useDirectMLConnection,
    required this.visionModel,
    required this.chatModel,
    required this.devMode,
    required this.locale,
    required this.themeMode,
    required this.sttLanguage,
    required this.ttsVoice,
    required this.ttsRate,
  });

  /// Default settings
  factory AppSettings.defaults() {
    return const AppSettings(
      backendUrl: ApiConstants.defaultBackendUrl,
      mlServiceUrl: ApiConstants.defaultMLServiceUrl,
      useDirectMLConnection: false,  // Default to backend proxy for safety
      visionModel: AppConstants.defaultVisionModel,
      chatModel: AppConstants.defaultChatModel,
      devMode: false,
      locale: Locale('en'),
      themeMode: ThemeMode.system,
      sttLanguage: 'en-US',
      ttsVoice: AppConstants.defaultTtsVoice,
      ttsRate: AppConstants.defaultTtsRate,
    );
  }

  /// Create from JSON map
  factory AppSettings.fromJson(Map<String, dynamic> json) {
    return AppSettings(
      backendUrl: json['backendUrl'] as String? ?? ApiConstants.defaultBackendUrl,
      mlServiceUrl: json['mlServiceUrl'] as String? ?? ApiConstants.defaultMLServiceUrl,
      useDirectMLConnection: json['useDirectMLConnection'] as bool? ?? false,
      visionModel: json['visionModel'] as String? ?? AppConstants.defaultVisionModel,
      chatModel: json['chatModel'] as String? ?? AppConstants.defaultChatModel,
      devMode: json['devMode'] as bool? ?? false,
      locale: Locale(json['locale'] as String? ?? 'en'),
      themeMode: _parseThemeMode(json['themeMode'] as String?),
      sttLanguage: json['sttLanguage'] as String? ?? 'en-US',
      ttsVoice: json['ttsVoice'] as String? ?? AppConstants.defaultTtsVoice,
      ttsRate: (json['ttsRate'] as num?)?.toDouble() ?? AppConstants.defaultTtsRate,
    );
  }

  /// Convert to JSON map
  Map<String, dynamic> toJson() {
    return {
      'backendUrl': backendUrl,
      'mlServiceUrl': mlServiceUrl,
      'useDirectMLConnection': useDirectMLConnection,
      'visionModel': visionModel,
      'chatModel': chatModel,
      'devMode': devMode,
      'locale': locale.languageCode,
      'themeMode': themeMode.name,
      'sttLanguage': sttLanguage,
      'ttsVoice': ttsVoice,
      'ttsRate': ttsRate,
    };
  }

  /// Copy with new values
  AppSettings copyWith({
    String? backendUrl,
    String? mlServiceUrl,
    bool? useDirectMLConnection,
    String? visionModel,
    String? chatModel,
    bool? devMode,
    Locale? locale,
    ThemeMode? themeMode,
    String? sttLanguage,
    String? ttsVoice,
    double? ttsRate,
  }) {
    return AppSettings(
      backendUrl: backendUrl ?? this.backendUrl,
      mlServiceUrl: mlServiceUrl ?? this.mlServiceUrl,
      useDirectMLConnection: useDirectMLConnection ?? this.useDirectMLConnection,
      visionModel: visionModel ?? this.visionModel,
      chatModel: chatModel ?? this.chatModel,
      devMode: devMode ?? this.devMode,
      locale: locale ?? this.locale,
      themeMode: themeMode ?? this.themeMode,
      sttLanguage: sttLanguage ?? this.sttLanguage,
      ttsVoice: ttsVoice ?? this.ttsVoice,
      ttsRate: ttsRate ?? this.ttsRate,
    );
  }

  static ThemeMode _parseThemeMode(String? value) {
    switch (value) {
      case 'light':
        return ThemeMode.light;
      case 'dark':
        return ThemeMode.dark;
      default:
        return ThemeMode.system;
    }
  }
}
