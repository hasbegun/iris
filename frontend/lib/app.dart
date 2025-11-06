import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:iris/l10n/app_localizations.dart';

import 'core/theme/app_theme.dart';
import 'features/settings/providers/settings_provider.dart';
import 'features/home/presentation/home_screen_redesigned.dart';
import 'features/settings/presentation/settings_screen.dart';

class IrisApp extends ConsumerWidget {
  const IrisApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeMode = ref.watch(themeModeProvider);
    final locale = ref.watch(localeProvider);

    return MaterialApp(
      title: 'Iris',
      debugShowCheckedModeBanner: false,

      // Theme
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: themeMode,

      // Localization
      locale: locale,
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: const [
        Locale('en'),
        Locale('ko'),
        Locale('ja'),
        Locale('es'),
      ],

      // Routing
      initialRoute: '/',
      routes: {
        '/': (context) => const HomeScreenRedesigned(),
        '/settings': (context) => const SettingsScreen(),
      },
    );
  }
}
