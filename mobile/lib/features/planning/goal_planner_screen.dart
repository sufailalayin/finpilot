import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/api_client.dart';
import '../../core/app_error_state.dart';
import 'planning_service.dart';

class GoalPlannerScreen extends StatefulWidget {
  const GoalPlannerScreen({super.key, required this.api});
  final ApiClient api;

  @override
  State<GoalPlannerScreen> createState() => _GoalPlannerScreenState();
}

class _GoalPlannerScreenState extends State<GoalPlannerScreen> {
  late final PlanningService _planning = PlanningService(widget.api);
  late Future<Map<String, dynamic>> _future;
  final _money = NumberFormat.currency(locale: 'en_IN', symbol: '₹', decimalDigits: 0);

  @override
  void initState() {
    super.initState();
    _future = _planning.goalDashboard();
  }

  Future<void> _refresh() async {
    setState(() => _future = _planning.goalDashboard());
    await _future;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Goal Planner', style: TextStyle(fontWeight: FontWeight.w800))),
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
            );
          }
          final data = snapshot.data!;
          final goals = (data['goals'] as List<dynamic>?) ?? const [];
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
                      const Text('GOAL POSITION', style: TextStyle(fontWeight: FontWeight.w800, letterSpacing: 1, fontSize: 12)),
                      const SizedBox(height: 10),
                      Text(_money.format(number(data['total_remaining'])), style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 30)),
                      const Text('Remaining across all goals'),
                      const SizedBox(height: 14),
                      Text('Saved ' + _money.format(number(data['total_saved'])) + ' of ' + _money.format(number(data['total_target']))),
                    ],
                  ),
                ),
                const SizedBox(height: 24),
                Text('Goal plans', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
                const SizedBox(height: 10),
                if (goals.isEmpty)
                  const Card(child: Padding(padding: EdgeInsets.all(18), child: Text('No savings goals yet.')))
                else
                  ...goals.map((raw) {
                    final goal = Map<String, dynamic>.from(raw as Map);
                    final progress = number(goal['progress_pct']);
                    final monthly = goal['required_monthly_contribution'] == null ? null : number(goal['required_monthly_contribution']);
                    final status = goal['status'].toString();
                    final statusLabel = switch (status) {
                      'completed' => 'Completed',
                      'overdue' => 'Overdue',
                      'needs_attention' => 'Needs attention',
                      _ => 'On track',
                    };
                    return Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(children: [
                              Expanded(child: Text(goal['name'].toString(), style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16))),
                              Text(statusLabel, style: const TextStyle(fontWeight: FontWeight.w700)),
                            ]),
                            const SizedBox(height: 4),
                            Text(goal['goal_type'].toString()),
                            const SizedBox(height: 12),
                            LinearProgressIndicator(value: (progress / 100).clamp(0.0, 1.0)),
                            const SizedBox(height: 8),
                            Text(progress.toStringAsFixed(1) + '% complete • ' + _money.format(number(goal['remaining_amount'])) + ' remaining'),
                            if (monthly != null) ...[
                              const SizedBox(height: 8),
                              Text('Required monthly contribution: ' + _money.format(monthly), style: const TextStyle(fontWeight: FontWeight.w700)),
                            ],
                            if (goal['months_remaining'] != null) ...[
                              const SizedBox(height: 5),
                              Text(goal['months_remaining'].toString() + ' month(s) remaining'),
                            ],
                            if (goal['target_date'] != null) ...[
                              const SizedBox(height: 5),
                              Text('Target date: ' + goal['target_date'].toString()),
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