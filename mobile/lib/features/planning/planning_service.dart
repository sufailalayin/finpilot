import '../../core/api_client.dart';

class PlanningService {
  PlanningService(this._api);

  final ApiClient _api;

  Future<List<dynamic>> listBudgets() async {
    final response = await _api.dio.get('/planning/budgets');
    return response.data as List<dynamic>;
  }

  Future<List<dynamic>> listGoals() async {
    final response = await _api.dio.get('/planning/goals');
    return response.data as List<dynamic>;
  }

  Future<void> createGoal({
    required String name,
    required double targetAmount,
    required double currentAmount,
    DateTime? targetDate,
  }) async {
    await _api.dio.post(
      '/planning/goals',
      data: {
        'name': name.trim(),
        'target_amount': targetAmount,
        'current_amount': currentAmount,
        'target_date': targetDate?.toIso8601String().split('T').first,
      },
    );
  }

  Future<void> createBudget({
    required String name,
    required double amount,
    required DateTime periodStart,
    required DateTime periodEnd,
    String? categoryId,
  }) async {
    await _api.dio.post(
      '/planning/budgets',
      data: {
        'name': name.trim(),
        'amount': amount,
        'period_start': periodStart.toIso8601String().split('T').first,
        'period_end': periodEnd.toIso8601String().split('T').first,
        'category_id': categoryId,
      },
    );
  }
}
