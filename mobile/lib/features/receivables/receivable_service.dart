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
      },
    );
    _api.notifyDataChanged();
  }

  Future<void> recordRepayment({
    required String receivableId,
    required double amount,
    required DateTime receivedOn,
    String? note,
  }) async {
    await _api.dio.post(
      '/receivables/$receivableId/repayments',
      data: {
        'amount': amount,
        'received_on': receivedOn.toIso8601String().split('T').first,
        'note': note?.trim().isEmpty == true ? null : note?.trim(),
      },
    );
    _api.notifyDataChanged();
  }

  Future<void> delete(String id) async {
    await _api.dio.delete('/receivables/$id');
    _api.notifyDataChanged();
  }
}
