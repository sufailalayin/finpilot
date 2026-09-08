import '../../core/api_client.dart';

class FinanceService {
  FinanceService(this._api);

  final ApiClient _api;

  Future<List<dynamic>> listAccounts() async {
    final response = await _api.dio.get('/finance/accounts');
    return (response.data as List<dynamic>);
  }

  Future<List<dynamic>> listCategories() async {
    final response = await _api.dio.get('/finance/categories');
    return (response.data as List<dynamic>);
  }

  Future<void> createAccount({
    required String name,
    required String accountType,
    required double openingBalance,
  }) async {
    await _api.dio.post(
      '/finance/accounts',
      data: {
        'name': name.trim(),
        'account_type': accountType,
        'currency': 'INR',
        'opening_balance': openingBalance,
      },
    );
  }

  Future<void> createTransaction({
    required String accountId,
    required String? categoryId,
    required String transactionType,
    required double amount,
    required DateTime occurredOn,
    String? merchant,
    String? note,
  }) async {
    await _api.dio.post(
      '/finance/transactions',
      data: {
        'account_id': accountId,
        'category_id': categoryId,
        'transaction_type': transactionType,
        'amount': amount,
        'occurred_on': occurredOn.toIso8601String().split('T').first,
        'merchant': merchant?.trim().isEmpty == true ? null : merchant?.trim(),
        'note': note?.trim().isEmpty == true ? null : note?.trim(),
      },
    );
  }
}
