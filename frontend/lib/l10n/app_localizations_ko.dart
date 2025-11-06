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
}
