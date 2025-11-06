// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'Iris';

  @override
  String get home => 'Home';

  @override
  String get settings => 'Settings';

  @override
  String get selectImage => 'Select Image';

  @override
  String get selectVideo => 'Select Video';

  @override
  String get enterPrompt => 'Ask a question about the media...';

  @override
  String get promptHint => 'Ask a question about the image...';

  @override
  String get send => 'Send';

  @override
  String get speak => 'Speak';

  @override
  String get listening => 'Listening...';

  @override
  String get starting => 'Starting...';

  @override
  String get stopRecording => 'Stop Recording';

  @override
  String get startRecording => 'Start Recording';

  @override
  String get processing => 'Processing...';

  @override
  String get readAloud => 'Read Aloud';

  @override
  String get backendUrl => 'Backend URL';

  @override
  String get visionModel => 'Vision Model';

  @override
  String get chatModel => 'Chat Model';

  @override
  String get devMode => 'Developer Mode';

  @override
  String get theme => 'Theme';

  @override
  String get language => 'Language';

  @override
  String get light => 'Light';

  @override
  String get dark => 'Dark';

  @override
  String get system => 'System';

  @override
  String get english => 'English';

  @override
  String get korean => 'Korean';

  @override
  String get japanese => 'Japanese';

  @override
  String get spanish => 'Spanish';

  @override
  String get save => 'Save';

  @override
  String get cancel => 'Cancel';

  @override
  String get error => 'Error';

  @override
  String get connectionError =>
      'Could not connect to server. Please check your settings.';

  @override
  String get invalidUrl => 'Invalid URL format';

  @override
  String get noMediaSelected => 'No media selected';

  @override
  String get generalSettings => 'General';

  @override
  String get developerSettings => 'Developer';

  @override
  String get speechSettings => 'Speech';

  @override
  String get ttsVoice => 'TTS Voice';

  @override
  String get ttsRate => 'Speech Rate';

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
}
