import '../../core/api_client.dart';

class AnalyticsService {
  AnalyticsService(this._api);

  final ApiClient _api;

  Future<Map<String, dynamic>> report({int months = 6}) async {
    final response = await _api.dio.get(
      '/analytics/report',
      queryParameters: {'months': months},
    );
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<Map<String, dynamic>> overview() async {
    final response = await _api.dio.get('/analytics/overview');
    return Map<String, dynamic>.from(response.data as Map);
  }
}
