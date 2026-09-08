import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/api_client.dart';
import 'planning_service.dart';

class BudgetDashboardScreen extends StatefulWidget {
  const BudgetDashboardScreen({super.key, required this.api});
  final ApiClient api;

  @override
  State<BudgetDashboardScreen> createState() => _BudgetDashboardScreenState();
}

class _BudgetDashboardScreenState extends State<BudgetDashboardScreen> {
  late final PlanningService _planning = PlanningService(widget.api);
  late Future<Map<String, dynamic>> _future;
  final _money = NumberFormat.currency(locale: 'en_IN', symbol: '₹', decimalDigits: 0);

  @override
  void initState() {
    super.initState();
    _future = _planning.budgetDashboard();
  }

  Future<void> _refresh() async {
    setState(() => _future = _planning.budgetDashboard());
    await _future;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Budget Control', style: TextStyle(fontWeight: FontWeight.w800))),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError || !snapshot.hasData) {
            return Center(child: FilledButton.icon(onPressed: _refresh, icon: const Icon(Icons.refresh), label: const Text('Retry')));
          }
          final data = snapshot.data!;
          final rows = (data['budgets'] as List<dynamic>?) ?? const [];
          double number(dynamic value) => double.tryParse(value?.toString() ?? '0') ?? 0;

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
                      const Text('MONTHLY BUDGET POSITION', style: TextStyle(fontWeight: FontWeight.w800, letterSpacing: 1, fontSize: 12)),
                      const SizedBox(height: 10),
                      Text(_money.format(number(data['total_remaining'])), style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 30)),
                      const Text('Remaining across active budgets'),
                      const SizedBox(height: 16),
                      Row(
                        children: [
                          Expanded(child: Text('Budget\n' + _money.format(number(data['total_budget'])), style: const TextStyle(fontWeight: FontWeight.w700))),
                          Expanded(child: Text('Spent\n' + _money.format(number(data['total_spent'])), style: const TextStyle(fontWeight: FontWeight.w700))),
                          Expanded(child: Text('Forecast\n' + _money.format(number(data['projected_total_spend'])), style: const TextStyle(fontWeight: FontWeight.w700))),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),
                Text('Live budget performance', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
                const SizedBox(height: 10),
                if (rows.isEmpty)
                  const Card(child: Padding(padding: EdgeInsets.all(18), child: Text('No active budgets for today. Create a budget from Planning.')))
                else
                  ...rows.map((raw) {
                    final row = Map<String, dynamic>.from(raw as Map);
                    final usage = number(row['usage_pct']);
                    final projectedOverrun = number(row['projected_overrun']);
                    final status = row['status'].toString();
                    final label = switch (status) {
                      'over' => 'Over budget',
                      'warning' => 'Limit warning',
                      'forecast_over' => 'Forecast to exceed',
                      _ => 'On track',
                    };

                    return Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(children: [
                              Expanded(child: Text(row['name'].toString(), style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16))),
                              Text(label, style: const TextStyle(fontWeight: FontWeight.w700)),
                            ]),
                            const SizedBox(height: 12),
                            LinearProgressIndicator(value: (usage / 100).clamp(0.0, 1.0)),
                            const SizedBox(height: 8),
                            Text(usage.toStringAsFixed(1) + '% used • ' + _money.format(number(row['remaining'])) + ' remaining'),
                            const SizedBox(height: 8),
                            Text('Projected: ' + _money.format(number(row['projected_spend']))),
                            if (projectedOverrun > 0)
                              Text('Projected overrun: ' + _money.format(projectedOverrun), style: TextStyle(color: Theme.of(context).colorScheme.error, fontWeight: FontWeight.w700)),
                            if (row['rollover_enabled'] == true) ...[
                              const SizedBox(height: 6),
                              const Text('Rollover enabled'),
                            ],
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