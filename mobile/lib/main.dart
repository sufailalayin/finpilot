import 'package:flutter/material.dart';

import 'core/api_client.dart';
import 'features/auth/auth_screen.dart';
import 'features/auth/auth_service.dart';
import 'features/navigation/app_shell.dart';
import 'features/security/app_lock_screen.dart';
import 'features/security/app_security_service.dart';

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
  late final AppSecurityService _security = AppSecurityService();
  bool _unlocked = false;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FinPilot',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: const Color(0xFF185A4A),
        scaffoldBackgroundColor: const Color(0xFFF7F9F8),
        appBarTheme: const AppBarTheme(
          centerTitle: false,
          elevation: 0,
        ),
        cardTheme: const CardThemeData(
          elevation: 0,
          margin: EdgeInsets.zero,
        ),
        inputDecorationTheme: const InputDecorationTheme(
          border: OutlineInputBorder(),
          filled: true,
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
            return FutureBuilder<bool>(
              future: _security.isLockEnabled(),
              builder: (context, lockSnapshot) {
                if (lockSnapshot.connectionState != ConnectionState.done) {
                  return const Scaffold(
                    body: Center(child: CircularProgressIndicator()),
                  );
                }
                final lockEnabled = lockSnapshot.data == true;
                if (lockEnabled && !_unlocked) {
                  return AppLockScreen(
                    onUnlocked: () => setState(() => _unlocked = true),
                  );
                }
                return AppShell(api: _api);
              },
            );
          }

          return AuthScreen(api: _api);
        },
      ),
    );
  }
}
