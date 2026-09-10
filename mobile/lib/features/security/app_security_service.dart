import 'dart:convert';
import 'dart:math';

import 'package:crypto/crypto.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:local_auth/local_auth.dart';

class AppSecurityService {
  AppSecurityService()
      : _storage = const FlutterSecureStorage(),
        _auth = LocalAuthentication();

  static const _pinHashKey = 'finpilot_app_pin_hash_v2';
  static const _pinSaltKey = 'finpilot_app_pin_salt_v2';
  static const _lockEnabledKey = 'finpilot_app_lock_enabled';
  static const _biometricEnabledKey = 'finpilot_biometric_enabled';
  static const _setupPromptedKey = 'finpilot_security_setup_prompted';
  static const _pinFailuresKey = 'finpilot_pin_failures';
  static const _pinLockedUntilKey = 'finpilot_pin_locked_until';
  static const _legacyPinHashKey = 'finpilot_app_pin_hash';

  static const int _iterations = 120000;
  static const int _maxPinAttempts = 5;
  static const int _pinLockSeconds = 30;

  final FlutterSecureStorage _storage;
  final LocalAuthentication _auth;

  String _randomSalt() {
    final random = Random.secure();
    final bytes = List<int>.generate(24, (_) => random.nextInt(256));
    return base64UrlEncode(bytes);
  }

  String _derivePinHash(String pin, String salt) {
    var block = utf8.encode('$salt|finpilot-pin|$pin');
    var digest = sha256.convert(block).bytes;
    for (var i = 1; i < _iterations; i++) {
      digest = sha256.convert([...digest, ...block]).bytes;
    }
    return base64UrlEncode(digest);
  }

  Future<bool> isLockEnabled() async =>
      (await _storage.read(key: _lockEnabledKey)) == 'true';

  Future<bool> isBiometricEnabled() async =>
      (await _storage.read(key: _biometricEnabledKey)) == 'true';

  Future<bool> wasSecuritySetupPrompted() async =>
      (await _storage.read(key: _setupPromptedKey)) == 'true';

  Future<void> markSecuritySetupPrompted() =>
      _storage.write(key: _setupPromptedKey, value: 'true');

  Future<void> resetSecuritySetupPrompt() =>
      _storage.delete(key: _setupPromptedKey);

  Future<void> setPin(String pin) async {
    if (!RegExp(r'^\d{4,8}$').hasMatch(pin)) {
      throw ArgumentError('PIN must contain 4 to 8 digits.');
    }
    final salt = _randomSalt();
    final hash = _derivePinHash(pin, salt);
    await _storage.write(key: _pinSaltKey, value: salt);
    await _storage.write(key: _pinHashKey, value: hash);
    await _storage.delete(key: _legacyPinHashKey);
    await _storage.write(key: _lockEnabledKey, value: 'true');
    await _storage.write(key: _pinFailuresKey, value: '0');
    await _storage.delete(key: _pinLockedUntilKey);
    await markSecuritySetupPrompted();
  }

  Future<int> pinLockSecondsRemaining() async {
    final raw = await _storage.read(key: _pinLockedUntilKey);
    final until = int.tryParse(raw ?? '');
    if (until == null) return 0;
    final now = DateTime.now().millisecondsSinceEpoch;
    if (until <= now) {
      await _storage.delete(key: _pinLockedUntilKey);
      await _storage.write(key: _pinFailuresKey, value: '0');
      return 0;
    }
    return ((until - now) / 1000).ceil();
  }

  Future<bool> verifyPin(String pin) async {
    if (await pinLockSecondsRemaining() > 0) return false;

    final stored = await _storage.read(key: _pinHashKey);
    final salt = await _storage.read(key: _pinSaltKey);
    bool ok = false;

    if (stored != null && salt != null) {
      ok = stored == _derivePinHash(pin, salt);
    } else {
      final legacy = await _storage.read(key: _legacyPinHashKey);
      if (legacy != null) {
        final legacyHash =
            sha256.convert(utf8.encode('finpilot-pin:' + pin)).toString();
        ok = legacy == legacyHash;
        if (ok) await setPin(pin);
      }
    }

    if (ok) {
      await _storage.write(key: _pinFailuresKey, value: '0');
      await _storage.delete(key: _pinLockedUntilKey);
      return true;
    }

    final failures =
        (int.tryParse(await _storage.read(key: _pinFailuresKey) ?? '0') ?? 0) +
            1;
    if (failures >= _maxPinAttempts) {
      final until = DateTime.now()
          .add(const Duration(seconds: _pinLockSeconds))
          .millisecondsSinceEpoch;
      await _storage.write(key: _pinFailuresKey, value: '0');
      await _storage.write(key: _pinLockedUntilKey, value: until.toString());
    } else {
      await _storage.write(key: _pinFailuresKey, value: failures.toString());
    }
    return false;
  }

  Future<void> disableLock() async {
    await _storage.delete(key: _pinHashKey);
    await _storage.delete(key: _pinSaltKey);
    await _storage.delete(key: _legacyPinHashKey);
    await _storage.write(key: _lockEnabledKey, value: 'false');
    await _storage.write(key: _biometricEnabledKey, value: 'false');
    await _storage.delete(key: _pinFailuresKey);
    await _storage.delete(key: _pinLockedUntilKey);
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
    if (enabled && !await isLockEnabled()) {
      throw StateError('Set an app PIN before enabling biometrics.');
    }
    await _storage.write(
      key: _biometricEnabledKey,
      value: enabled ? 'true' : 'false',
    );
    if (enabled) await markSecuritySetupPrompted();
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
