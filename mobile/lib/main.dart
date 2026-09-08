import 'package:flutter/material.dart';

import 'core/api_client.dart';
import 'features/auth/auth_screen.dart';
import 'features/auth/auth_service.dart';
import 'features/navigation/app_shell.dart';

void main() {
  runApp(const FinPilotApp());
}

class FinPilotApp extends StatefulWidget {
  const FinPilotApp({super.key});

  @override
  State<FinPilotApp> createState() => _FinPilotAppState();
}

class _FinPilotAppState extends State<FinPilotApp> {
  late final ApiClient _api = ApiClient();
  late final Future<bool> _session = AuthService(_api).hasSession();

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FinPilot',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: const Color(0xFF185A4A),
        inputDecorationTheme: const InputDecorationTheme(
          border: OutlineInputBorder(),
        ),
      ),
      home: FutureBuilder<bool>(
        future: _session,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Scaffold(
              body: Center(child: CircularProgressIndicator()),
            );
          }

          if (snapshot.data == true) {
            return AppShell(api: _api);
          }

          return AuthScreen(api: _api);
        },
      ),
    );
  }
}
