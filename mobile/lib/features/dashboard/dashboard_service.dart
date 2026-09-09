import '../../core/api_client.dart';

class DashboardData {
  DashboardData({
    required this.totalBalance,
    required this.monthIncome,
    required this.monthExpense,
    required this.monthNet,
    required this.transactionCount,
    required this.accounts,
    required this.recentTransactions,
    required this.netWorth,
    required this.investmentAssets,
    required this.liabilities,
    required this.savingsRate,
    required this.healthScore,
    required this.healthScoreAvailable,
    required this.healthGrade,
    required this.activeBudgetCount,
    required this.budgetWarningCount,
    required this.upcomingAlertCount,
    required this.insights,
    required this.alerts,
    required this.upcomingBills,
    required this.goals,
    required this.emergencyFund,
  });

  final double totalBalance;
  final double monthIncome;
  final double monthExpense;
  final double monthNet;
  final int transactionCount;
  final List<dynamic> accounts;
  final List<dynamic> recentTransactions;
  final double netWorth;
  final double investmentAssets;
  final double liabilities;
  final double savingsRate;
  final int healthScore;
  final bool healthScoreAvailable;
  final String healthGrade;
  final int activeBudgetCount;
  final int budgetWarningCount;
  final int upcomingAlertCount;
  final List<dynamic> insights;
  final List<dynamic> alerts;
  final List<dynamic> upcomingBills;
  final List<dynamic> goals;
  final Map<String, dynamic> emergencyFund;

  factory DashboardData.fromJson(Map<String, dynamic> json) {
    final summary = json['summary'] is Map
        ? Map<String, dynamic>.from(json['summary'] as Map)
        : <String, dynamic>{};

    double money(dynamic value) =>
        double.tryParse(value?.toString() ?? '0') ?? 0;

    int integer(dynamic value) =>
        int.tryParse(value?.toString() ?? '0') ?? 0;

    return DashboardData(
      totalBalance: money(summary['total_balance']),
      monthIncome: money(summary['month_income']),
      monthExpense: money(summary['month_expense']),
      monthNet: money(summary['month_net']),
      transactionCount: integer(summary['transaction_count']),
      accounts: (json['accounts'] as List<dynamic>?) ?? const [],
      recentTransactions:
          (json['recent_transactions'] as List<dynamic>?) ?? const [],
      netWorth: money(
        json['net_worth'] ?? summary['total_balance'],
      ),
      investmentAssets: money(json['investment_assets']),
      liabilities: money(json['liabilities']),
      savingsRate: double.tryParse(json['savings_rate'].toString()) ?? 0,
      healthScore: int.tryParse(json['financial_health_score'].toString()) ?? 0,
      healthScoreAvailable: json['health_score_available'] == true,
      healthGrade: json['health_grade']?.toString() ?? 'Not rated',
      activeBudgetCount:
          int.tryParse(json['active_budget_count'].toString()) ?? 0,
      budgetWarningCount:
          int.tryParse(json['budget_warning_count'].toString()) ?? 0,
      upcomingAlertCount:
          int.tryParse(json['upcoming_alert_count'].toString()) ?? 0,
      insights: (json['insights'] as List<dynamic>?) ?? const [],
      alerts: (json['alerts'] as List<dynamic>?) ?? const [],
      upcomingBills: (json['upcoming_bills'] as List<dynamic>?) ?? const [],
      goals: (json['goals'] as List<dynamic>?) ?? const [],
      emergencyFund: json['emergency_fund'] is Map
          ? Map<String, dynamic>.from(json['emergency_fund'] as Map)
          : <String, dynamic>{},
    );
  }
}

class DashboardService {
  DashboardService(this._api);

  final ApiClient _api;

  Future<DashboardData> load() async {
    final response = await _api.dio.get('/dashboard');
    return DashboardData.fromJson(response.data as Map<String, dynamic>);
  }
}
