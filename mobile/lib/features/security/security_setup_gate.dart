import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import 'app_security_service.dart';

class SecuritySetupGate extends StatefulWidget {
  const SecuritySetupGate({
    super.key,
    required this.api,
    required this.child,
  });

  final ApiClient api;
  final Widget child;

  @override
  State<SecuritySetupGate> createState() => _SecuritySetupGateState();
}

class _SecuritySetupGateState extends State<SecuritySetupGate> {
  final _security = AppSecurityService();
  final _pin = TextEditingController();
  final _confirm = TextEditingController();

  bool _loading = true;
  bool _needsSetup = false;
  bool _biometricAvailable = false;
  bool _enableBiometric = false;
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _prepare();
  }

  Future<void> _prepare() async {
    final lockEnabled = await _security.isLockEnabled();
    final prompted = await _security.wasSecuritySetupPrompted();
    final biometric = await _security.biometricAvailable();

    if (lockEnabled && !prompted) {
      await _security.markSecuritySetupPrompted();
    }

    if (!mounted) return;
    setState(() {
      _biometricAvailable = biometric;
      _needsSetup = !lockEnabled && !prompted;
      _loading = false;
    });
  }

  Future<void> _save() async {
    if (_saving) return;
    final pin = _pin.text.trim();
    final confirm = _confirm.text.trim();

    if (!RegExp(r'^\d{4,8}$').hasMatch(pin)) {
      setState(() => _error = 'Choose a 4–8 digit PIN.');
      return;
    }
    if (pin != confirm) {
      setState(() => _error = 'PIN confirmation does not match.');
      return;
    }

    setState(() {
      _saving = true;
      _error = null;
    });

    try {
      await _security.setPin(pin);
      if (_enableBiometric && _biometricAvailable) {
        await _security.setBiometricEnabled(true);
      }
      if (!mounted) return;
      setState(() {
        _needsSetup = false;
        _saving = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _saving = false;
        _error = 'Unable to configure app security on this device.';
      });
    }
  }

  Future<void> _skip() async {
    await _security.markSecuritySetupPrompted();
    if (!mounted) return;
    setState(() => _needsSetup = false);
  }

  @override
  void dispose() {
    _pin.dispose();
    _confirm.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (!_needsSetup) return widget.child;

    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 460),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  CircleAvatar(
                    radius: 36,
                    backgroundColor: scheme.primaryContainer,
                    child: Icon(
                      Icons.shield_outlined,
                      size: 36,
                      color: scheme.onPrimaryContainer,
                    ),
                  ),
                  const SizedBox(height: 20),
                  Text(
                    'Secure FinPilot on this device',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                          fontWeight: FontWeight.w900,
                        ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'You will stay signed in securely. Add an app PIN so your financial data stays protected when someone else has your phone.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: scheme.onSurfaceVariant),
                  ),
                  const SizedBox(height: 26),
                  TextField(
                    controller: _pin,
                    obscureText: true,
                    keyboardType: TextInputType.number,
                    maxLength: 8,
                    decoration: const InputDecoration(
                      labelText: 'Create app PIN',
                      helperText: '4–8 digits',
                      prefixIcon: Icon(Icons.pin_outlined),
                    ),
                  ),
                  const SizedBox(height: 10),
                  TextField(
                    controller: _confirm,
                    obscureText: true,
                    keyboardType: TextInputType.number,
                    maxLength: 8,
                    decoration: const InputDecoration(
                      labelText: 'Confirm app PIN',
                      prefixIcon: Icon(Icons.lock_outline),
                    ),
                  ),
                  if (_biometricAvailable) ...[
                    const SizedBox(height: 8),
                    SwitchListTile(
                      contentPadding: EdgeInsets.zero,
                      secondary: const Icon(Icons.fingerprint),
                      title: const Text('Use fingerprint / biometrics'),
                      subtitle: const Text(
                        'Your PIN remains available as a backup unlock method.',
                      ),
                      value: _enableBiometric,
                      onChanged: _saving
                          ? null
                          : (value) =>
                              setState(() => _enableBiometric = value),
                    ),
                  ],
                  if (_error != null) ...[
                    const SizedBox(height: 10),
                    Text(
                      _error!,
                      textAlign: TextAlign.center,
                      style: TextStyle(color: scheme.error),
                    ),
                  ],
                  const SizedBox(height: 18),
                  SizedBox(
                    height: 52,
                    child: FilledButton.icon(
                      onPressed: _saving ? null : _save,
                      icon: const Icon(Icons.verified_user_outlined),
                      label: Text(
                        _saving ? 'Securing...' : 'Enable app protection',
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  TextButton(
                    onPressed: _saving ? null : _skip,
                    child: const Text('Not now'),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'You can change this later in Profile → Security & Privacy.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 12,
                      color: scheme.onSurfaceVariant,
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
