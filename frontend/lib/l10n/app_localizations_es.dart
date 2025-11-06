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
}
