// Basic Flutter widget test for Iris app

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:iris/app.dart';
import 'package:iris/shared/providers/service_providers.dart';

void main() {
  testWidgets('App launches and shows home screen', (WidgetTester tester) async {
    // Initialize SharedPreferences for testing
    SharedPreferences.setMockInitialValues({});
    final prefs = await SharedPreferences.getInstance();

    // Build our app and trigger a frame
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          sharedPreferencesProvider.overrideWithValue(prefs),
        ],
        child: const IrisApp(),
      ),
    );

    // Wait for async operations to complete
    await tester.pumpAndSettle();

    // Verify that the app title is displayed
    expect(find.text('Iris'), findsWidgets);

    // Verify that settings button exists
    expect(find.byIcon(Icons.settings), findsOneWidget);
  });
}
