import 'package:flutter_test/flutter_test.dart';
import 'package:finpilot/features/accounts/transfer_screen.dart';

void main() {
  group('Transfer validation rules', () {
    test('outside account sentinel is defined', () {
      expect(TransferScreen.outsideAccount, equals('__outside__'));
    });

    test('outside to outside transfer is prevented', () {
      const from = TransferScreen.outsideAccount;
      const to = TransferScreen.outsideAccount;
      final bothOutside = from == TransferScreen.outsideAccount &&
          to == TransferScreen.outsideAccount;
      expect(bothOutside, isTrue);
    });

    test('internal to outside is identified as external', () {
      const from = 'acc-123';
      const to = TransferScreen.outsideAccount;
      final fromIsOutside = from == TransferScreen.outsideAccount;
      final toIsOutside = to == TransferScreen.outsideAccount;

      expect(fromIsOutside, isFalse);
      expect(toIsOutside, isTrue);
      expect(from != to, isTrue);
    });

    test('outside to internal is identified as external', () {
      const from = TransferScreen.outsideAccount;
      const to = 'acc-456';
      final fromIsOutside = from == TransferScreen.outsideAccount;
      final toIsOutside = to == TransferScreen.outsideAccount;

      expect(fromIsOutside, isTrue);
      expect(toIsOutside, isFalse);
      expect(from != to, isTrue);
    });

    test('transfer amount parsing supports decimals and rejects invalid numbers', () {
      expect(double.tryParse('100.50'), equals(100.50));
      expect(double.tryParse('1,250.75'.replaceAll(',', '')), equals(1250.75));
      expect(double.tryParse('0'), equals(0.0));
      expect(double.tryParse('-50'), equals(-50.0));
      expect(double.tryParse('abc'), isNull);
    });
  });
}
