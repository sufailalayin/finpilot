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

class _FinPilotAppState extends State<FinPilotApp> with WidgetsBindingObserver {
  late final ApiClient _api = ApiClient();
  late final Future<bool> _session = AuthService(_api).hasSession();
  late final AppSecurityService _security = AppSecurityService();
  bool _unlocked = false;
  bool _lockEnabled = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _refreshLockState();
  }

  Future<void> _refreshLockState() async {
    final enabled = await _security.isLockEnabled();
    if (!mounted) return;
    setState(() => _lockEnabled = enabled);
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.paused ||
        state == AppLifecycleState.hidden ||
        state == AppLifecycleState.detached) {
      if (_lockEnabled && _unlocked) {
        setState(() => _unlocked = false);
      }
    } else if (state == AppLifecycleState.resumed) {
      _refreshLockState();
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

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
            if (_lockEnabled && !_unlocked) {
              return AppLockScreen(
                onUnlocked: () => setState(() => _unlocked = true),
              );
            }
            return AppShell(api: _api);
          }

          return AuthScreen(api: _api);
        },
      ),
    );
  }
}
