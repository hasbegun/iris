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
}
