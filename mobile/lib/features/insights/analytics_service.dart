import '../../core/api_client.dart';

class AnalyticsService {
  AnalyticsService(this._api);

  final ApiClient _api;

  Future<Map<String, dynamic>> overview() async {
    final response = await _api.dio.get('/analytics/overview');
    return Map<String, dynamic>.from(response.data as Map);
  }
}
