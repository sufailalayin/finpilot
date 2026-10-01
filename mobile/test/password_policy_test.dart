import 'package:flutter_test/flutter_test.dart';
import 'package:finpilot/features/auth/password_policy.dart';

void main() {
  group('password policy', () {
    test('new passwords require at least 10 characters', () {
      expect(newPasswordLooksValid('12345678'), isFalse);
      expect(newPasswordLooksValid('123456789'), isFalse);
      expect(newPasswordLooksValid('1234567890'), isTrue);
    });

    test('login accepts any non-empty password for server validation', () {
      expect(loginPasswordLooksValid(''), isFalse);
      expect(loginPasswordLooksValid('12345678'), isTrue);
      expect(loginPasswordLooksValid('legacy9xx'), isTrue);
    });
  });
}
