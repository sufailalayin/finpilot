import '../../core/api_client.dart';

class AutomationService {
  AutomationService(this._api);

  final ApiClient _api;

  Future<Map<String, dynamic>> alerts() async {
    final response = await _api.dio.get('/automation/alerts');
    _api.notifyDataChanged();
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<Map<String, dynamic>> overview() async {
    final response = await _api.dio.get('/automation/overview');
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<void> addBill({
    required String name,
    required double amount,
    required DateTime dueOn,
    String frequency = 'once',
    String billType = 'bill',
    String? provider,
    int reminderDaysBefore = 3,
    bool autoRenew = false,
  }) async {
    await _api.dio.post(
      '/automation/bills',
      data: {
        'name': name.trim(),
        'bill_type': billType,
        'provider': provider?.trim().isEmpty == true ? null : provider?.trim(),
        'amount': amount,
        'due_on': dueOn.toIso8601String().split('T').first,
        'frequency': frequency,
        'reminder_days_before': reminderDaysBefore,
        'auto_renew': autoRenew,
      },
    );
    _api.notifyDataChanged();
  }

  Future<void> markBillPaid(String billId) async {
    await _api.dio.post('/automation/bills/$billId/paid');
    _api.notifyDataChanged();
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
    _api.notifyDataChanged();
  }
}
