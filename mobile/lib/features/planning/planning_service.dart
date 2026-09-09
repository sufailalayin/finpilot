import '../../core/api_client.dart';

class PlanningService {
  PlanningService(this._api);

  final ApiClient _api;

  Future<Map<String, dynamic>> budgetDashboard() async {
    final response = await _api.dio.get('/planning/budgets/dashboard');
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<List<dynamic>> listBudgets() async {
    final response = await _api.dio.get('/planning/budgets');
    return response.data as List<dynamic>;
  }

  Future<Map<String, dynamic>> goalDashboard() async {
    final response = await _api.dio.get('/planning/goals/dashboard');
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<List<dynamic>> listGoals() async {
    final response = await _api.dio.get('/planning/goals');
    return response.data as List<dynamic>;
  }

  Future<void> updateGoal({
    required String goalId,
    required String name,
    required String goalType,
    required double targetAmount,
    required double currentAmount,
    DateTime? targetDate,
  }) async {
    await _api.dio.patch(
      '/planning/goals/$goalId',
      data: {
        'name': name.trim(),
        'goal_type': goalType,
        'target_amount': targetAmount,
        'current_amount': currentAmount,
        'target_date': targetDate?.toIso8601String().split('T').first,
      },
    );
    _api.notifyDataChanged();
  }

  Future<void> deleteGoal(String goalId) async {
    await _api.dio.delete('/planning/goals/$goalId');
    _api.notifyDataChanged();
  }

  Future<void> createGoal({
    required String name,
    required double targetAmount,
    required double currentAmount,
    String goalType = 'other',
    DateTime? targetDate,
  }) async {
    await _api.dio.post(
      '/planning/goals',
      data: {
        'name': name.trim(),
        'goal_type': goalType,
        'target_amount': targetAmount,
        'current_amount': currentAmount,
        'target_date': targetDate?.toIso8601String().split('T').first,
      },
    );
    _api.notifyDataChanged();
  }

  Future<void> updateBudget({
    required String budgetId,
    required String name,
    required double amount,
    required DateTime periodStart,
    required DateTime periodEnd,
    String? categoryId,
    bool rolloverEnabled = false,
    double alertThresholdPct = 80,
  }) async {
    await _api.dio.patch(
      '/planning/budgets/$budgetId',
      data: {
        'name': name.trim(),
        'amount': amount,
        'period_start': periodStart.toIso8601String().split('T').first,
        'period_end': periodEnd.toIso8601String().split('T').first,
        'category_id': categoryId,
        'rollover_enabled': rolloverEnabled,
        'alert_threshold_pct': alertThresholdPct,
      },
    );
    _api.notifyDataChanged();
  }

  Future<void> deleteBudget(String budgetId) async {
    await _api.dio.delete('/planning/budgets/$budgetId');
    _api.notifyDataChanged();
  }

  Future<void> createBudget({
    required String name,
    required double amount,
    required DateTime periodStart,
    required DateTime periodEnd,
    String? categoryId,
    bool rolloverEnabled = false,
    double alertThresholdPct = 80,
  }) async {
    await _api.dio.post(
      '/planning/budgets',
      data: {
        'name': name.trim(),
        'amount': amount,
        'period_start': periodStart.toIso8601String().split('T').first,
        'period_end': periodEnd.toIso8601String().split('T').first,
        'category_id': categoryId,
        'rollover_enabled': rolloverEnabled,
        'alert_threshold_pct': alertThresholdPct,
      },
    );
    _api.notifyDataChanged();
  }
}
