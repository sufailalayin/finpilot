import 'dart:convert';

import 'package:crypto/crypto.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:local_auth/local_auth.dart';

class AppSecurityService {
  AppSecurityService()
      : _storage = const FlutterSecureStorage(),
        _auth = LocalAuthentication();

  static const _pinHashKey = 'finpilot_app_pin_hash';
  static const _lockEnabledKey = 'finpilot_app_lock_enabled';
  static const _biometricEnabledKey = 'finpilot_biometric_enabled';

  final FlutterSecureStorage _storage;
  final LocalAuthentication _auth;

  String _hashPin(String pin) =>
      sha256.convert(utf8.encode('finpilot-pin:' + pin)).toString();

  Future<bool> isLockEnabled() async =>
      (await _storage.read(key: _lockEnabledKey)) == 'true';

  Future<bool> isBiometricEnabled() async =>
      (await _storage.read(key: _biometricEnabledKey)) == 'true';

  Future<void> setPin(String pin) async {
    await _storage.write(key: _pinHashKey, value: _hashPin(pin));
    await _storage.write(key: _lockEnabledKey, value: 'true');
  }

  Future<bool> verifyPin(String pin) async {
    final stored = await _storage.read(key: _pinHashKey);
    if (stored == null) return false;
    return stored == _hashPin(pin);
  }

  Future<void> disableLock() async {
    await _storage.delete(key: _pinHashKey);
    await _storage.write(key: _lockEnabledKey, value: 'false');
    await _storage.write(key: _biometricEnabledKey, value: 'false');
  }

  Future<bool> biometricAvailable() async {
    try {
      return await _auth.isDeviceSupported() && await _auth.canCheckBiometrics;
    } catch (_) {
      return false;
    }
  }

  Future<void> setBiometricEnabled(bool enabled) async {
    if (enabled && !await biometricAvailable()) {
      throw StateError('Biometric authentication is not available.');
    }
    await _storage.write(
      key: _biometricEnabledKey,
      value: enabled ? 'true' : 'false',
    );
  }

  Future<bool> authenticateBiometric() async {
    if (!await isBiometricEnabled()) return false;
    try {
      return await _auth.authenticate(
        localizedReason: 'Unlock your FinPilot financial data',
        options: const AuthenticationOptions(
          biometricOnly: true,
          stickyAuth: true,
        ),
      );
    } catch (_) {
      return false;
    }
  }
}
