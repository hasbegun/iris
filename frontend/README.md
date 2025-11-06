# Iris - AI Vision Assistant (Flutter App)

Flutter mobile application for vision analysis powered by Ollama.

## ✅ Phase 1 + 2 Complete

### Implemented Features

- ✅ **Project renamed** from `frontend` to `iris`
- ✅ **Riverpod state management** (compile-time safe, minimal boilerplate)
- ✅ **Theme system** (Light/Dark/System with Material 3)
- ✅ **Internationalization** (English, Korean, Japanese, Spanish placeholders)
- ✅ **Settings management** with persistent storage
- ✅ **Developer mode** for backend configuration

## Getting Started

### Prerequisites

- Flutter SDK 3.9.0 or higher
- Dart 3.9.0 or higher

### Installation

```bash
# Install dependencies
flutter pub get

# Run the app
flutter run
```

### Running on Platforms

```bash
# iOS Simulator
flutter run -d ios

# Android Emulator
flutter run -d android

# macOS Desktop
flutter run -d macos
```

## Settings

Tap the gear icon (⚙️) in the top-right corner to access settings.

### General
- **Theme**: Light, Dark, or System
- **Language**: English, Korean, Japanese, Spanish

### Developer Mode
Enable to configure:
- **Backend URL**: Server address (default: `http://localhost:9000`)
- **Vision Model**: Ollama model (default: `llava:latest`)
- **Chat Model**: Ollama model (default: `gemma3:latest`)

### Speech
- **Speech Rate**: Adjust TTS speed (0.1 - 1.0)

## Architecture

**State Management**: Riverpod (chosen for minimal boilerplate and type safety)

```
lib/
├── core/              # Theme, constants, utilities
├── features/          # Feature modules
│   ├── home/         # Home screen
│   └── settings/     # Settings screen
├── shared/            # Shared services & widgets
└── l10n/              # Localization files
```

## Dependencies

See `pubspec.yaml` for full list. Key packages:
- `flutter_riverpod` - State management
- `shared_preferences` - Settings storage
- `dio` - HTTP client (for Phase 5)
- `image_picker`, `video_player` - Media (for Phase 3)
- `speech_to_text`, `flutter_tts` - Speech (for Phase 4)

## Next Steps

- **Phase 3**: Media selection & display (images/videos)
- **Phase 4**: Text & voice prompt input
- **Phase 5**: Backend API integration
- **Phase 6**: Response display & TTS
- **Phase 7**: Testing & polish

## License

See project root for license information.
