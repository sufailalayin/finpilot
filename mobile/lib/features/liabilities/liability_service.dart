import '../../core/api_client.dart';

class LiabilityService {
  LiabilityService(this._api);

  final ApiClient _api;

  Future<Map<String, dynamic>> overview() async {
    final response = await _api.dio.get('/liabilities/overview/summary');
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<void> createLiability({
    required String name,
    required String liabilityType,
    String? lender,
    required double originalPrincipal,
    required double outstandingPrincipal,
    required double interestRate,
    required double emiAmount,
    DateTime? nextDueOn,
    String? fundingAccountId,
  }) async {
    await _api.dio.post(
      '/liabilities',
      data: {
        'name': name.trim(),
        'liability_type': liabilityType,
        'lender': lender?.trim().isEmpty == true ? null : lender?.trim(),
        'original_principal': originalPrincipal,
        'outstanding_principal': outstandingPrincipal,
        'interest_rate': interestRate,
        'emi_amount': emiAmount,
        'next_due_on':
            nextDueOn?.toIso8601String().split('T').first,
        'funding_account_id': fundingAccountId,
      },
    );
    _api.notifyDataChanged();
  }

  Future<void> updateLiability({
    required String liabilityId,
    required String name,
    required String liabilityType,
    String? lender,
    required double outstandingPrincipal,
    required double interestRate,
    required double emiAmount,
    DateTime? nextDueOn,
  }) async {
    await _api.dio.patch(
      '/liabilities/$liabilityId',
      data: {
        'name': name.trim(),
        'liability_type': liabilityType,
        'lender': lender?.trim().isEmpty == true ? null : lender?.trim(),
        'outstanding_principal': outstandingPrincipal,
        'interest_rate': interestRate,
        'emi_amount': emiAmount,
        'next_due_on': nextDueOn?.toIso8601String().split('T').first,
      },
    );
    _api.notifyDataChanged();
  }

  Future<void> recordPayment({
    required String liabilityId,
    required double amount,
    required double principalComponent,
    required double interestComponent,
    required DateTime paidOn,
    String? paymentAccountId,
  }) async {
    await _api.dio.post(
      '/liabilities/$liabilityId/payments',
      data: {
        'amount': amount,
        'principal_component': principalComponent,
        'interest_component': interestComponent,
        'paid_on': paidOn.toIso8601String().split('T').first,
        'payment_account_id': paymentAccountId,
      },
    );
    _api.notifyDataChanged();
  }

  Future<List<Map<String, dynamic>>> accounts() async {
    final response = await _api.dio.get('/finance/accounts/balances');
    final rows = (response.data as List<dynamic>?) ?? const [];
    return rows
        .map((row) => Map<String, dynamic>.from(row as Map))
        .where((row) =>
            row['account_type']?.toString() == 'cash' ||
            row['account_type']?.toString() == 'bank')
        .toList();
  }

  Future<void> deleteLiability(String liabilityId) async {
    await _api.dio.delete('/liabilities/$liabilityId');
    _api.notifyDataChanged();
  }
}
