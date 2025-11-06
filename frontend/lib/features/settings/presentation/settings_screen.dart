import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:iris/l10n/app_localizations.dart';
import '../providers/settings_provider.dart';
import '../../../core/constants/app_constants.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final settings = ref.watch(settingsProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.settings),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // General Settings
          _buildSectionHeader(context, l10n.generalSettings),
          _buildThemeTile(context, ref, l10n, settings.themeMode),
          _buildLanguageTile(context, ref, l10n, settings.locale),
          const Divider(height: 32),

          // Developer Settings
          _buildSectionHeader(context, l10n.developerSettings),
          _buildDevModeTile(context, ref, l10n, settings.devMode),
          if (settings.devMode) ...[
            _buildBackendUrlTile(context, ref, l10n, settings.backendUrl),
            _buildVisionModelTile(context, ref, l10n, settings.visionModel),
            _buildChatModelTile(context, ref, l10n, settings.chatModel),
          ],
          const Divider(height: 32),

          // Speech Settings
          _buildSectionHeader(context, l10n.speechSettings),
          _buildTtsRateTile(context, ref, l10n, settings.ttsRate),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(BuildContext context, String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8, top: 8),
      child: Text(
        title,
        style: Theme.of(context).textTheme.titleMedium?.copyWith(
              color: Theme.of(context).colorScheme.primary,
              fontWeight: FontWeight.bold,
            ),
      ),
    );
  }

  Widget _buildThemeTile(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations l10n,
    ThemeMode currentMode,
  ) {
    return ListTile(
      leading: const Icon(Icons.palette),
      title: Text(l10n.theme),
      subtitle: Text(_getThemeModeLabel(l10n, currentMode)),
      onTap: () => _showThemeDialog(context, ref, l10n, currentMode),
    );
  }

  Widget _buildLanguageTile(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations l10n,
    Locale currentLocale,
  ) {
    return ListTile(
      leading: const Icon(Icons.language),
      title: Text(l10n.language),
      subtitle: Text(_getLanguageLabel(l10n, currentLocale)),
      onTap: () => _showLanguageDialog(context, ref, l10n, currentLocale),
    );
  }

  Widget _buildDevModeTile(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations l10n,
    bool devMode,
  ) {
    return SwitchListTile(
      secondary: const Icon(Icons.developer_mode),
      title: Text(l10n.devMode),
      value: devMode,
      onChanged: (value) {
        ref.read(settingsProvider.notifier).toggleDevMode(value);
      },
    );
  }

  Widget _buildBackendUrlTile(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations l10n,
    String backendUrl,
  ) {
    return ListTile(
      leading: const Icon(Icons.api),
      title: Text(l10n.backendUrl),
      subtitle: Text(backendUrl),
      onTap: () => _showBackendUrlDialog(context, ref, l10n, backendUrl),
    );
  }

  Widget _buildVisionModelTile(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations l10n,
    String visionModel,
  ) {
    return ListTile(
      leading: const Icon(Icons.remove_red_eye),
      title: Text(l10n.visionModel),
      subtitle: Text(visionModel),
      onTap: () => _showModelDialog(
        context,
        ref,
        l10n,
        l10n.visionModel,
        visionModel,
        true,
      ),
    );
  }

  Widget _buildChatModelTile(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations l10n,
    String chatModel,
  ) {
    return ListTile(
      leading: const Icon(Icons.chat),
      title: Text(l10n.chatModel),
      subtitle: Text(chatModel),
      onTap: () => _showModelDialog(
        context,
        ref,
        l10n,
        l10n.chatModel,
        chatModel,
        false,
      ),
    );
  }

  Widget _buildTtsRateTile(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations l10n,
    double ttsRate,
  ) {
    return ListTile(
      leading: const Icon(Icons.speed),
      title: Text(l10n.ttsRate),
      subtitle: Slider(
        value: ttsRate,
        min: 0.1,
        max: 1.0,
        divisions: 9,
        label: ttsRate.toStringAsFixed(1),
        onChanged: (value) {
          ref.read(settingsProvider.notifier).updateTtsRate(value);
        },
      ),
    );
  }

  String _getThemeModeLabel(AppLocalizations l10n, ThemeMode mode) {
    switch (mode) {
      case ThemeMode.light:
        return l10n.light;
      case ThemeMode.dark:
        return l10n.dark;
      case ThemeMode.system:
        return l10n.system;
    }
  }

  String _getLanguageLabel(AppLocalizations l10n, Locale locale) {
    switch (locale.languageCode) {
      case 'en':
        return l10n.english;
      case 'ko':
        return l10n.korean;
      case 'ja':
        return l10n.japanese;
      case 'es':
        return l10n.spanish;
      default:
        return l10n.english;
    }
  }

  void _showThemeDialog(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations l10n,
    ThemeMode currentMode,
  ) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(l10n.theme),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            RadioListTile<ThemeMode>(
              title: Text(l10n.light),
              value: ThemeMode.light,
              groupValue: currentMode,
              onChanged: (value) {
                if (value != null) {
                  ref.read(settingsProvider.notifier).updateThemeMode(value);
                  Navigator.pop(context);
                }
              },
            ),
            RadioListTile<ThemeMode>(
              title: Text(l10n.dark),
              value: ThemeMode.dark,
              groupValue: currentMode,
              onChanged: (value) {
                if (value != null) {
                  ref.read(settingsProvider.notifier).updateThemeMode(value);
                  Navigator.pop(context);
                }
              },
            ),
            RadioListTile<ThemeMode>(
              title: Text(l10n.system),
              value: ThemeMode.system,
              groupValue: currentMode,
              onChanged: (value) {
                if (value != null) {
                  ref.read(settingsProvider.notifier).updateThemeMode(value);
                  Navigator.pop(context);
                }
              },
            ),
          ],
        ),
      ),
    );
  }

  void _showLanguageDialog(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations l10n,
    Locale currentLocale,
  ) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(l10n.language),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: AppConstants.supportedLocaleCodes
              .map(
                (code) => RadioListTile<String>(
                  title: Text(_getLanguageNameForCode(l10n, code)),
                  value: code,
                  groupValue: currentLocale.languageCode,
                  onChanged: (value) {
                    if (value != null) {
                      ref.read(settingsProvider.notifier).updateLocale(Locale(value));
                      Navigator.pop(context);
                    }
                  },
                ),
              )
              .toList(),
        ),
      ),
    );
  }

  String _getLanguageNameForCode(AppLocalizations l10n, String code) {
    switch (code) {
      case 'en':
        return l10n.english;
      case 'ko':
        return l10n.korean;
      case 'ja':
        return l10n.japanese;
      case 'es':
        return l10n.spanish;
      default:
        return code;
    }
  }

  void _showBackendUrlDialog(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations l10n,
    String currentUrl,
  ) {
    final controller = TextEditingController(text: currentUrl);

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(l10n.backendUrl),
        content: TextField(
          controller: controller,
          decoration: InputDecoration(
            hintText: 'http://localhost:9000',
            helperText: 'Enter the backend server URL',
          ),
          keyboardType: TextInputType.url,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text(l10n.cancel),
          ),
          TextButton(
            onPressed: () {
              final url = controller.text.trim();
              if (url.isNotEmpty) {
                ref.read(settingsProvider.notifier).updateBackendUrl(url);
                Navigator.pop(context);
              }
            },
            child: Text(l10n.save),
          ),
        ],
      ),
    );
  }

  void _showModelDialog(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations l10n,
    String title,
    String currentModel,
    bool isVision,
  ) {
    final controller = TextEditingController(text: currentModel);

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: TextField(
          controller: controller,
          decoration: InputDecoration(
            hintText: isVision ? 'llava:latest' : 'gemma3:latest',
            helperText: 'Enter the model name',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text(l10n.cancel),
          ),
          TextButton(
            onPressed: () {
              final model = controller.text.trim();
              if (model.isNotEmpty) {
                if (isVision) {
                  ref.read(settingsProvider.notifier).updateVisionModel(model);
                } else {
                  ref.read(settingsProvider.notifier).updateChatModel(model);
                }
                Navigator.pop(context);
              }
            },
            child: Text(l10n.save),
          ),
        ],
      ),
    );
  }
}
