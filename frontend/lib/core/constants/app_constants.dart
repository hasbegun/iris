/// Application-wide constants
class AppConstants {
  // App Info
  static const String appName = 'Iris';
  static const String appVersion = '1.0.0';

  // Storage Keys
  static const String keyBackendUrl = 'backend_url';
  static const String keyVisionModel = 'vision_model';
  static const String keyChatModel = 'chat_model';
  static const String keyDevMode = 'dev_mode';
  static const String keyLocale = 'locale';
  static const String keyThemeMode = 'theme_mode';
  static const String keySttLanguage = 'stt_language';
  static const String keyTtsVoice = 'tts_voice';
  static const String keyTtsRate = 'tts_rate';

  // Default Model Names
  static const String defaultVisionModel = 'llava:latest';
  static const String defaultChatModel = 'gemma3:latest';

  // Default TTS Settings
  static const String defaultTtsVoice = 'en-US';
  static const double defaultTtsRate = 0.5;

  // Supported Locales
  static const List<String> supportedLocaleCodes = ['en', 'ko', 'ja', 'es'];

  // Media
  static const int maxImageSizeMB = 10;
  static const int maxVideoLengthSeconds = 60;
  static const List<String> supportedImageFormats = ['jpg', 'jpeg', 'png', 'webp'];
  static const List<String> supportedVideoFormats = ['mp4', 'mov', 'avi'];
}
