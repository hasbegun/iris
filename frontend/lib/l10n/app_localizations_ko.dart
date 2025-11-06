// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Korean (`ko`).
class AppLocalizationsKo extends AppLocalizations {
  AppLocalizationsKo([String locale = 'ko']) : super(locale);

  @override
  String get appTitle => 'Iris';

  @override
  String get home => '홈';

  @override
  String get settings => '설정';

  @override
  String get selectImage => '이미지 선택';

  @override
  String get selectVideo => '비디오 선택';

  @override
  String get enterPrompt => '질문을 입력하세요...';

  @override
  String get promptHint => 'Ask a question about the image...';

  @override
  String get send => '전송';

  @override
  String get speak => '말하기';

  @override
  String get listening => '듣는 중...';

  @override
  String get starting => 'Starting...';

  @override
  String get stopRecording => 'Stop Recording';

  @override
  String get startRecording => 'Start Recording';

  @override
  String get processing => '처리 중...';

  @override
  String get readAloud => '소리내어 읽기';

  @override
  String get backendUrl => '백엔드 URL';

  @override
  String get visionModel => '비전 모델';

  @override
  String get chatModel => '채팅 모델';

  @override
  String get devMode => '개발자 모드';

  @override
  String get theme => '테마';

  @override
  String get language => '언어';

  @override
  String get light => '밝게';

  @override
  String get dark => '어둡게';

  @override
  String get system => '시스템';

  @override
  String get english => 'English';

  @override
  String get korean => '한국어';

  @override
  String get japanese => '日本語';

  @override
  String get spanish => 'Español';

  @override
  String get save => '저장';

  @override
  String get cancel => '취소';

  @override
  String get error => '오류';

  @override
  String get connectionError => '서버에 연결할 수 없습니다. 설정을 확인하세요.';

  @override
  String get invalidUrl => '잘못된 URL 형식';

  @override
  String get noMediaSelected => '선택된 미디어 없음';

  @override
  String get generalSettings => '일반';

  @override
  String get developerSettings => '개발자';

  @override
  String get speechSettings => '음성';

  @override
  String get ttsVoice => 'TTS 음성';

  @override
  String get ttsRate => '말하기 속도';

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
