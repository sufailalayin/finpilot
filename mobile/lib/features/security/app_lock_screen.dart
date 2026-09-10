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
  bool _biometricEnabled = false;
  bool _unlockingPin = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _prepareUnlock();
  }

  Future<void> _prepareUnlock() async {
    final enabled = await _security.isBiometricEnabled();
    if (!mounted) return;
    setState(() => _biometricEnabled = enabled);

    if (!enabled) return;

    // Give Android/Flutter lifecycle a moment to fully resume before opening
    // the biometric prompt. This avoids intermittent cold-start failures.
    await Future<void>.delayed(const Duration(milliseconds: 450));
    if (!mounted) return;
    await _tryBiometric();
  }

  Future<void> _tryBiometric() async {
    if (_checkingBiometric || !_biometricEnabled) return;

    setState(() {
      _checkingBiometric = true;
      _error = null;
    });

    final ok = await _security.authenticateBiometric();
    if (!mounted) return;

    if (ok) {
      widget.onUnlocked();
      return;
    }

    setState(() {
      _checkingBiometric = false;
      _error = 'Biometric unlock was not completed. You can use your PIN.';
    });
  }

  Future<void> _unlockWithPin() async {
    if (_unlockingPin) return;

    final lockedFor = await _security.pinLockSecondsRemaining();
    if (!mounted) return;
    if (lockedFor > 0) {
      setState(
        () => _error =
            'Too many incorrect PIN attempts. Try again in ${lockedFor}s.',
      );
      return;
    }

    final value = _pin.text.trim();
    if (value.length < 4) {
      setState(() => _error = 'Enter your app PIN.');
      return;
    }

    setState(() {
      _unlockingPin = true;
      _error = null;
    });

    final ok = await _security.verifyPin(value);
    if (!mounted) return;

    if (ok) {
      widget.onUnlocked();
      return;
    }

    final afterFailureLock = await _security.pinLockSecondsRemaining();
    if (!mounted) return;
    setState(() {
      _unlockingPin = false;
      _error = afterFailureLock > 0
          ? 'Too many incorrect PIN attempts. Try again in ${afterFailureLock}s.'
          : 'Incorrect PIN.';
    });
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
                      onPressed: _unlockingPin ? null : _unlockWithPin,
                      child: Text(_unlockingPin ? 'Unlocking...' : 'Unlock'),
                    ),
                  ),
                  const SizedBox(height: 10),
                  if (_biometricEnabled)
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
