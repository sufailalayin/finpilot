import '../../core/api_client.dart';

class SubscriptionService {
  SubscriptionService(this._api);

  final ApiClient _api;

  Future<Map<String, dynamic>> features() async {
    final response = await _api.dio.get('/subscriptions/features');
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<Map<String, dynamic>> status() async {
    final response = await _api.dio.get('/subscriptions/status');
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<List<Map<String, dynamic>>> plans() async {
    final response = await _api.dio.get('/subscriptions/plans');
    final body = Map<String, dynamic>.from(response.data as Map);
    final rows = (body['plans'] as List<dynamic>?) ?? const [];
    return rows
        .map((row) => Map<String, dynamic>.from(row as Map))
        .toList();
  }

  Future<Map<String, dynamic>> verifyGooglePlay({
    required String billingPlanId,
    required String productId,
    required String purchaseToken,
  }) async {
    final response = await _api.dio.post(
      '/subscriptions/google-play/verify',
      data: {
        'billing_plan_id': billingPlanId,
        'product_id': productId,
        'purchase_token': purchaseToken,
      },
    );
    return Map<String, dynamic>.from(response.data as Map);
  }
}
