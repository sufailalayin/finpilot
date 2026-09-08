import 'package:flutter/material.dart';

import 'app_security_service.dart';

class AppLockScreen extends StatefulWidget {
  const AppLockScreen({
    super.key,
    required this.onUnlocked,
  });

  final VoidCallback onUnlocked;

  @override
  State<AppLockScreen> createState() => _AppLockScreenState();
}

class _AppLockScreenState extends State<AppLockScreen> {
  final _security = AppSecurityService();
  final _pin = TextEditingController();
  bool _checkingBiometric = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _tryBiometric();
  }

  Future<void> _tryBiometric() async {
    if (_checkingBiometric) return;
    setState(() => _checkingBiometric = true);
    final ok = await _security.authenticateBiometric();
    if (!mounted) return;
    if (ok) {
      widget.onUnlocked();
      return;
    }
    setState(() => _checkingBiometric = false);
  }

  Future<void> _unlockWithPin() async {
    final value = _pin.text.trim();
    if (value.length < 4) {
      setState(() => _error = 'Enter your app PIN.');
      return;
    }
    final ok = await _security.verifyPin(value);
    if (!mounted) return;
    if (ok) {
      widget.onUnlocked();
    } else {
      setState(() => _error = 'Incorrect PIN.');
    }
  }

  @override
  void dispose() {
    _pin.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(28),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Column(
                children: [
                  CircleAvatar(
                    radius: 38,
                    backgroundColor:
                        Theme.of(context).colorScheme.primaryContainer,
                    child: const Icon(Icons.lock_outline, size: 38),
                  ),
                  const SizedBox(height: 20),
                  Text(
                    'FinPilot is locked',
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                          fontWeight: FontWeight.w900,
                        ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Unlock to access your financial data.',
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 28),
                  TextField(
                    controller: _pin,
                    obscureText: true,
                    keyboardType: TextInputType.number,
                    maxLength: 8,
                    textInputAction: TextInputAction.done,
                    onSubmitted: (_) => _unlockWithPin(),
                    decoration: const InputDecoration(
                      labelText: 'App PIN',
                      prefixIcon: Icon(Icons.pin_outlined),
                    ),
                  ),
                  if (_error != null) ...[
                    const SizedBox(height: 8),
                    Text(
                      _error!,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                      ),
                    ),
                  ],
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton(
                      onPressed: _unlockWithPin,
                      child: const Text('Unlock'),
                    ),
                  ),
                  const SizedBox(height: 10),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      onPressed: _checkingBiometric ? null : _tryBiometric,
                      icon: const Icon(Icons.fingerprint),
                      label: Text(
                        _checkingBiometric
                            ? 'Checking biometrics...'
                            : 'Use biometrics',
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
