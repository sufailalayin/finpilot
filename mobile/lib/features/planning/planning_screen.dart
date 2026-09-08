import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/api_client.dart';
import '../automation/automation_screen.dart';
import 'planning_service.dart';

class PlanningScreen extends StatefulWidget {
  const PlanningScreen({super.key, required this.api});

  final ApiClient api;

  @override
  State<PlanningScreen> createState() => _PlanningScreenState();
}

class _PlanningScreenState extends State<PlanningScreen> {
  late final PlanningService _planning = PlanningService(widget.api);
  late Future<List<dynamic>> _goals;
  late Future<List<dynamic>> _budgets;

  final _money = NumberFormat.currency(locale: 'en_IN', symbol: '₹', decimalDigits: 0);

  @override
  void initState() {
    super.initState();
    _reload();
  }

  void _reload() {
    _goals = _planning.listGoals();
    _budgets = _planning.listBudgets();
  }

  Future<void> _addGoal() async {
    final name = TextEditingController();
    final target = TextEditingController();
    final current = TextEditingController(text: '0');

    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('New savings goal'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(controller: name, decoration: const InputDecoration(labelText: 'Goal name')),
            TextField(controller: target, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Target amount')),
            TextField(controller: current, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Already saved')),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          FilledButton(
            onPressed: () async {
              final targetAmount = double.tryParse(target.text.trim());
              final currentAmount = double.tryParse(current.text.trim());
              if (name.text.trim().isEmpty || targetAmount == null || currentAmount == null) return;
              await _planning.createGoal(
                name: name.text,
                targetAmount: targetAmount,
                currentAmount: currentAmount,
              );
              if (context.mounted) Navigator.pop(context, true);
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );

    name.dispose();
    target.dispose();
    current.dispose();

    if (saved == true) setState(_reload);
  }

  Future<void> _addBudget() async {
    final name = TextEditingController();
    final amount = TextEditingController();
    final now = DateTime.now();
    final start = DateTime(now.year, now.month, 1);
    final end = DateTime(now.year, now.month + 1, 0);

    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('New monthly budget'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(controller: name, decoration: const InputDecoration(labelText: 'Budget name')),
            TextField(controller: amount, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Budget amount')),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          FilledButton(
            onPressed: () async {
              final value = double.tryParse(amount.text.trim());
              if (name.text.trim().isEmpty || value == null || value <= 0) return;
              await _planning.createBudget(
                name: name.text,
                amount: value,
                periodStart: start,
                periodEnd: end,
              );
              if (context.mounted) Navigator.pop(context, true);
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );

    name.dispose();
    amount.dispose();

    if (saved == true) setState(_reload);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Planning')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(
            children: [
              Expanded(child: FilledButton.tonalIcon(onPressed: _addBudget, icon: const Icon(Icons.pie_chart_outline), label: const Text('Add budget'))),
              const SizedBox(width: 12),
              Expanded(child: FilledButton.tonalIcon(onPressed: _addGoal, icon: const Icon(Icons.flag_outlined), label: const Text('Add goal'))),
            ],
          ),
          const SizedBox(height: 12),
          FilledButton.tonalIcon(
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(
                builder: (_) => AutomationScreen(api: widget.api),
              ),
            ),
            icon: const Icon(Icons.auto_mode_outlined),
            label: const Text('Bills, recurring & cash-flow forecast'),
          ),
          const SizedBox(height: 24),
          Text('Budgets', style: Theme.of(context).textTheme.titleLarge),
          FutureBuilder<List<dynamic>>(
            future: _budgets,
            builder: (context, snapshot) {
              if (!snapshot.hasData) return const Padding(padding: EdgeInsets.all(24), child: Center(child: CircularProgressIndicator()));
              final items = snapshot.data!;
              if (items.isEmpty) return const Card(child: Padding(padding: EdgeInsets.all(16), child: Text('No budgets yet.')));
              return Column(
                children: items.map((item) => Card(
                  child: ListTile(
                    leading: const Icon(Icons.pie_chart_outline),
                    title: Text(item['name'].toString()),
                    subtitle: Text(item['period_start'].toString() + ' to ' + item['period_end'].toString()),
                    trailing: Text(_money.format(double.parse(item['amount'].toString()))),
                  ),
                )).toList(),
              );
            },
          ),
          const SizedBox(height: 24),
          Text('Savings goals', style: Theme.of(context).textTheme.titleLarge),
          FutureBuilder<List<dynamic>>(
            future: _goals,
            builder: (context, snapshot) {
              if (!snapshot.hasData) return const Padding(padding: EdgeInsets.all(24), child: Center(child: CircularProgressIndicator()));
              final items = snapshot.data!;
              if (items.isEmpty) return const Card(child: Padding(padding: EdgeInsets.all(16), child: Text('No savings goals yet.')));
              return Column(
                children: items.map((item) {
                  final current = double.parse(item['current_amount'].toString());
                  final target = double.parse(item['target_amount'].toString());
                  final progress = target <= 0 ? 0.0 : (current / target).clamp(0.0, 1.0);
                  return Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(item['name'].toString(), style: const TextStyle(fontWeight: FontWeight.w700)),
                          const SizedBox(height: 8),
                          LinearProgressIndicator(value: progress),
                          const SizedBox(height: 8),
                          Text(_money.format(current) + ' of ' + _money.format(target)),
                        ],
                      ),
                    ),
                  );
                }).toList(),
              );
            },
          ),
        ],
      ),
    );
  }
}
