// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Japanese (`ja`).
class AppLocalizationsJa extends AppLocalizations {
  AppLocalizationsJa([String locale = 'ja']) : super(locale);

  @override
  String get appTitle => 'Iris';

  @override
  String get home => 'ホーム';

  @override
  String get settings => '設定';

  @override
  String get selectImage => '画像を選択';

  @override
  String get selectVideo => 'ビデオを選択';

  @override
  String get enterPrompt => '質問を入力してください...';

  @override
  String get promptHint => 'Ask a question about the image...';

  @override
  String get send => '送信';

  @override
  String get speak => '話す';

  @override
  String get listening => '聞いています...';

  @override
  String get starting => 'Starting...';

  @override
  String get stopRecording => 'Stop Recording';

  @override
  String get startRecording => 'Start Recording';

  @override
  String get processing => '処理中...';

  @override
  String get readAloud => '読み上げる';

  @override
  String get backendUrl => 'バックエンドURL';

  @override
  String get visionModel => 'ビジョンモデル';

  @override
  String get chatModel => 'チャットモデル';

  @override
  String get devMode => '開発者モード';

  @override
  String get theme => 'テーマ';

  @override
  String get language => '言語';

  @override
  String get light => 'ライト';

  @override
  String get dark => 'ダーク';

  @override
  String get system => 'システム';

  @override
  String get english => 'English';

  @override
  String get korean => '한국어';

  @override
  String get japanese => '日本語';

  @override
  String get spanish => 'Español';

  @override
  String get save => '保存';

  @override
  String get cancel => 'キャンセル';

  @override
  String get error => 'エラー';

  @override
  String get connectionError => 'サーバーに接続できません。設定を確認してください。';

  @override
  String get invalidUrl => '無効なURL形式';

  @override
  String get noMediaSelected => 'メディアが選択されていません';

  @override
  String get generalSettings => '一般';

  @override
  String get developerSettings => '開発者';

  @override
  String get speechSettings => '音声';

  @override
  String get ttsVoice => 'TTS音声';

  @override
  String get ttsRate => '話す速度';

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
