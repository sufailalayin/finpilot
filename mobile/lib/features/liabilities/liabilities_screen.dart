import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/api_client.dart';
import '../../core/app_error_state.dart';
import 'liability_service.dart';

class LiabilitiesScreen extends StatefulWidget {
  const LiabilitiesScreen({super.key, required this.api});

  final ApiClient api;

  @override
  State<LiabilitiesScreen> createState() => _LiabilitiesScreenState();
}

class _LiabilitiesScreenState extends State<LiabilitiesScreen> {
  late final LiabilityService _liabilities = LiabilityService(widget.api);
  late Future<Map<String, dynamic>> _future;

  final _money = NumberFormat.currency(
    locale: 'en_IN',
    symbol: '₹',
    decimalDigits: 0,
  );

  @override
  void initState() {
    super.initState();
    _future = _liabilities.overview();
  }

  Future<void> _refresh() async {
    setState(() => _future = _liabilities.overview());
    await _future;
  }

  Future<void> _addLiability() async {
    final name = TextEditingController();
    final lender = TextEditingController();
    final original = TextEditingController();
    final outstanding = TextEditingController();
    final rate = TextEditingController(text: '0');
    final emi = TextEditingController(text: '0');
    final accounts = await _liabilities.accounts();
    String type = 'personal_loan';
    String destinationType = accounts.isEmpty ? 'outside' : 'account';
    String? fundingAccountId =
        accounts.isEmpty ? null : accounts.first['id'].toString();
    DateTime? due;

    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setLocal) => AlertDialog(
          title: const Text('Add loan / liability'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: name,
                  decoration: const InputDecoration(labelText: 'Name'),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: type,
                  decoration: const InputDecoration(labelText: 'Type'),
                  items: const [
                    DropdownMenuItem(
                      value: 'personal_loan',
                      child: Text('Personal loan'),
                    ),
                    DropdownMenuItem(
                      value: 'home_loan',
                      child: Text('Home loan'),
                    ),
                    DropdownMenuItem(
                      value: 'vehicle_loan',
                      child: Text('Vehicle loan'),
                    ),
                    DropdownMenuItem(
                      value: 'credit_card',
                      child: Text('Credit card'),
                    ),
                    DropdownMenuItem(
                      value: 'business_loan',
                      child: Text('Business loan'),
                    ),
                    DropdownMenuItem(
                      value: 'other',
                      child: Text('Other'),
                    ),
                  ],
                  onChanged: (value) {
                    if (value != null) setLocal(() => type = value);
                  },
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: lender,
                  decoration: const InputDecoration(labelText: 'Lender'),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: destinationType,
                  decoration: const InputDecoration(
                    labelText: 'Borrowed money received into',
                  ),
                  items: const [
                    DropdownMenuItem(value: 'account', child: Text('My cash / bank account')),
                    DropdownMenuItem(value: 'outside', child: Text('Outside FinPilot')),
                  ],
                  onChanged: (value) {
                    if (value == null) return;
                    setLocal(() {
                      destinationType = value;
                      if (value != 'account') fundingAccountId = null;
                    });
                  },
                ),
                if (destinationType == 'account') ...[
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    initialValue: fundingAccountId,
                    decoration: const InputDecoration(labelText: 'Select cash / bank account'),
                    items: accounts.map((row) => DropdownMenuItem<String>(
                      value: row['id'].toString(),
                      child: Text(
                        row['name'].toString() + ' • ' +
                        _money.format(double.tryParse(row['current_balance'].toString()) ?? 0),
                      ),
                    )).toList(),
                    onChanged: (value) => setLocal(() => fundingAccountId = value),
                  ),
                ],
                const SizedBox(height: 12),
                TextField(
                  controller: original,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                    labelText: 'Original principal',
                    prefixText: '₹ ',
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: outstanding,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                    labelText: 'Outstanding principal',
                    prefixText: '₹ ',
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: rate,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                    labelText: 'Interest rate %',
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: emi,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                    labelText: 'Monthly EMI',
                    prefixText: '₹ ',
                  ),
                ),
                const SizedBox(height: 12),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Next due date'),
                  subtitle: Text(
                    due == null
                        ? 'Optional'
                        : DateFormat('dd MMM yyyy').format(due!),
                  ),
                  onTap: () async {
                    final picked = await showDatePicker(
                      context: context,
                      firstDate: DateTime.now(),
                      lastDate: DateTime.now().add(
                        const Duration(days: 3650),
                      ),
                      initialDate: due ?? DateTime.now(),
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
                final originalValue = double.tryParse(
                  original.text.trim().replaceAll(',', ''),
                );
                final outstandingValue = double.tryParse(
                  outstanding.text.trim().replaceAll(',', ''),
                );
                final rateValue =
                    double.tryParse(rate.text.trim()) ?? 0;
                final emiValue = double.tryParse(
                      emi.text.trim().replaceAll(',', ''),
                    ) ??
                    0;

                if (name.text.trim().isEmpty ||
                    originalValue == null ||
                    outstandingValue == null ||
                    originalValue <= 0 ||
                    outstandingValue <= 0 ||
                    (destinationType == 'account' && fundingAccountId == null)) {
                  return;
                }

                await _liabilities.createLiability(
                  name: name.text,
                  liabilityType: type,
                  lender: lender.text,
                  originalPrincipal: originalValue,
                  outstandingPrincipal: outstandingValue,
                  interestRate: rateValue,
                  emiAmount: emiValue,
                  nextDueOn: due,
                  fundingAccountId:
                      destinationType == 'account' ? fundingAccountId : null,
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
      lender.dispose();
      original.dispose();
      outstanding.dispose();
      rate.dispose();
      emi.dispose();
    });

    if (saved == true) await _refresh();
  }

  Future<void> _editLiability(Map<String, dynamic> item) async {
    final name = TextEditingController(text: item['name']?.toString() ?? '');
    final lender = TextEditingController(text: item['lender']?.toString() ?? '');
    final outstanding = TextEditingController(
      text: item['outstanding_principal']?.toString() ?? '',
    );
    final rate = TextEditingController(
      text: item['interest_rate']?.toString() ?? '0',
    );
    final emi = TextEditingController(
      text: item['emi_amount']?.toString() ?? '0',
    );
    var type = item['liability_type']?.toString() ?? 'other';
    DateTime? due = item['next_due_on'] == null
        ? null
        : DateTime.tryParse(item['next_due_on'].toString());

    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setLocal) => AlertDialog(
          title: const Text('Edit liability'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(controller: name, decoration: const InputDecoration(labelText: 'Name')),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: type,
                  decoration: const InputDecoration(labelText: 'Type'),
                  items: const [
                    DropdownMenuItem(value: 'personal_loan', child: Text('Personal loan')),
                    DropdownMenuItem(value: 'home_loan', child: Text('Home loan')),
                    DropdownMenuItem(value: 'vehicle_loan', child: Text('Vehicle loan')),
                    DropdownMenuItem(value: 'credit_card', child: Text('Credit card')),
                    DropdownMenuItem(value: 'business_loan', child: Text('Business loan')),
                    DropdownMenuItem(value: 'other', child: Text('Other')),
                  ],
                  onChanged: (value) {
                    if (value != null) setLocal(() => type = value);
                  },
                ),
                const SizedBox(height: 12),
                TextField(controller: lender, decoration: const InputDecoration(labelText: 'Lender')),
                const SizedBox(height: 12),
                TextField(controller: outstanding, keyboardType: const TextInputType.numberWithOptions(decimal: true), decoration: const InputDecoration(labelText: 'Outstanding principal', prefixText: '₹ ')),
                const SizedBox(height: 12),
                TextField(controller: rate, keyboardType: const TextInputType.numberWithOptions(decimal: true), decoration: const InputDecoration(labelText: 'Interest rate %')),
                const SizedBox(height: 12),
                TextField(controller: emi, keyboardType: const TextInputType.numberWithOptions(decimal: true), decoration: const InputDecoration(labelText: 'Monthly EMI', prefixText: '₹ ')),
                const SizedBox(height: 12),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Next due date'),
                  subtitle: Text(due == null ? 'Optional' : DateFormat('dd MMM yyyy').format(due!)),
                  onTap: () async {
                    final picked = await showDatePicker(
                      context: context,
                      firstDate: DateTime.now().subtract(const Duration(days: 3650)),
                      lastDate: DateTime.now().add(const Duration(days: 3650)),
                      initialDate: due ?? DateTime.now(),
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
                final outstandingValue = double.tryParse(outstanding.text.trim().replaceAll(',', ''));
                final rateValue = double.tryParse(rate.text.trim()) ?? 0;
                final emiValue = double.tryParse(emi.text.trim().replaceAll(',', '')) ?? 0;
                if (name.text.trim().isEmpty || outstandingValue == null || outstandingValue < 0) return;
                await _liabilities.updateLiability(
                  liabilityId: item['id'].toString(),
                  name: name.text,
                  liabilityType: type,
                  lender: lender.text,
                  outstandingPrincipal: outstandingValue,
                  interestRate: rateValue,
                  emiAmount: emiValue,
                  nextDueOn: due,
                );
                if (!context.mounted) return;
                FocusManager.instance.primaryFocus?.unfocus();
                Navigator.of(context).pop(true);
              },
              child: const Text('Save changes'),
            ),
          ],
        ),
      ),
    );

    WidgetsBinding.instance.addPostFrameCallback((_) {
      name.dispose();
      lender.dispose();
      outstanding.dispose();
      rate.dispose();
      emi.dispose();
    });
    if (saved == true) await _refresh();
  }

  Future<void> _recordPayment(Map<String, dynamic> item) async {
    final amount = TextEditingController(
      text: item['emi_amount']?.toString() ?? '',
    );
    final principal = TextEditingController();
    final interest = TextEditingController(text: '0');
    DateTime paidOn = DateTime.now();

    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Record EMI / payment'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: amount,
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(
                labelText: 'Total payment',
                prefixText: '₹ ',
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: principal,
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(
                labelText: 'Principal component',
                prefixText: '₹ ',
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: interest,
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(
                labelText: 'Interest component',
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
              final total = double.tryParse(
                amount.text.trim().replaceAll(',', ''),
              );
              final principalValue = double.tryParse(
                principal.text.trim().replaceAll(',', ''),
              );
              final interestValue = double.tryParse(
                    interest.text.trim().replaceAll(',', ''),
                  ) ??
                  0;

              if (total == null ||
                  principalValue == null ||
                  total <= 0 ||
                  principalValue <= 0) {
                return;
              }

              await _liabilities.recordPayment(
                liabilityId: item['id'].toString(),
                amount: total,
                principalComponent: principalValue,
                interestComponent: interestValue,
                paidOn: paidOn,
              );
              if (!context.mounted) return;
                FocusManager.instance.primaryFocus?.unfocus();
                Navigator.of(context).pop(true);
            },
            child: const Text('Record'),
          ),
        ],
      ),
    );

    WidgetsBinding.instance.addPostFrameCallback((_) {
      amount.dispose();
      principal.dispose();
      interest.dispose();
    });

    if (saved == true) await _refresh();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Loans & Liabilities',
          style: TextStyle(fontWeight: FontWeight.w800),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _addLiability,
        icon: const Icon(Icons.add),
        label: const Text('Add liability'),
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
          final liabilities =
              (data['liabilities'] as List<dynamic>?) ?? const [];
          final outstanding = double.tryParse(
                data['total_outstanding'].toString(),
              ) ??
              0;
          final monthlyEmi = double.tryParse(
                data['monthly_emi_commitment'].toString(),
              ) ??
              0;
          final payoff = double.tryParse(
                data['payoff_progress_pct'].toString(),
              ) ??
              0;
          final dti = data['debt_to_income_pct'] == null
              ? null
              : double.tryParse(data['debt_to_income_pct'].toString());

          return RefreshIndicator(
            onRefresh: _refresh,
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 100),
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
                        'TOTAL OUTSTANDING DEBT',
                        style: TextStyle(
                          fontWeight: FontWeight.w800,
                          letterSpacing: 1,
                          fontSize: 12,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        _money.format(outstanding),
                        style: const TextStyle(
                          fontWeight: FontWeight.w900,
                          fontSize: 30,
                        ),
                      ),
                      const SizedBox(height: 16),
                      LinearProgressIndicator(
                        value: (payoff / 100).clamp(0.0, 1.0),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Debt repaid: ' + payoff.toStringAsFixed(1) + '%',
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: Card(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Icon(Icons.calendar_month_outlined),
                              const SizedBox(height: 10),
                              Text(
                                _money.format(monthlyEmi),
                                style: const TextStyle(
                                  fontWeight: FontWeight.w900,
                                  fontSize: 18,
                                ),
                              ),
                              const SizedBox(height: 4),
                              const Text('Monthly EMI'),
                            ],
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Card(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Icon(Icons.percent),
                              const SizedBox(height: 10),
                              Text(
                                dti == null
                                    ? '—'
                                    : dti.toStringAsFixed(1) + '%',
                                style: const TextStyle(
                                  fontWeight: FontWeight.w900,
                                  fontSize: 18,
                                ),
                              ),
                              const SizedBox(height: 4),
                              const Text('Debt-to-income'),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                Text(
                  'Your liabilities',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
                const SizedBox(height: 10),
                if (liabilities.isEmpty)
                  const Card(
                    child: Padding(
                      padding: EdgeInsets.all(18),
                      child: Text('No loans or liabilities recorded.'),
                    ),
                  )
                else
                  ...liabilities.map((raw) {
                    final item = Map<String, dynamic>.from(raw as Map);
                    final balance = double.tryParse(
                          item['outstanding_principal'].toString(),
                        ) ??
                        0;
                    final original = double.tryParse(
                          item['original_principal'].toString(),
                        ) ??
                        0;
                    final progress = original <= 0
                        ? 0.0
                        : ((original - balance) / original).clamp(0.0, 1.0);

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
                                      fontWeight: FontWeight.w800,
                                      fontSize: 16,
                                    ),
                                  ),
                                ),
                                PopupMenuButton<String>(
                                  onSelected: (action) async {
                                    if (action == 'edit') {
                                      await _editLiability(item);
                                    } else if (action == 'payment') {
                                      await _recordPayment(item);
                                    } else if (action == 'delete') {
                                      await _liabilities.deleteLiability(
                                        item['id'].toString(),
                                      );
                                      await _refresh();
                                    }
                                  },
                                  itemBuilder: (_) => const [
                                    PopupMenuItem(
                                      value: 'edit',
                                      child: Text('Edit'),
                                    ),
                                    PopupMenuItem(
                                      value: 'payment',
                                      child: Text('Record payment'),
                                    ),
                                    PopupMenuItem(
                                      value: 'delete',
                                      child: Text('Delete'),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                            Text(
                              item['lender']?.toString() ??
                                  item['liability_type'].toString(),
                            ),
                            const SizedBox(height: 12),
                            LinearProgressIndicator(value: progress),
                            const SizedBox(height: 8),
                            Row(
                              children: [
                                Expanded(
                                  child: Text(
                                    'Outstanding\n' +
                                        _money.format(balance),
                                  ),
                                ),
                                Expanded(
                                  child: Text(
                                    'EMI\n' +
                                        _money.format(
                                          double.tryParse(
                                                item['emi_amount'].toString(),
                                              ) ??
                                              0,
                                        ),
                                  ),
                                ),
                                Expanded(
                                  child: Text(
                                    'Rate\n' +
                                        item['interest_rate'].toString() +
                                        '%',
                                  ),
                                ),
                              ],
                            ),
                            if (item['next_due_on'] != null) ...[
                              const SizedBox(height: 8),
                              Text(
                                'Next due: ' +
                                    item['next_due_on'].toString(),
                              ),
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
