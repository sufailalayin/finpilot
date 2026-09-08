import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/api_client.dart';
import 'analytics_service.dart';
import 'report_export_service.dart';

class ReportsScreen extends StatefulWidget {
  const ReportsScreen({super.key, required this.api});

  final ApiClient api;

  @override
  State<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends State<ReportsScreen> {
  late final AnalyticsService _analytics = AnalyticsService(widget.api);
  late Future<Map<String, dynamic>> _future;
  final _export = ReportExportService();

  final _money = NumberFormat.currency(
    locale: 'en_IN',
    symbol: '₹',
    decimalDigits: 0,
  );

  @override
  void initState() {
    super.initState();
    _future = _analytics.report(months: 6);
  }

  Future<void> _refresh() async {
    setState(() => _future = _analytics.report(months: 6));
    await _future;
  }

  Widget _changeCard(String label, dynamic value, IconData icon) {
    final change = value == null ? null : double.tryParse(value.toString());
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surface,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(
            color: Theme.of(context).colorScheme.outlineVariant,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, size: 20),
            const SizedBox(height: 10),
            Text(
              change == null
                  ? '—'
                  : (change >= 0 ? '+' : '') +
                      change.toStringAsFixed(1) +
                      '%',
              style: const TextStyle(
                fontWeight: FontWeight.w900,
                fontSize: 18,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                fontSize: 12,
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Reports',
          style: TextStyle(fontWeight: FontWeight.w800),
        ),
      ),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError || !snapshot.hasData) {
            return Center(
              child: FilledButton.icon(
                onPressed: _refresh,
                icon: const Icon(Icons.refresh),
                label: const Text('Retry reports'),
              ),
            );
          }

          final data = snapshot.data!;
          final current =
              Map<String, dynamic>.from(data['current_month'] as Map);
          final trend = (data['trend'] as List<dynamic>?) ?? const [];
          final categories =
              (data['category_breakdown'] as List<dynamic>?) ?? const [];

          final currentIncome =
              double.tryParse(current['income'].toString()) ?? 0;
          final currentExpenses =
              double.tryParse(current['expenses'].toString()) ?? 0;
          final currentNet = double.tryParse(current['net'].toString()) ?? 0;
          final currentWorth =
              double.tryParse(current['net_worth'].toString()) ?? 0;

          return RefreshIndicator(
            onRefresh: _refresh,
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
              children: [
                Container(
                  padding: const EdgeInsets.all(22),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.primaryContainer,
                    borderRadius: BorderRadius.circular(24),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'CURRENT MONTH',
                        style: TextStyle(
                          fontWeight: FontWeight.w800,
                          letterSpacing: 1,
                          fontSize: 12,
                        ),
                      ),
                      const SizedBox(height: 10),
                      Text(
                        _money.format(currentWorth),
                        style: const TextStyle(
                          fontWeight: FontWeight.w900,
                          fontSize: 30,
                        ),
                      ),
                      const SizedBox(height: 4),
                      const Text('Estimated net worth'),
                      const SizedBox(height: 18),
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              'Income\n' + _money.format(currentIncome),
                              style:
                                  const TextStyle(fontWeight: FontWeight.w700),
                            ),
                          ),
                          Expanded(
                            child: Text(
                              'Expenses\n' + _money.format(currentExpenses),
                              style:
                                  const TextStyle(fontWeight: FontWeight.w700),
                            ),
                          ),
                          Expanded(
                            child: Text(
                              'Net\n' + _money.format(currentNet),
                              style:
                                  const TextStyle(fontWeight: FontWeight.w700),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 14),
                Row(
                  children: [
                    Expanded(
                      child: FilledButton.tonalIcon(
                        onPressed: () => _export.shareJson(data),
                        icon: const Icon(Icons.download_outlined),
                        label: const Text('Export report JSON'),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () => _export.shareTrendCsv(data),
                        icon: const Icon(Icons.table_view_outlined),
                        label: const Text('Export trend CSV'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 18),
                Row(
                  children: [
                    _changeCard(
                      'Income vs last month',
                      data['income_change_pct'],
                      Icons.south_west_rounded,
                    ),
                    const SizedBox(width: 10),
                    _changeCard(
                      'Expense vs last month',
                      data['expense_change_pct'],
                      Icons.north_east_rounded,
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    _changeCard(
                      'Net vs last month',
                      data['net_change_pct'],
                      Icons.trending_up,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: Theme.of(context).colorScheme.surface,
                          borderRadius: BorderRadius.circular(18),
                          border: Border.all(
                            color:
                                Theme.of(context).colorScheme.outlineVariant,
                          ),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Icon(Icons.savings_outlined, size: 20),
                            const SizedBox(height: 10),
                            Text(
                              (double.tryParse(
                                            current['savings_rate'].toString(),
                                          ) ??
                                          0)
                                      .toStringAsFixed(1) +
                                  '%',
                              style: const TextStyle(
                                fontWeight: FontWeight.w900,
                                fontSize: 18,
                              ),
                            ),
                            const SizedBox(height: 4),
                            const Text(
                              'Savings rate',
                              style: TextStyle(fontSize: 12),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 26),
                Text(
                  '6-month trend',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
                const SizedBox(height: 10),
                ...trend.map((item) {
                  final m = Map<String, dynamic>.from(item as Map);
                  final income = double.tryParse(m['income'].toString()) ?? 0;
                  final expense =
                      double.tryParse(m['expenses'].toString()) ?? 0;
                  final netWorth =
                      double.tryParse(m['net_worth'].toString()) ?? 0;
                  final savings =
                      double.tryParse(m['savings_rate'].toString()) ?? 0;

                  return Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            m['month'].toString(),
                            style: const TextStyle(
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                          const SizedBox(height: 12),
                          Row(
                            children: [
                              Expanded(
                                child: Text('Income\n' + _money.format(income)),
                              ),
                              Expanded(
                                child:
                                    Text('Expense\n' + _money.format(expense)),
                              ),
                              Expanded(
                                child: Text(
                                  'Savings\n' +
                                      savings.toStringAsFixed(1) +
                                      '%',
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 10),
                          Text(
                            'Net worth: ' + _money.format(netWorth),
                            style: const TextStyle(
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                }),
                const SizedBox(height: 24),
                Text(
                  'Category breakdown',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
                const SizedBox(height: 10),
                if (categories.isEmpty)
                  const Card(
                    child: Padding(
                      padding: EdgeInsets.all(18),
                      child: Text('No expense data for this month.'),
                    ),
                  )
                else
                  ...categories.map((item) {
                    final row = Map<String, dynamic>.from(item as Map);
                    final amount =
                        double.tryParse(row['amount'].toString()) ?? 0;
                    final pct =
                        double.tryParse(row['percentage'].toString()) ?? 0;
                    return Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Expanded(
                                  child: Text(
                                    row['category'].toString(),
                                    style: const TextStyle(
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                ),
                                Text(_money.format(amount)),
                              ],
                            ),
                            const SizedBox(height: 10),
                            LinearProgressIndicator(
                              value: (pct / 100).clamp(0.0, 1.0),
                            ),
                            const SizedBox(height: 6),
                            Text(pct.toStringAsFixed(1) + '% of expenses'),
                          ],
                        ),
                      ),
                    );
                  }),
              ],
            ),
          );
        },
      ),
    );
  }
}
