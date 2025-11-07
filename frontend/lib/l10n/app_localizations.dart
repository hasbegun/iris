import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_es.dart';
import 'app_localizations_ja.dart';
import 'app_localizations_ko.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations? of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations);
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('es'),
    Locale('ja'),
    Locale('ko'),
  ];

  /// Application title
  ///
  /// In en, this message translates to:
  /// **'Iris'**
  String get appTitle;

  /// Home screen title
  ///
  /// In en, this message translates to:
  /// **'Home'**
  String get home;

  /// Settings screen title
  ///
  /// In en, this message translates to:
  /// **'Settings'**
  String get settings;

  /// Button to select an image
  ///
  /// In en, this message translates to:
  /// **'Select Image'**
  String get selectImage;

  /// Button to select a video
  ///
  /// In en, this message translates to:
  /// **'Select Video'**
  String get selectVideo;

  /// Placeholder for prompt input
  ///
  /// In en, this message translates to:
  /// **'Ask a question about the media...'**
  String get enterPrompt;

  /// Hint text for prompt input field
  ///
  /// In en, this message translates to:
  /// **'Ask a question about the image...'**
  String get promptHint;

  /// Send button
  ///
  /// In en, this message translates to:
  /// **'Send'**
  String get send;

  /// Speak button for voice input
  ///
  /// In en, this message translates to:
  /// **'Speak'**
  String get speak;

  /// Status when recording voice
  ///
  /// In en, this message translates to:
  /// **'Listening...'**
  String get listening;

  /// Status when starting voice recognition
  ///
  /// In en, this message translates to:
  /// **'Starting...'**
  String get starting;

  /// Stop recording button
  ///
  /// In en, this message translates to:
  /// **'Stop Recording'**
  String get stopRecording;

  /// Start recording button
  ///
  /// In en, this message translates to:
  /// **'Start Recording'**
  String get startRecording;

  /// Processing status
  ///
  /// In en, this message translates to:
  /// **'Processing...'**
  String get processing;

  /// Button to read response aloud
  ///
  /// In en, this message translates to:
  /// **'Read Aloud'**
  String get readAloud;

  /// Backend server URL setting
  ///
  /// In en, this message translates to:
  /// **'Backend URL'**
  String get backendUrl;

  /// Vision model setting
  ///
  /// In en, this message translates to:
  /// **'Vision Model'**
  String get visionModel;

  /// Chat model setting
  ///
  /// In en, this message translates to:
  /// **'Chat Model'**
  String get chatModel;

  /// Developer mode setting
  ///
  /// In en, this message translates to:
  /// **'Developer Mode'**
  String get devMode;

  /// Theme setting
  ///
  /// In en, this message translates to:
  /// **'Theme'**
  String get theme;

  /// Language setting
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get language;

  /// Light theme
  ///
  /// In en, this message translates to:
  /// **'Light'**
  String get light;

  /// Dark theme
  ///
  /// In en, this message translates to:
  /// **'Dark'**
  String get dark;

  /// System theme
  ///
  /// In en, this message translates to:
  /// **'System'**
  String get system;

  /// English language
  ///
  /// In en, this message translates to:
  /// **'English'**
  String get english;

  /// Korean language
  ///
  /// In en, this message translates to:
  /// **'Korean'**
  String get korean;

  /// Japanese language
  ///
  /// In en, this message translates to:
  /// **'Japanese'**
  String get japanese;

  /// Spanish language
  ///
  /// In en, this message translates to:
  /// **'Spanish'**
  String get spanish;

  /// Save button
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get save;

  /// Cancel button
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancel;

  /// Error title
  ///
  /// In en, this message translates to:
  /// **'Error'**
  String get error;

  /// Connection error message
  ///
  /// In en, this message translates to:
  /// **'Could not connect to server. Please check your settings.'**
  String get connectionError;

  /// Invalid URL error
  ///
  /// In en, this message translates to:
  /// **'Invalid URL format'**
  String get invalidUrl;

  /// No media selected message
  ///
  /// In en, this message translates to:
  /// **'No media selected'**
  String get noMediaSelected;

  /// General settings section
  ///
  /// In en, this message translates to:
  /// **'General'**
  String get generalSettings;

  /// Developer settings section
  ///
  /// In en, this message translates to:
  /// **'Developer'**
  String get developerSettings;

  /// Speech settings section
  ///
  /// In en, this message translates to:
  /// **'Speech'**
  String get speechSettings;

  /// Text-to-speech voice setting
  ///
  /// In en, this message translates to:
  /// **'TTS Voice'**
  String get ttsVoice;

  /// Text-to-speech rate setting
  ///
  /// In en, this message translates to:
  /// **'Speech Rate'**
  String get ttsRate;

  /// Dismiss button
  ///
  /// In en, this message translates to:
  /// **'Dismiss'**
  String get dismiss;

  /// Select media section header
  ///
  /// In en, this message translates to:
  /// **'Select Media'**
  String get selectMedia;

  /// Take photo button
  ///
  /// In en, this message translates to:
  /// **'Take Photo'**
  String get takePhoto;

  /// Validation message for empty prompt
  ///
  /// In en, this message translates to:
  /// **'Please enter a question'**
  String get pleaseEnterQuestion;

  /// Loading media status message
  ///
  /// In en, this message translates to:
  /// **'Loading media...'**
  String get loadingMedia;

  /// Hint text for backend URL input
  ///
  /// In en, this message translates to:
  /// **'http://localhost:9000'**
  String get backendUrlHint;

  /// Helper text for backend URL input
  ///
  /// In en, this message translates to:
  /// **'Enter the backend server URL'**
  String get backendUrlHelper;

  /// Helper text for model name input
  ///
  /// In en, this message translates to:
  /// **'Enter the model name'**
  String get modelNameHint;

  /// Live camera screen title
  ///
  /// In en, this message translates to:
  /// **'Live Camera'**
  String get liveCamera;

  /// Message when microphone permission is needed
  ///
  /// In en, this message translates to:
  /// **'Microphone permission needed for voice commands'**
  String get microphonePermissionNeeded;

  /// Speech recognition error message
  ///
  /// In en, this message translates to:
  /// **'Speech error: {error}'**
  String speechError(String error);

  /// Status when finding an object
  ///
  /// In en, this message translates to:
  /// **'Finding: {object}'**
  String findingObject(String object);

  /// Message when detection is stopped
  ///
  /// In en, this message translates to:
  /// **'Detection stopped'**
  String get detectionStopped;

  /// Message for unimplemented pause feature
  ///
  /// In en, this message translates to:
  /// **'Pause not yet implemented'**
  String get pauseNotImplemented;

  /// Message for unimplemented resume feature
  ///
  /// In en, this message translates to:
  /// **'Resume not yet implemented'**
  String get resumeNotImplemented;

  /// Message for unrecognized voice command
  ///
  /// In en, this message translates to:
  /// **'Unknown command: {command}'**
  String unknownCommand(String command);

  /// Error when no cameras are found
  ///
  /// In en, this message translates to:
  /// **'No cameras available on this device'**
  String get noCamerasAvailable;

  /// Error when camera permission is denied
  ///
  /// In en, this message translates to:
  /// **'Camera permission denied. Please enable it in Settings > Iris > Camera.'**
  String get cameraPermissionDenied;

  /// General camera error message
  ///
  /// In en, this message translates to:
  /// **'Camera error: {error}'**
  String cameraError(String error);

  /// Camera initialization error
  ///
  /// In en, this message translates to:
  /// **'Failed to initialize camera: {error}'**
  String cameraInitializationFailed(String error);

  /// Camera stream error
  ///
  /// In en, this message translates to:
  /// **'Failed to start camera stream: {error}'**
  String cameraStreamFailed(String error);

  /// Detection mode label
  ///
  /// In en, this message translates to:
  /// **'Detection'**
  String get detection;

  /// Segmentation mode label
  ///
  /// In en, this message translates to:
  /// **'Segmentation'**
  String get segmentation;

  /// Tooltip for stop listening button
  ///
  /// In en, this message translates to:
  /// **'Stop listening'**
  String get stopListening;

  /// Tooltip for voice command button
  ///
  /// In en, this message translates to:
  /// **'Voice command'**
  String get voiceCommand;

  /// Button to open app settings
  ///
  /// In en, this message translates to:
  /// **'Open Settings'**
  String get openSettings;

  /// Retry button
  ///
  /// In en, this message translates to:
  /// **'Retry'**
  String get retry;

  /// Instructions for enabling camera permission
  ///
  /// In en, this message translates to:
  /// **'Enable Camera permission in Settings, then tap Retry'**
  String get retryInstructions;

  /// Status when initializing camera
  ///
  /// In en, this message translates to:
  /// **'Initializing camera...'**
  String get initializingCamera;

  /// Status when detecting objects
  ///
  /// In en, this message translates to:
  /// **'Detecting...'**
  String get detecting;

  /// Status when detecting specific object
  ///
  /// In en, this message translates to:
  /// **'Detecting: {object}'**
  String detectingObject(String object);

  /// Status when segmenting
  ///
  /// In en, this message translates to:
  /// **'Segmenting...'**
  String get segmenting;

  /// Status when segmenting specific object
  ///
  /// In en, this message translates to:
  /// **'Segmenting: {object}'**
  String segmentingObject(String object);

  /// Count of detected objects
  ///
  /// In en, this message translates to:
  /// **'{count} object(s) found'**
  String objectsFound(int count);

  /// Count of segments found
  ///
  /// In en, this message translates to:
  /// **'{count} segment(s) found'**
  String segmentsFound(int count);

  /// Instructions for using live camera
  ///
  /// In en, this message translates to:
  /// **'Tap button below or use mic to say \"find [object]\"'**
  String get liveCameraInstructions;

  /// Button to stop detection
  ///
  /// In en, this message translates to:
  /// **'Stop Detection'**
  String get stopDetection;

  /// Button to start detection
  ///
  /// In en, this message translates to:
  /// **'Start Detection'**
  String get startDetection;

  /// Status when connecting to backend
  ///
  /// In en, this message translates to:
  /// **'Connecting...'**
  String get connecting;

  /// Status when backend is not connected
  ///
  /// In en, this message translates to:
  /// **'Not Connected'**
  String get notConnected;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'es', 'ja', 'ko'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'es':
      return AppLocalizationsEs();
    case 'ja':
      return AppLocalizationsJa();
    case 'ko':
      return AppLocalizationsKo();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
