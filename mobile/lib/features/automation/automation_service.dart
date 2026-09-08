import '../../core/api_client.dart';

class AutomationService {
  AutomationService(this._api);

  final ApiClient _api;

  Future<Map<String, dynamic>> overview() async {
    final response = await _api.dio.get('/automation/overview');
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<void> addBill({
    required String name,
    required double amount,
    required DateTime dueOn,
    String frequency = 'once',
  }) async {
    await _api.dio.post(
      '/automation/bills',
      data: {
        'name': name.trim(),
        'amount': amount,
        'due_on': dueOn.toIso8601String().split('T').first,
        'frequency': frequency,
      },
    );
  }

  Future<void> markBillPaid(String billId) async {
    await _api.dio.post('/automation/bills/$billId/paid');
  }

  Future<void> addRecurring({
    required String accountId,
    String? categoryId,
    required String name,
    required String transactionType,
    required double amount,
    required String frequency,
    required DateTime nextDueOn,
  }) async {
    await _api.dio.post(
      '/automation/recurring',
      data: {
        'account_id': accountId,
        'category_id': categoryId,
        'name': name.trim(),
        'transaction_type': transactionType,
        'amount': amount,
        'frequency': frequency,
        'day_of_month': frequency == 'monthly' ? nextDueOn.day : null,
        'next_due_on': nextDueOn.toIso8601String().split('T').first,
      },
    );
  }
}
