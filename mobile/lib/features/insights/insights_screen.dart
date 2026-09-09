import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/api_client.dart';
import '../../core/app_error_state.dart';
import 'analytics_service.dart';
import 'reports_screen.dart';

class InsightsScreen extends StatefulWidget {
  const InsightsScreen({super.key, required this.api});

  final ApiClient api;

  @override
  State<InsightsScreen> createState() => _InsightsScreenState();
}

class _InsightsScreenState extends State<InsightsScreen> {
  late final AnalyticsService _analytics = AnalyticsService(widget.api);
  late Future<Map<String, dynamic>> _future;

  final _money = NumberFormat.currency(
    locale: 'en_IN',
    symbol: '₹',
    decimalDigits: 0,
  );

  @override
  void initState() {
    super.initState();
    _future = _analytics.overview();
  }

  Future<void> _refresh() async {
    setState(() => _future = _analytics.overview());
    await _future;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Financial Insights',
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
            return AppErrorState(
              error: snapshot.error,
              onRetry: _refresh,
              title: 'Insights unavailable',
            );
          }

          final data = snapshot.data!;
          final score = data['financial_health_score'] as int? ?? 0;
          final savingsRate =
              double.tryParse(data['savings_rate'].toString()) ?? 0;
          final healthGrade = data['health_grade']?.toString() ?? 'Not rated';
          final healthComponents =
              (data['health_components'] as List<dynamic>?) ?? const [];
          final categories =
              (data['top_categories'] as List<dynamic>?) ?? const [];
          final budgets = (data['budgets'] as List<dynamic>?) ?? const [];
          final insights = (data['insights'] as List<dynamic>?) ?? const [];

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
                  child: Row(
                    children: [
                      SizedBox(
                        width: 84,
                        height: 84,
                        child: Stack(
                          fit: StackFit.expand,
                          children: [
                            CircularProgressIndicator(
                              value: score / 100,
                              strokeWidth: 9,
                            ),
                            Center(
                              child: Text(
                                score.toString(),
                                style: const TextStyle(
                                  fontSize: 24,
                                  fontWeight: FontWeight.w900,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 20),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Financial health score',
                              style: TextStyle(fontWeight: FontWeight.w800),
                            ),
                            const SizedBox(height: 6),
                            Text(
                              healthGrade,
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'Savings rate: ' +
                                  savingsRate.toStringAsFixed(1) +
                                  '%',
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                Text(
                  'Health breakdown',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
                const SizedBox(height: 10),
                ...healthComponents.map((raw) {
                  final item = Map<String, dynamic>.from(raw as Map);
                  final componentScore =
                      int.tryParse(item['score'].toString()) ?? 0;
                  final maxScore =
                      int.tryParse(item['max_score'].toString()) ?? 1;
                  final ratio = maxScore <= 0
                      ? 0.0
                      : (componentScore / maxScore).clamp(0.0, 1.0);
                  return Card(
                    child: Padding(
                      padding: const EdgeInsets.all(14),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  item['label'].toString(),
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w800,
                                  ),
                                ),
                              ),
                              Text(
                                componentScore.toString() +
                                    '/' +
                                    maxScore.toString(),
                                style: const TextStyle(
                                  fontWeight: FontWeight.w900,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 9),
                          LinearProgressIndicator(value: ratio),
                          const SizedBox(height: 7),
                          Text(item['message'].toString()),
                        ],
                      ),
                    ),
                  );
                }),
                const SizedBox(height: 16),
                FilledButton.tonalIcon(
                  onPressed: () => Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => ReportsScreen(api: widget.api),
                    ),
                  ),
                  icon: const Icon(Icons.bar_chart_outlined),
                  label: const Text('View full reports'),
                ),
                const SizedBox(height: 24),
                Text(
                  'Smart insights',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
                const SizedBox(height: 10),
                ...insights.map(
                  (item) => Card(
                    child: ListTile(
                      leading: Icon(
                        item['severity'] == 'good'
                            ? Icons.check_circle_outline
                            : item['severity'] == 'warning'
                                ? Icons.warning_amber_outlined
                                : Icons.lightbulb_outline,
                      ),
                      title: Text(
                        item['title'].toString(),
                        style: const TextStyle(fontWeight: FontWeight.w700),
                      ),
                      subtitle: Text(item['message'].toString()),
                    ),
                  ),
                ),
                const SizedBox(height: 22),
                Text(
                  'Top spending',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
                const SizedBox(height: 10),
                if (categories.isEmpty)
                  const Card(
                    child: Padding(
                      padding: EdgeInsets.all(18),
                      child: Text('Add expenses to see category analysis.'),
                    ),
                  )
                else
                  ...categories.map((item) {
                    final amount =
                        double.tryParse(item['amount'].toString()) ?? 0;
                    final percentage =
                        double.tryParse(item['percentage'].toString()) ?? 0;
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
                                    item['category'].toString(),
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
                              value: (percentage / 100).clamp(0.0, 1.0),
                            ),
                            const SizedBox(height: 6),
                            Text(
                              percentage.toStringAsFixed(1) + '% of expenses',
                            ),
                          ],
                        ),
                      ),
                    );
                  }),
                const SizedBox(height: 22),
                Text(
                  'Budget progress',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
                const SizedBox(height: 10),
                if (budgets.isEmpty)
                  const Card(
                    child: Padding(
                      padding: EdgeInsets.all(18),
                      child: Text('Create a budget to start progress tracking.'),
                    ),
                  )
                else
                  ...budgets.map((item) {
                    final pct =
                        double.tryParse(item['percentage'].toString()) ?? 0;
                    return Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              item['name'].toString(),
                              style: const TextStyle(
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                            const SizedBox(height: 10),
                            LinearProgressIndicator(
                              value: (pct / 100).clamp(0.0, 1.0),
                            ),
                            const SizedBox(height: 7),
                            Text(
                              _money.format(
                                    double.tryParse(item['spent'].toString()) ??
                                        0,
                                  ) +
                                  ' of ' +
                                  _money.format(
                                    double.tryParse(item['limit'].toString()) ??
                                        0,
                                  ),
                            ),
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
