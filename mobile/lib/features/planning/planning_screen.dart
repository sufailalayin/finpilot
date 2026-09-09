import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/api_client.dart';
import '../assets/assets_screen.dart';
import '../automation/automation_screen.dart';
import '../liabilities/liabilities_screen.dart';
import '../receivables/receivables_screen.dart';
import '../subscription/pro_feature_gate.dart';
import 'planning_service.dart';
import 'budget_dashboard_screen.dart';
import 'goal_planner_screen.dart';

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
    String goalType = 'emergency_fund';
    DateTime? targetDate;

    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setLocal) => AlertDialog(
        title: const Text('New savings goal'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(controller: name, decoration: const InputDecoration(labelText: 'Goal name')),
            TextField(controller: target, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Target amount')),
            TextField(controller: current, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Already saved')),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: goalType,
              decoration: const InputDecoration(labelText: 'Goal type'),
              items: const [
                DropdownMenuItem(value: 'emergency_fund', child: Text('Emergency fund')),
                DropdownMenuItem(value: 'travel', child: Text('Travel')),
                DropdownMenuItem(value: 'car', child: Text('Car')),
                DropdownMenuItem(value: 'home', child: Text('Home')),
                DropdownMenuItem(value: 'education', child: Text('Education')),
                DropdownMenuItem(value: 'wedding', child: Text('Wedding')),
                DropdownMenuItem(value: 'retirement', child: Text('Retirement')),
                DropdownMenuItem(value: 'other', child: Text('Other')),
              ],
              onChanged: (value) {
                if (value != null) setLocal(() => goalType = value);
              },
            ),
            const SizedBox(height: 8),
            ListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Target date'),
              subtitle: Text(
                targetDate == null
                    ? 'Optional'
                    : DateFormat('dd MMM yyyy').format(targetDate!),
              ),
              trailing: const Icon(Icons.calendar_today_outlined),
              onTap: () async {
                final picked = await showDatePicker(
                  context: context,
                  firstDate: DateTime.now(),
                  lastDate: DateTime.now().add(const Duration(days: 7300)),
                  initialDate: targetDate ?? DateTime.now().add(const Duration(days: 365)),
                );
                if (picked != null) setLocal(() => targetDate = picked);
              },
            ),
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
                goalType: goalType,
                targetDate: targetDate,
              );
              if (!context.mounted) return;
              FocusManager.instance.primaryFocus?.unfocus();
              Navigator.of(context).pop(true);
            },
            child: const Text('Save'),
          ),
        ],
      ),
      ),
    );

    WidgetsBinding.instance.addPostFrameCallback((_) {
      name.dispose();
      target.dispose();
      current.dispose();
    });

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
              if (!context.mounted) return;
              FocusManager.instance.primaryFocus?.unfocus();
              Navigator.of(context).pop(true);
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );

    WidgetsBinding.instance.addPostFrameCallback((_) {
      name.dispose();
      amount.dispose();
    });

    if (saved == true) setState(_reload);
  }

  Future<void> _editBudget(Map<String, dynamic> item) async {
    final name = TextEditingController(text: item['name']?.toString() ?? '');
    final amount = TextEditingController(text: item['amount']?.toString() ?? '');
    final start =
        DateTime.tryParse(item['period_start']?.toString() ?? '') ??
            DateTime.now();
    final end =
        DateTime.tryParse(item['period_end']?.toString() ?? '') ??
            DateTime.now();

    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Edit budget'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: name,
              decoration: const InputDecoration(labelText: 'Budget name'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: amount,
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(
                labelText: 'Budget amount',
                prefixText: '₹ ',
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () async {
              final value = double.tryParse(
                amount.text.trim().replaceAll(',', ''),
              );
              if (name.text.trim().isEmpty || value == null || value <= 0) {
                return;
              }

              await _planning.updateBudget(
                budgetId: item['id'].toString(),
                name: name.text,
                amount: value,
                periodStart: start,
                periodEnd: end,
                categoryId: item['category_id']?.toString(),
                rolloverEnabled: item['rollover_enabled'] == true,
                alertThresholdPct: double.tryParse(
                      item['alert_threshold_pct']?.toString() ?? '80',
                    ) ??
                    80,
              );

              if (!context.mounted) return;
              FocusManager.instance.primaryFocus?.unfocus();
              Navigator.of(context).pop(true);
            },
            child: const Text('Save changes'),
          ),
        ],
      ),
    );

    WidgetsBinding.instance.addPostFrameCallback((_) {
      name.dispose();
      amount.dispose();
    });

    if (saved == true) {
      setState(_reload);
    }
  }

  Future<void> _deleteBudget(Map<String, dynamic> item) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete budget?'),
        content: Text(
          'Delete "' + item['name'].toString() + '"?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;
    await _planning.deleteBudget(item['id'].toString());
    if (mounted) setState(_reload);
  }

  Future<void> _editGoal(Map<String, dynamic> item) async {
    final name = TextEditingController(text: item['name']?.toString() ?? '');
    final target = TextEditingController(
      text: item['target_amount']?.toString() ?? '',
    );
    final current = TextEditingController(
      text: item['current_amount']?.toString() ?? '0',
    );
    final goalType = item['goal_type']?.toString() ?? 'other';
    final targetDate = item['target_date'] == null
        ? null
        : DateTime.tryParse(item['target_date'].toString());

    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Edit savings goal'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: name,
              decoration: const InputDecoration(labelText: 'Goal name'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: target,
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(
                labelText: 'Target amount',
                prefixText: '₹ ',
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: current,
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(
                labelText: 'Already saved',
                prefixText: '₹ ',
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () async {
              final targetValue = double.tryParse(
                target.text.trim().replaceAll(',', ''),
              );
              final currentValue = double.tryParse(
                current.text.trim().replaceAll(',', ''),
              );

              if (name.text.trim().isEmpty ||
                  targetValue == null ||
                  currentValue == null ||
                  targetValue <= 0 ||
                  currentValue < 0 ||
                  currentValue > targetValue) {
                return;
              }

              await _planning.updateGoal(
                goalId: item['id'].toString(),
                name: name.text,
                goalType: goalType,
                targetAmount: targetValue,
                currentAmount: currentValue,
                targetDate: targetDate,
              );

              if (!context.mounted) return;
              FocusManager.instance.primaryFocus?.unfocus();
              Navigator.of(context).pop(true);
            },
            child: const Text('Save changes'),
          ),
        ],
      ),
    );

    WidgetsBinding.instance.addPostFrameCallback((_) {
      name.dispose();
      target.dispose();
      current.dispose();
    });

    if (saved == true) {
      setState(_reload);
    }
  }

  Future<void> _deleteGoal(Map<String, dynamic> item) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete goal?'),
        content: Text(
          'Delete "' + item['name'].toString() + '"?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;
    await _planning.deleteGoal(item['id'].toString());
    if (mounted) setState(_reload);
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
                builder: (_) => ProFeatureGate(api: widget.api, featureCode: 'smart_alerts', child: AutomationScreen(api: widget.api)),
              ),
            ),
            icon: const Icon(Icons.auto_mode_outlined),
            label: const Text('Bills, recurring & cash-flow forecast'),
          ),
          const SizedBox(height: 12),
          FilledButton.tonalIcon(
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(
                builder: (_) => ProFeatureGate(api: widget.api, featureCode: 'assets_liabilities', child: LiabilitiesScreen(api: widget.api)),
              ),
            ),
            icon: const Icon(Icons.account_balance_outlined),
            label: const Text('Loans, EMI & debt analytics'),
          ),
          const SizedBox(height: 12),
          FilledButton.tonalIcon(
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(
                builder: (_) => ProFeatureGate(
                  api: widget.api,
                  featureCode: 'assets_liabilities',
                  child: ReceivablesScreen(api: widget.api),
                ),
              ),
            ),
            icon: const Icon(Icons.handshake_outlined),
            label: const Text('Money given & pending returns'),
          ),
          const SizedBox(height: 12),
          FilledButton.tonalIcon(
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(
                builder: (_) => ProFeatureGate(api: widget.api, featureCode: 'assets_liabilities', child: AssetsScreen(api: widget.api)),
              ),
            ),
            icon: const Icon(Icons.savings_outlined),
            label: const Text('Assets & investments'),
          ),
          const SizedBox(height: 24),
          Row(
            children: [
              Expanded(
                child: Text('Budgets', style: Theme.of(context).textTheme.titleLarge),
              ),
              TextButton(
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => ProFeatureGate(api: widget.api, featureCode: 'smart_budgeting', child: BudgetDashboardScreen(api: widget.api)),
                  ),
                ),
                child: const Text('View budget control'),
              ),
            ],
          ),
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
                    trailing: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          _money.format(
                            double.tryParse(item['amount'].toString()) ?? 0,
                          ),
                        ),
                        PopupMenuButton<String>(
                          onSelected: (action) async {
                            final row = Map<String, dynamic>.from(item as Map);
                            if (action == 'edit') {
                              await _editBudget(row);
                            } else if (action == 'delete') {
                              await _deleteBudget(row);
                            }
                          },
                          itemBuilder: (_) => const [
                            PopupMenuItem(
                              value: 'edit',
                              child: Text('Edit'),
                            ),
                            PopupMenuItem(
                              value: 'delete',
                              child: Text('Delete'),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                )).toList(),
              );
            },
          ),
          const SizedBox(height: 24),
          Row(
            children: [
              Expanded(
                child: Text('Savings goals', style: Theme.of(context).textTheme.titleLarge),
              ),
              TextButton(
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => ProFeatureGate(api: widget.api, featureCode: 'smart_budgeting', child: GoalPlannerScreen(api: widget.api)),
                  ),
                ),
                child: const Text('Open goal planner'),
              ),
            ],
          ),
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
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  item['name'].toString(),
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ),
                              PopupMenuButton<String>(
                                onSelected: (action) async {
                                  final row = Map<String, dynamic>.from(
                                    item as Map,
                                  );
                                  if (action == 'edit') {
                                    await _editGoal(row);
                                  } else if (action == 'delete') {
                                    await _deleteGoal(row);
                                  }
                                },
                                itemBuilder: (_) => const [
                                  PopupMenuItem(
                                    value: 'edit',
                                    child: Text('Edit'),
                                  ),
                                  PopupMenuItem(
                                    value: 'delete',
                                    child: Text('Delete'),
                                  ),
                                ],
                              ),
                            ],
                          ),
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
