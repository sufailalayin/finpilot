import 'package:flutter/material.dart';

import 'core/api_client.dart';
import 'features/auth/auth_screen.dart';
import 'features/auth/auth_service.dart';
import 'features/navigation/app_shell.dart';
import 'features/security/app_lock_screen.dart';
import 'features/security/app_security_service.dart';
import 'features/security/security_setup_gate.dart';
import 'features/update/app_update_gate.dart';

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
  bool _securityReady = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _refreshLockState();
  }

  Future<void> _refreshLockState() async {
    final enabled = await _security.isLockEnabled();
    if (!mounted) return;
    setState(() {
      _lockEnabled = enabled;
      _securityReady = true;
    });
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
        colorSchemeSeed: const Color(0xFF124D40),
        scaffoldBackgroundColor: const Color(0xFFF6F8F7),
        appBarTheme: const AppBarTheme(
          centerTitle: false,
          elevation: 0,
          backgroundColor: Colors.transparent,
          surfaceTintColor: Colors.transparent,
          titleTextStyle: TextStyle(
            color: Color(0xFF102A24),
            fontSize: 20,
            fontWeight: FontWeight.w800,
          ),
        ),
        cardTheme: CardThemeData(
          elevation: 0,
          margin: EdgeInsets.zero,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: const BorderSide(color: Color(0xFFE5EBE8), width: 1),
          ),
          color: Colors.white,
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            elevation: 0,
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            textStyle: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
        outlinedButtonTheme: OutlinedButtonThemeData(
          style: OutlinedButton.styleFrom(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            side: const BorderSide(color: Color(0xFF124D40), width: 1.2),
            textStyle: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: Color(0xFFD2DCD7)),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: Color(0xFFD2DCD7)),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: Color(0xFF124D40), width: 1.8),
          ),
          filled: true,
          fillColor: Colors.white,
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        ),
        navigationBarTheme: NavigationBarThemeData(
          height: 68,
          backgroundColor: Colors.white,
          elevation: 2,
          indicatorColor: const Color(0xFFD1ECE5),
          labelTextStyle: WidgetStateProperty.resolveWith((states) {
            if (states.contains(WidgetState.selected)) {
              return const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w800,
                color: Color(0xFF124D40),
              );
            }
            return const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w500,
              color: Color(0xFF6B7280),
            );
          }),
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
            if (!_securityReady) {
              return const Scaffold(
                body: Center(child: CircularProgressIndicator()),
              );
            }
            if (_lockEnabled && !_unlocked) {
              return AppLockScreen(
                onUnlocked: () => setState(() => _unlocked = true),
              );
            }
            return AppUpdateGate(
              api: _api,
              child: SecuritySetupGate(
                api: _api,
                child: AppShell(api: _api),
              ),
            );
          }

          return AppUpdateGate(
            api: _api,
            child: AuthScreen(api: _api),
          );
        },
      ),
    );
  }
}
