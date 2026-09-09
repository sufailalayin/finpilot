import '../../core/api_client.dart';

class ReceivableService {
  ReceivableService(this._api);

  final ApiClient _api;

  Future<Map<String, dynamic>> overview() async {
    final response = await _api.dio.get('/receivables/overview');
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<Map<String, dynamic>> detail(String id) async {
    final response = await _api.dio.get('/receivables/$id');
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<void> create({
    required String personName,
    String? phone,
    required double originalAmount,
    required DateTime givenOn,
    DateTime? dueOn,
    String? note,
    String sourceType = 'outside',
    String? sourceAccountId,
  }) async {
    await _api.dio.post(
      '/receivables',
      data: {
        'person_name': personName.trim(),
        'phone': phone?.trim().isEmpty == true ? null : phone?.trim(),
        'original_amount': originalAmount,
        'given_on': givenOn.toIso8601String().split('T').first,
        'due_on': dueOn?.toIso8601String().split('T').first,
        'note': note?.trim().isEmpty == true ? null : note?.trim(),
        'source_type': sourceType,
        'source_account_id': sourceAccountId,
      },
    );
    _api.notifyDataChanged();
  }

  Future<void> recordRepayment({
    required String receivableId,
    required double amount,
    required DateTime receivedOn,
    String? note,
    String destinationType = 'outside',
    String? destinationAccountId,
  }) async {
    await _api.dio.post(
      '/receivables/$receivableId/repayments',
      data: {
        'amount': amount,
        'received_on': receivedOn.toIso8601String().split('T').first,
        'note': note?.trim().isEmpty == true ? null : note?.trim(),
        'destination_type': destinationType,
        'destination_account_id': destinationAccountId,
      },
    );
    _api.notifyDataChanged();
  }

  Future<void> delete(String id) async {
    await _api.dio.delete('/receivables/$id');
    _api.notifyDataChanged();
  }

  Future<List<Map<String, dynamic>>> accounts() async {
    final response = await _api.dio.get('/finance/accounts/balances');
    final rows = (response.data as List<dynamic>?) ?? const [];
    return rows.map((row) => Map<String, dynamic>.from(row as Map)).toList();
  }

  Future<void> move({
    required String sourceType,
    required String destinationType,
    String? sourceAccountId,
    String? destinationAccountId,
    String? sourceReceivableId,
    String? destinationReceivableId,
    required double amount,
    required DateTime occurredOn,
    String? note,
  }) async {
    await _api.dio.post(
      '/receivables/movements',
      data: {
        'source_type': sourceType,
        'destination_type': destinationType,
        'source_account_id': sourceAccountId,
        'destination_account_id': destinationAccountId,
        'source_receivable_id': sourceReceivableId,
        'destination_receivable_id': destinationReceivableId,
        'amount': amount,
        'occurred_on': occurredOn.toIso8601String().split('T').first,
        'note': note?.trim().isEmpty == true ? null : note?.trim(),
      },
    );
    _api.notifyDataChanged();
  }
}
