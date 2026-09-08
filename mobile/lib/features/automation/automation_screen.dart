import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/api_client.dart';
import '../finance/finance_service.dart';
import 'automation_service.dart';

class AutomationScreen extends StatefulWidget {
  const AutomationScreen({super.key, required this.api});

  final ApiClient api;

  @override
  State<AutomationScreen> createState() => _AutomationScreenState();
}

class _AutomationScreenState extends State<AutomationScreen> {
  late final AutomationService _automation = AutomationService(widget.api);
  late final FinanceService _finance = FinanceService(widget.api);
  late Future<Map<String, dynamic>> _future;

  final _money = NumberFormat.currency(
    locale: 'en_IN',
    symbol: '₹',
    decimalDigits: 0,
  );

  @override
  void initState() {
    super.initState();
    _future = _automation.overview();
  }

  Future<void> _refresh() async {
    setState(() => _future = _automation.overview());
    await _future;
  }

  Future<void> _addBill() async {
    final name = TextEditingController();
    final amount = TextEditingController();
    var due = DateTime.now().add(const Duration(days: 7));

    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setLocal) => AlertDialog(
          title: const Text('Add bill reminder'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: name,
                decoration: const InputDecoration(labelText: 'Bill name'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: amount,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(labelText: 'Amount'),
              ),
              const SizedBox(height: 12),
              ListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('Due date'),
                subtitle: Text(DateFormat('dd MMM yyyy').format(due)),
                onTap: () async {
                  final picked = await showDatePicker(
                    context: context,
                    firstDate: DateTime.now(),
                    lastDate: DateTime.now().add(const Duration(days: 730)),
                    initialDate: due,
                  );
                  if (picked != null) setLocal(() => due = picked);
                },
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
                final value =
                    double.tryParse(amount.text.replaceAll(',', '').trim());
                if (name.text.trim().isEmpty ||
                    value == null ||
                    value <= 0) {
                  return;
                }
                await _automation.addBill(
                  name: name.text,
                  amount: value,
                  dueOn: due,
                );
                if (context.mounted) Navigator.pop(context, true);
              },
              child: const Text('Save'),
            ),
          ],
        ),
      ),
    );

    name.dispose();
    amount.dispose();
    if (saved == true) await _refresh();
  }

  Future<void> _addRecurring() async {
    final accounts = await _finance.listAccounts();
    if (!mounted) return;
    if (accounts.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Create an account first.')),
      );
      return;
    }

    final name = TextEditingController();
    final amount = TextEditingController();
    String accountId = accounts.first['id'].toString();
    String type = 'expense';
    String frequency = 'monthly';
    var nextDue = DateTime.now().add(const Duration(days: 30));

    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setLocal) => AlertDialog(
          title: const Text('Add recurring item'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: name,
                  decoration: const InputDecoration(labelText: 'Name'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: amount,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(labelText: 'Amount'),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: accountId,
                  decoration: const InputDecoration(labelText: 'Account'),
                  items: accounts
                      .map(
                        (a) => DropdownMenuItem<String>(
                          value: a['id'].toString(),
                          child: Text(a['name'].toString()),
                        ),
                      )
                      .toList(),
                  onChanged: (v) {
                    if (v != null) setLocal(() => accountId = v);
                  },
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: type,
                  decoration: const InputDecoration(labelText: 'Type'),
                  items: const [
                    DropdownMenuItem(value: 'expense', child: Text('Expense')),
                    DropdownMenuItem(value: 'income', child: Text('Income')),
                  ],
                  onChanged: (v) {
                    if (v != null) setLocal(() => type = v);
                  },
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: frequency,
                  decoration: const InputDecoration(labelText: 'Frequency'),
                  items: const [
                    DropdownMenuItem(value: 'weekly', child: Text('Weekly')),
                    DropdownMenuItem(value: 'monthly', child: Text('Monthly')),
                    DropdownMenuItem(value: 'yearly', child: Text('Yearly')),
                  ],
                  onChanged: (v) {
                    if (v != null) setLocal(() => frequency = v);
                  },
                ),
                const SizedBox(height: 12),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Next due'),
                  subtitle: Text(DateFormat('dd MMM yyyy').format(nextDue)),
                  onTap: () async {
                    final picked = await showDatePicker(
                      context: context,
                      firstDate: DateTime.now(),
                      lastDate: DateTime.now().add(const Duration(days: 730)),
                      initialDate: nextDue,
                    );
                    if (picked != null) setLocal(() => nextDue = picked);
                  },
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () async {
                final value =
                    double.tryParse(amount.text.replaceAll(',', '').trim());
                if (name.text.trim().isEmpty ||
                    value == null ||
                    value <= 0) {
                  return;
                }
                await _automation.addRecurring(
                  accountId: accountId,
                  name: name.text,
                  transactionType: type,
                  amount: value,
                  frequency: frequency,
                  nextDueOn: nextDue,
                );
                if (context.mounted) Navigator.pop(context, true);
              },
              child: const Text('Save'),
            ),
          ],
        ),
      ),
    );

    name.dispose();
    amount.dispose();
    if (saved == true) await _refresh();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Money Automation',
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
                label: const Text('Retry'),
              ),
            );
          }

          final data = snapshot.data!;
          final bills = (data['bills'] as List<dynamic>?) ?? const [];
          final rules =
              (data['recurring_rules'] as List<dynamic>?) ?? const [];
          final forecast = double.tryParse(
                data['projected_30d_net'].toString(),
              ) ??
              0;

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
                        '30-DAY CASH-FLOW FORECAST',
                        style: TextStyle(
                          fontWeight: FontWeight.w800,
                          letterSpacing: 1,
                          fontSize: 12,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        _money.format(forecast),
                        style: const TextStyle(
                          fontWeight: FontWeight.w900,
                          fontSize: 30,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        forecast >= 0
                            ? 'Projected cash flow is positive.'
                            : 'Upcoming commitments may exceed recurring income.',
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: FilledButton.tonalIcon(
                        onPressed: _addBill,
                        icon: const Icon(Icons.notifications_active_outlined),
                        label: const Text('Add bill'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: FilledButton.tonalIcon(
                        onPressed: _addRecurring,
                        icon: const Icon(Icons.repeat),
                        label: const Text('Recurring'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                Text(
                  'Upcoming bills',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
                const SizedBox(height: 8),
                if (bills.isEmpty)
                  const Card(
                    child: Padding(
                      padding: EdgeInsets.all(16),
                      child: Text('No bills due in the next 30 days.'),
                    ),
                  )
                else
                  ...bills.map(
                    (bill) => Card(
                      child: ListTile(
                        leading:
                            const Icon(Icons.notifications_none_outlined),
                        title: Text(bill['name'].toString()),
                        subtitle: Text('Due ' + bill['due_on'].toString()),
                        trailing: Text(
                          _money.format(
                            double.tryParse(bill['amount'].toString()) ?? 0,
                          ),
                        ),
                        onTap: () async {
                          await _automation.markBillPaid(
                            bill['id'].toString(),
                          );
                          await _refresh();
                        },
                      ),
                    ),
                  ),
                const SizedBox(height: 24),
                Text(
                  'Recurring cash flow',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
                const SizedBox(height: 8),
                if (rules.isEmpty)
                  const Card(
                    child: Padding(
                      padding: EdgeInsets.all(16),
                      child: Text('No recurring income or expenses yet.'),
                    ),
                  )
                else
                  ...rules.map(
                    (rule) => Card(
                      child: ListTile(
                        leading: const Icon(Icons.repeat),
                        title: Text(rule['name'].toString()),
                        subtitle: Text(
                          rule['frequency'].toString() +
                              ' • next ' +
                              rule['next_due_on'].toString(),
                        ),
                        trailing: Text(
                          (rule['transaction_type'] == 'income' ? '+ ' : '- ') +
                              _money.format(
                                double.tryParse(rule['amount'].toString()) ?? 0,
                              ),
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }
}
