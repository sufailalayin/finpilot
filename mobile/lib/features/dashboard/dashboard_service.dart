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
  });

  final double totalBalance;
  final double monthIncome;
  final double monthExpense;
  final double monthNet;
  final int transactionCount;
  final List<dynamic> accounts;
  final List<dynamic> recentTransactions;

  factory DashboardData.fromJson(Map<String, dynamic> json) {
    final summary = json['summary'] as Map<String, dynamic>;
    double money(dynamic value) => double.parse(value.toString());

    return DashboardData(
      totalBalance: money(summary['total_balance']),
      monthIncome: money(summary['month_income']),
      monthExpense: money(summary['month_expense']),
      monthNet: money(summary['month_net']),
      transactionCount: summary['transaction_count'] as int,
      accounts: (json['accounts'] as List<dynamic>?) ?? const [],
      recentTransactions:
          (json['recent_transactions'] as List<dynamic>?) ?? const [],
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
