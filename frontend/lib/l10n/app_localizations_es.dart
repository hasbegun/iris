// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Spanish Castilian (`es`).
class AppLocalizationsEs extends AppLocalizations {
  AppLocalizationsEs([String locale = 'es']) : super(locale);

  @override
  String get appTitle => 'Iris';

  @override
  String get home => 'Inicio';

  @override
  String get settings => 'Configuración';

  @override
  String get selectImage => 'Seleccionar imagen';

  @override
  String get selectVideo => 'Seleccionar video';

  @override
  String get enterPrompt => 'Ingrese su pregunta...';

  @override
  String get promptHint => 'Ask a question about the image...';

  @override
  String get send => 'Enviar';

  @override
  String get speak => 'Hablar';

  @override
  String get listening => 'Escuchando...';

  @override
  String get starting => 'Starting...';

  @override
  String get stopRecording => 'Stop Recording';

  @override
  String get startRecording => 'Start Recording';

  @override
  String get processing => 'Procesando...';

  @override
  String get readAloud => 'Leer en voz alta';

  @override
  String get backendUrl => 'URL del backend';

  @override
  String get visionModel => 'Modelo de visión';

  @override
  String get chatModel => 'Modelo de chat';

  @override
  String get devMode => 'Modo desarrollador';

  @override
  String get theme => 'Tema';

  @override
  String get language => 'Idioma';

  @override
  String get light => 'Claro';

  @override
  String get dark => 'Oscuro';

  @override
  String get system => 'Sistema';

  @override
  String get english => 'English';

  @override
  String get korean => '한국어';

  @override
  String get japanese => '日本語';

  @override
  String get spanish => 'Español';

  @override
  String get save => 'Guardar';

  @override
  String get cancel => 'Cancelar';

  @override
  String get error => 'Error';

  @override
  String get connectionError =>
      'No se pudo conectar al servidor. Verifique su configuración.';

  @override
  String get invalidUrl => 'Formato de URL inválido';

  @override
  String get noMediaSelected => 'No hay medios seleccionados';

  @override
  String get generalSettings => 'General';

  @override
  String get developerSettings => 'Desarrollador';

  @override
  String get speechSettings => 'Voz';

  @override
  String get ttsVoice => 'Voz TTS';

  @override
  String get ttsRate => 'Velocidad de habla';

  @override
  String get dismiss => 'Dismiss';

  @override
  String get selectMedia => 'Select Media';

  @override
  String get takePhoto => 'Take Photo';

  @override
  String get pleaseEnterQuestion => 'Please enter a question';

  @override
  String get loadingMedia => 'Loading media...';

  @override
  String get backendUrlHint => 'http://localhost:9000';

  @override
  String get backendUrlHelper => 'Enter the backend server URL';

  @override
  String get modelNameHint => 'Enter the model name';

  @override
  String get liveCamera => 'Live Camera';

  @override
  String get microphonePermissionNeeded =>
      'Microphone permission needed for voice commands';

  @override
  String speechError(String error) {
    return 'Speech error: $error';
  }

  @override
  String findingObject(String object) {
    return 'Finding: $object';
  }

  @override
  String get detectionStopped => 'Detection stopped';

  @override
  String get pauseNotImplemented => 'Pause not yet implemented';

  @override
  String get resumeNotImplemented => 'Resume not yet implemented';

  @override
  String unknownCommand(String command) {
    return 'Unknown command: $command';
  }

  @override
  String get noCamerasAvailable => 'No cameras available on this device';

  @override
  String get cameraPermissionDenied =>
      'Camera permission denied. Please enable it in Settings > Iris > Camera.';

  @override
  String cameraError(String error) {
    return 'Camera error: $error';
  }

  @override
  String cameraInitializationFailed(String error) {
    return 'Failed to initialize camera: $error';
  }

  @override
  String cameraStreamFailed(String error) {
    return 'Failed to start camera stream: $error';
  }

  @override
  String get detection => 'Detection';

  @override
  String get segmentation => 'Segmentation';

  @override
  String get stopListening => 'Stop listening';

  @override
  String get voiceCommand => 'Voice command';

  @override
  String get openSettings => 'Open Settings';

  @override
  String get retry => 'Retry';

  @override
  String get retryInstructions =>
      'Enable Camera permission in Settings, then tap Retry';

  @override
  String get initializingCamera => 'Initializing camera...';

  @override
  String get detecting => 'Detecting...';

  @override
  String detectingObject(String object) {
    return 'Detecting: $object';
  }

  @override
  String get segmenting => 'Segmenting...';

  @override
  String segmentingObject(String object) {
    return 'Segmenting: $object';
  }

  @override
  String objectsFound(int count) {
    return '$count object(s) found';
  }

  @override
  String segmentsFound(int count) {
    return '$count segment(s) found';
  }

  @override
  String get liveCameraInstructions =>
      'Tap button below or use mic to say \"find [object]\"';

  @override
  String get stopDetection => 'Stop Detection';

  @override
  String get startDetection => 'Start Detection';

  @override
  String get connecting => 'Connecting...';

  @override
  String get notConnected => 'Not Connected';
}
