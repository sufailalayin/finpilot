import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/api_client.dart';
import '../../core/app_error_state.dart';
import '../finance/finance_service.dart';
import 'automation_service.dart';
import 'smart_alerts_screen.dart';

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
    String billType = 'bill';
    String frequency = 'once';
    bool autoRenew = false;
    double reminderDays = 3;
    final provider = TextEditingController();
    final cardLast4 = TextEditingController();
    DateTime? generatedOn;

    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setLocal) => AlertDialog(
          title: const Text('Add bill reminder'),
          content: SingleChildScrollView(
            child: Column(
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
              DropdownButtonFormField<String>(
                initialValue: billType,
                decoration: const InputDecoration(labelText: 'Type'),
                items: const [
                  DropdownMenuItem(value: 'bill', child: Text('Bill')),
                  DropdownMenuItem(value: 'subscription', child: Text('Subscription')),
                  DropdownMenuItem(value: 'emi', child: Text('EMI')),
                  DropdownMenuItem(value: 'insurance', child: Text('Insurance')),
                  DropdownMenuItem(value: 'utility', child: Text('Utility')),
                  DropdownMenuItem(value: 'credit_card', child: Text('Credit card')),
                ],
                onChanged: (value) {
                  if (value != null) {
                    setLocal(() {
                      billType = value;
                      if (value == 'credit_card') {
                        frequency = 'monthly';
                      }
                    });
                  }
                },
              ),
              const SizedBox(height: 12),
              TextField(
                controller: provider,
                decoration: const InputDecoration(labelText: 'Provider / company'),
              ),
              if (billType == 'credit_card') ...[
                const SizedBox(height: 12),
                TextField(
                  controller: cardLast4,
                  keyboardType: TextInputType.number,
                  maxLength: 4,
                  decoration: const InputDecoration(
                    labelText: 'Card last 4 digits',
                    counterText: '',
                  ),
                ),
                const SizedBox(height: 6),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Bill generated / statement date'),
                  subtitle: Text(
                    generatedOn == null
                        ? 'Select date'
                        : DateFormat('dd MMM yyyy').format(generatedOn!),
                  ),
                  trailing: const Icon(Icons.receipt_long_outlined),
                  onTap: () async {
                    final picked = await showDatePicker(
                      context: context,
                      firstDate: DateTime.now().subtract(const Duration(days: 365)),
                      lastDate: DateTime.now().add(const Duration(days: 365)),
                      initialDate: generatedOn ?? DateTime.now(),
                    );
                    if (picked != null) {
                      setLocal(() => generatedOn = picked);
                    }
                  },
                ),
              ],
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: frequency,
                decoration: const InputDecoration(labelText: 'Frequency'),
                items: const [
                  DropdownMenuItem(value: 'once', child: Text('One time')),
                  DropdownMenuItem(value: 'weekly', child: Text('Weekly')),
                  DropdownMenuItem(value: 'monthly', child: Text('Monthly')),
                  DropdownMenuItem(value: 'yearly', child: Text('Yearly')),
                ],
                onChanged: (value) {
                  if (value != null) setLocal(() => frequency = value);
                },
              ),
              if (billType == 'subscription') ...[
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Auto-renew'),
                  value: autoRenew,
                  onChanged: (value) => setLocal(() => autoRenew = value),
                ),
              ],
              ListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('Remind before'),
                subtitle: Text(reminderDays.round().toString() + ' day(s)'),
              ),
              Slider(
                min: 0,
                max: 14,
                divisions: 14,
                value: reminderDays,
                onChanged: (value) => setLocal(() => reminderDays = value),
              ),
              const SizedBox(height: 12),
              ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text(
                  billType == 'credit_card'
                      ? 'Payment last date'
                      : 'Due date',
                ),
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
                  frequency: frequency,
                  billType: billType,
                  provider: provider.text,
                  reminderDaysBefore: reminderDays.round(),
                  autoRenew: autoRenew,
                  billGeneratedOn:
                      billType == 'credit_card' ? generatedOn : null,
                  cardLast4:
                      billType == 'credit_card' ? cardLast4.text : null,
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
    provider.dispose();
    cardLast4.dispose();
    if (saved == true) await _refresh();
  }

  Future<void> _editBill(Map<String, dynamic> bill) async {
    final name = TextEditingController(text: bill['name']?.toString() ?? '');
    final amount = TextEditingController(text: bill['amount']?.toString() ?? '');
    final provider = TextEditingController(text: bill['provider']?.toString() ?? '');
    final cardLast4 = TextEditingController(
      text: bill['card_last4']?.toString() ?? '',
    );
    DateTime? generatedOn = bill['bill_generated_on'] == null
        ? null
        : DateTime.tryParse(bill['bill_generated_on'].toString());
    var due = DateTime.tryParse(bill['due_on']?.toString() ?? '') ?? DateTime.now();
    var frequency = bill['frequency']?.toString() ?? 'once';
    var billType = bill['bill_type']?.toString() ?? 'bill';
    var autoRenew = bill['auto_renew'] == true;
    var reminderDays = double.tryParse(bill['reminder_days_before']?.toString() ?? '3') ?? 3;

    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setLocal) => AlertDialog(
          title: const Text('Edit bill'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(controller: name, decoration: const InputDecoration(labelText: 'Bill name')),
                const SizedBox(height: 12),
                TextField(controller: amount, keyboardType: const TextInputType.numberWithOptions(decimal: true), decoration: const InputDecoration(labelText: 'Amount', prefixText: '₹ ')),
                const SizedBox(height: 12),
                TextField(controller: provider, decoration: const InputDecoration(labelText: 'Provider / company')),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: billType,
                  decoration: const InputDecoration(labelText: 'Type'),
                  items: const [
                    DropdownMenuItem(value: 'bill', child: Text('Bill')),
                    DropdownMenuItem(value: 'subscription', child: Text('Subscription')),
                    DropdownMenuItem(value: 'emi', child: Text('EMI')),
                    DropdownMenuItem(value: 'insurance', child: Text('Insurance')),
                    DropdownMenuItem(value: 'utility', child: Text('Utility')),
                    DropdownMenuItem(value: 'credit_card', child: Text('Credit card')),
                  ],
                  onChanged: (value) {
                    if (value != null) {
                      setLocal(() {
                        billType = value;
                        if (value == 'credit_card') {
                          frequency = 'monthly';
                        }
                      });
                    }
                  },
                ),
                if (billType == 'credit_card') ...[
                  const SizedBox(height: 12),
                  TextField(
                    controller: cardLast4,
                    keyboardType: TextInputType.number,
                    maxLength: 4,
                    decoration: const InputDecoration(
                      labelText: 'Card last 4 digits',
                      counterText: '',
                    ),
                  ),
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('Bill generated / statement date'),
                    subtitle: Text(
                      generatedOn == null
                          ? 'Select date'
                          : DateFormat('dd MMM yyyy').format(generatedOn!),
                    ),
                    trailing: const Icon(Icons.receipt_long_outlined),
                    onTap: () async {
                      final picked = await showDatePicker(
                        context: context,
                        firstDate: DateTime.now().subtract(const Duration(days: 3650)),
                        lastDate: DateTime.now().add(const Duration(days: 3650)),
                        initialDate: generatedOn ?? DateTime.now(),
                      );
                      if (picked != null) setLocal(() => generatedOn = picked);
                    },
                  ),
                ],
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: frequency,
                  decoration: const InputDecoration(labelText: 'Frequency'),
                  items: const [
                    DropdownMenuItem(value: 'once', child: Text('One time')),
                    DropdownMenuItem(value: 'weekly', child: Text('Weekly')),
                    DropdownMenuItem(value: 'monthly', child: Text('Monthly')),
                    DropdownMenuItem(value: 'yearly', child: Text('Yearly')),
                  ],
                  onChanged: (value) {
                    if (value != null) setLocal(() => frequency = value);
                  },
                ),
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Auto-renew'),
                  value: autoRenew,
                  onChanged: (value) => setLocal(() => autoRenew = value),
                ),
                Slider(
                  min: 0,
                  max: 14,
                  divisions: 14,
                  value: reminderDays.clamp(0, 14),
                  label: reminderDays.round().toString(),
                  onChanged: (value) => setLocal(() => reminderDays = value),
                ),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text(
                    billType == 'credit_card'
                        ? 'Payment last date'
                        : 'Due date',
                  ),
                  subtitle: Text(DateFormat('dd MMM yyyy').format(due)),
                  onTap: () async {
                    final picked = await showDatePicker(
                      context: context,
                      firstDate: DateTime.now().subtract(const Duration(days: 3650)),
                      lastDate: DateTime.now().add(const Duration(days: 3650)),
                      initialDate: due,
                    );
                    if (picked != null) setLocal(() => due = picked);
                  },
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
            FilledButton(
              onPressed: () async {
                final value = double.tryParse(amount.text.trim().replaceAll(',', ''));
                if (name.text.trim().isEmpty || value == null || value <= 0) return;
                await _automation.updateBill(
                  billId: bill['id'].toString(),
                  name: name.text,
                  amount: value,
                  dueOn: due,
                  frequency: frequency,
                  billType: billType,
                  provider: provider.text,
                  reminderDaysBefore: reminderDays.round(),
                  autoRenew: autoRenew,
                  billGeneratedOn:
                      billType == 'credit_card' ? generatedOn : null,
                  cardLast4:
                      billType == 'credit_card' ? cardLast4.text : null,
                );
                if (context.mounted) Navigator.pop(context, true);
              },
              child: const Text('Save changes'),
            ),
          ],
        ),
      ),
    );

    name.dispose();
    amount.dispose();
    provider.dispose();
    cardLast4.dispose();
    if (saved == true) await _refresh();
  }

  Future<void> _editRecurring(Map<String, dynamic> rule) async {
    final accounts = await _finance.listAccounts();
    if (!mounted || accounts.isEmpty) return;

    final name = TextEditingController(text: rule['name']?.toString() ?? '');
    final amount = TextEditingController(text: rule['amount']?.toString() ?? '');
    var accountId = rule['account_id']?.toString() ?? accounts.first['id'].toString();
    var type = rule['transaction_type']?.toString() ?? 'expense';
    var frequency = rule['frequency']?.toString() ?? 'monthly';
    var nextDue = DateTime.tryParse(rule['next_due_on']?.toString() ?? '') ?? DateTime.now();

    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setLocal) => AlertDialog(
          title: const Text('Edit recurring item'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(controller: name, decoration: const InputDecoration(labelText: 'Name')),
                const SizedBox(height: 12),
                TextField(controller: amount, keyboardType: const TextInputType.numberWithOptions(decimal: true), decoration: const InputDecoration(labelText: 'Amount', prefixText: '₹ ')),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: accountId,
                  decoration: const InputDecoration(labelText: 'Account'),
                  items: accounts.map((a) => DropdownMenuItem<String>(
                    value: a['id'].toString(),
                    child: Text(a['name'].toString()),
                  )).toList(),
                  onChanged: (value) {
                    if (value != null) setLocal(() => accountId = value);
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
                  onChanged: (value) {
                    if (value != null) setLocal(() => type = value);
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
                  onChanged: (value) {
                    if (value != null) setLocal(() => frequency = value);
                  },
                ),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Next due'),
                  subtitle: Text(DateFormat('dd MMM yyyy').format(nextDue)),
                  onTap: () async {
                    final picked = await showDatePicker(
                      context: context,
                      firstDate: DateTime.now().subtract(const Duration(days: 3650)),
                      lastDate: DateTime.now().add(const Duration(days: 3650)),
                      initialDate: nextDue,
                    );
                    if (picked != null) setLocal(() => nextDue = picked);
                  },
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
            FilledButton(
              onPressed: () async {
                final value = double.tryParse(amount.text.trim().replaceAll(',', ''));
                if (name.text.trim().isEmpty || value == null || value <= 0) return;
                await _automation.updateRecurring(
                  ruleId: rule['id'].toString(),
                  accountId: accountId,
                  name: name.text,
                  transactionType: type,
                  amount: value,
                  frequency: frequency,
                  nextDueOn: nextDue,
                  isActive: rule['is_active'] != false,
                );
                if (context.mounted) Navigator.pop(context, true);
              },
              child: const Text('Save changes'),
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
            return AppErrorState(
              error: snapshot.error,
              onRetry: _refresh,
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
                FilledButton.tonalIcon(
                  onPressed: () => Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => SmartAlertsScreen(api: widget.api),
                    ),
                  ),
                  icon: const Icon(Icons.notifications_active_outlined),
                  label: const Text('Smart alerts'),
                ),
                const SizedBox(height: 12),
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
                        leading: Icon(
                          bill['bill_type'] == 'credit_card'
                              ? Icons.credit_card_outlined
                              : Icons.notifications_none_outlined,
                        ),
                        title: Text(bill['name'].toString()),
                        subtitle: Text(
                          bill['bill_type'] == 'credit_card'
                              ? 'Statement ' +
                                  (bill['bill_generated_on']?.toString() ?? '—') +
                                  ' • Pay by ' +
                                  bill['due_on'].toString()
                              : 'Due ' + bill['due_on'].toString(),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                        trailing: PopupMenuButton<String>(
                          onSelected: (action) async {
                            final row = Map<String, dynamic>.from(bill as Map);
                            if (action == 'edit') {
                              await _editBill(row);
                            } else if (action == 'paid') {
                              await _automation.markBillPaid(bill['id'].toString());
                              await _refresh();
                            } else if (action == 'delete') {
                              await _automation.deleteBill(bill['id'].toString());
                              await _refresh();
                            }
                          },
                          itemBuilder: (_) => const [
                            PopupMenuItem(value: 'edit', child: Text('Edit')),
                            PopupMenuItem(value: 'paid', child: Text('Mark paid')),
                            PopupMenuItem(value: 'delete', child: Text('Delete')),
                          ],
                        ),
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
                        trailing: PopupMenuButton<String>(
                          onSelected: (action) async {
                            final row = Map<String, dynamic>.from(rule as Map);
                            if (action == 'edit') {
                              await _editRecurring(row);
                            } else if (action == 'delete') {
                              await _automation.deleteRecurring(rule['id'].toString());
                              await _refresh();
                            }
                          },
                          itemBuilder: (_) => const [
                            PopupMenuItem(value: 'edit', child: Text('Edit')),
                            PopupMenuItem(value: 'delete', child: Text('Delete')),
                          ],
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
