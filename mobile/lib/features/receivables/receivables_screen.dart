import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/api_client.dart';
import '../../core/app_error_state.dart';
import 'receivable_service.dart';

class ReceivablesScreen extends StatefulWidget {
  const ReceivablesScreen({super.key, required this.api});

  final ApiClient api;

  @override
  State<ReceivablesScreen> createState() => _ReceivablesScreenState();
}

class _ReceivablesScreenState extends State<ReceivablesScreen>
    with SingleTickerProviderStateMixin {
  late final ReceivableService _service = ReceivableService(widget.api);
  late final TabController _tabs = TabController(length: 2, vsync: this);
  late Future<Map<String, dynamic>> _future;

  final _money = NumberFormat.currency(
    locale: 'en_IN',
    symbol: '₹',
    decimalDigits: 0,
  );

  @override
  void initState() {
    super.initState();
    _future = _service.overview();
  }

  Future<void> _refresh() async {
    setState(() => _future = _service.overview());
    await _future;
  }

  Future<void> _addMoneyGiven() async {
    final person = TextEditingController();
    final phone = TextEditingController();
    final amount = TextEditingController();
    final note = TextEditingController();
    final accounts = await _service.accounts();
    String sourceType = 'outside';
    String? sourceAccountId;
    DateTime givenOn = DateTime.now();
    DateTime? dueOn;

    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setLocal) => AlertDialog(
          title: const Text('Money given'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: person,
                  textInputAction: TextInputAction.next,
                  decoration: const InputDecoration(
                    labelText: 'Person name',
                    hintText: 'Who should return the money?',
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: phone,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(
                    labelText: 'Phone (optional)',
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: amount,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                    labelText: 'Amount given',
                    prefixText: '₹ ',
                  ),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: sourceType,
                  decoration: const InputDecoration(labelText: 'Money from'),
                  items: const [
                    DropdownMenuItem(
                      value: 'outside',
                      child: Text('Outside FinPilot'),
                    ),
                    DropdownMenuItem(
                      value: 'account',
                      child: Text('My cash / bank account'),
                    ),
                  ],
                  onChanged: (value) {
                    if (value == null) return;
                    setLocal(() {
                      sourceType = value;
                      if (value != 'account') sourceAccountId = null;
                    });
                  },
                ),
                if (sourceType == 'account') ...[
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    initialValue: sourceAccountId,
                    decoration: const InputDecoration(
                      labelText: 'Select cash / bank account',
                    ),
                    items: accounts
                        .where((row) => row['account_type']?.toString() != 'card')
                        .map(
                          (row) => DropdownMenuItem<String>(
                            value: row['id'].toString(),
                            child: Text(
                              row['name'].toString() +
                                  ' • ' +
                                  _money.format(
                                    double.tryParse(
                                          row['current_balance'].toString(),
                                        ) ??
                                        0,
                                  ),
                            ),
                          ),
                        )
                        .toList(),
                    onChanged: (value) =>
                        setLocal(() => sourceAccountId = value),
                  ),
                ],
                const SizedBox(height: 8),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Given date'),
                  subtitle: Text(DateFormat('dd MMM yyyy').format(givenOn)),
                  trailing: const Icon(Icons.calendar_today_outlined),
                  onTap: () async {
                    final picked = await showDatePicker(
                      context: context,
                      firstDate: DateTime(2000),
                      lastDate: DateTime.now(),
                      initialDate: givenOn,
                    );
                    if (picked != null) setLocal(() => givenOn = picked);
                  },
                ),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Expected return date'),
                  subtitle: Text(
                    dueOn == null
                        ? 'Optional'
                        : DateFormat('dd MMM yyyy').format(dueOn!),
                  ),
                  trailing: const Icon(Icons.event_outlined),
                  onTap: () async {
                    final picked = await showDatePicker(
                      context: context,
                      firstDate: givenOn,
                      lastDate:
                          DateTime.now().add(const Duration(days: 3650)),
                      initialDate:
                          dueOn ?? givenOn.add(const Duration(days: 30)),
                    );
                    if (picked != null) setLocal(() => dueOn = picked);
                  },
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: note,
                  minLines: 2,
                  maxLines: 4,
                  decoration: const InputDecoration(
                    labelText: 'Note (optional)',
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () async {
                final value = double.tryParse(
                  amount.text.trim().replaceAll(',', ''),
                );
                if (person.text.trim().isEmpty ||
                    value == null ||
                    value <= 0 ||
                    (sourceType == 'account' && sourceAccountId == null)) {
                  return;
                }

                await _service.create(
                  personName: person.text,
                  phone: phone.text,
                  originalAmount: value,
                  givenOn: givenOn,
                  dueOn: dueOn,
                  note: note.text,
                  sourceType: sourceType,
                  sourceAccountId: sourceAccountId,
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
      person.dispose();
      phone.dispose();
      amount.dispose();
      note.dispose();
    });

    if (saved == true && mounted) await _refresh();
  }

  Future<void> _recordRepayment(Map<String, dynamic> item) async {
    final amount = TextEditingController(
      text: item['remaining_amount']?.toString() ?? '',
    );
    final note = TextEditingController();
    final accounts = await _service.accounts();
    String destinationType = 'outside';
    String? destinationAccountId;
    DateTime receivedOn = DateTime.now();

    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setLocal) => AlertDialog(
          title: Text(
            'Money received from ' + item['person_name'].toString(),
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Pending: ' +
                    _money.format(
                      double.tryParse(
                            item['remaining_amount'].toString(),
                          ) ??
                          0,
                    ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: amount,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(
                  labelText: 'Amount received',
                  prefixText: '₹ ',
                ),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: destinationType,
                decoration: const InputDecoration(labelText: 'Received into'),
                items: const [
                  DropdownMenuItem(
                    value: 'outside',
                    child: Text('Outside FinPilot'),
                  ),
                  DropdownMenuItem(
                    value: 'account',
                    child: Text('My cash / bank account'),
                  ),
                ],
                onChanged: (value) {
                  if (value == null) return;
                  setLocal(() {
                    destinationType = value;
                    if (value != 'account') destinationAccountId = null;
                  });
                },
              ),
              if (destinationType == 'account') ...[
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: destinationAccountId,
                  decoration: const InputDecoration(
                    labelText: 'Select cash / bank account',
                  ),
                  items: accounts
                      .where((row) => row['account_type']?.toString() != 'card')
                      .map(
                        (row) => DropdownMenuItem<String>(
                          value: row['id'].toString(),
                          child: Text(row['name'].toString()),
                        ),
                      )
                      .toList(),
                  onChanged: (value) =>
                      setLocal(() => destinationAccountId = value),
                ),
              ],
              const SizedBox(height: 8),
              ListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('Received date'),
                subtitle:
                    Text(DateFormat('dd MMM yyyy').format(receivedOn)),
                onTap: () async {
                  final picked = await showDatePicker(
                    context: context,
                    firstDate: DateTime(2000),
                    lastDate: DateTime.now(),
                    initialDate: receivedOn,
                  );
                  if (picked != null) {
                    setLocal(() => receivedOn = picked);
                  }
                },
              ),
              TextField(
                controller: note,
                decoration: const InputDecoration(
                  labelText: 'Note (optional)',
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(false),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () async {
                final value = double.tryParse(
                  amount.text.trim().replaceAll(',', ''),
                );
                final remaining = double.tryParse(
                      item['remaining_amount'].toString(),
                    ) ??
                    0;
                if (value == null ||
                    value <= 0 ||
                    value > remaining ||
                    (destinationType == 'account' &&
                        destinationAccountId == null)) {
                  return;
                }

                await _service.recordRepayment(
                  receivableId: item['id'].toString(),
                  amount: value,
                  receivedOn: receivedOn,
                  note: note.text,
                  destinationType: destinationType,
                  destinationAccountId: destinationAccountId,
                );

                if (!context.mounted) return;
                FocusManager.instance.primaryFocus?.unfocus();
                Navigator.of(context).pop(true);
              },
              child: const Text('Record'),
            ),
          ],
        ),
      ),
    );

    WidgetsBinding.instance.addPostFrameCallback((_) {
      amount.dispose();
      note.dispose();
    });

    if (saved == true && mounted) await _refresh();
  }

  Future<void> _showHistory(Map<String, dynamic> item) async {
    final detail = await _service.detail(item['id'].toString());
    if (!mounted) return;
    final repayments =
        (detail['repayments'] as List<dynamic>?) ?? const [];

    await showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(item['person_name'].toString() + ' history'),
        content: SizedBox(
          width: double.maxFinite,
          child: repayments.isEmpty
              ? const Text('No repayments recorded yet.')
              : ListView.separated(
                  shrinkWrap: true,
                  itemCount: repayments.length,
                  separatorBuilder: (_, __) => const Divider(),
                  itemBuilder: (_, index) {
                    final row = Map<String, dynamic>.from(
                      repayments[index] as Map,
                    );
                    final noteText = row['note'] == null
                        ? ''
                        : ' • ' + row['note'].toString();
                    return ListTile(
                      contentPadding: EdgeInsets.zero,
                      title: Text(
                        _money.format(
                          double.tryParse(row['amount'].toString()) ?? 0,
                        ),
                      ),
                      subtitle: Text(
                        row['received_on'].toString() + noteText,
                      ),
                    );
                  },
                ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  Widget _pendingCard(Map<String, dynamic> item) {
    final remaining =
        double.tryParse(item['remaining_amount'].toString()) ?? 0;
    final original =
        double.tryParse(item['original_amount'].toString()) ?? 0;
    final received =
        double.tryParse(item['amount_received'].toString()) ?? 0;

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    item['person_name'].toString(),
                    style: const TextStyle(
                      fontWeight: FontWeight.w900,
                      fontSize: 17,
                    ),
                  ),
                ),
                Text(
                  _money.format(remaining),
                  style: const TextStyle(
                    fontWeight: FontWeight.w900,
                    fontSize: 18,
                  ),
                ),
              ],
            ),
            if (item['phone'] != null) ...[
              const SizedBox(height: 3),
              Text(item['phone'].toString()),
            ],
            const SizedBox(height: 10),
            Text(
              'Given ' +
                  _money.format(original) +
                  ' • Returned ' +
                  _money.format(received),
            ),
            if (item['due_on'] != null) ...[
              const SizedBox(height: 5),
              Text('Expected by ' + item['due_on'].toString()),
            ],
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: FilledButton.tonal(
                    onPressed: () => _recordRepayment(item),
                    child: const Text('Record returned money'),
                  ),
                ),
                IconButton(
                  onPressed: () => _showHistory(item),
                  tooltip: 'History',
                  icon: const Icon(Icons.history),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _clearedCard(Map<String, dynamic> item) {
    final original =
        double.tryParse(item['original_amount'].toString()) ?? 0;

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: ListTile(
        leading: const CircleAvatar(
          child: Icon(Icons.check),
        ),
        title: Text(
          item['person_name'].toString(),
          style: const TextStyle(fontWeight: FontWeight.w800),
        ),
        subtitle: Text(
          'Fully returned • Given ' + item['given_on'].toString(),
        ),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              _money.format(original),
              style: const TextStyle(fontWeight: FontWeight.w800),
            ),
            IconButton(
              onPressed: () => _showHistory(item),
              icon: const Icon(Icons.history),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _tabs.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Money Given',
          style: TextStyle(fontWeight: FontWeight.w800),
        ),
        bottom: TabBar(
          controller: _tabs,
          tabs: const [
            Tab(text: 'Pending'),
            Tab(text: 'Cleared'),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _addMoneyGiven,
        icon: const Icon(Icons.add),
        label: const Text('Money given'),
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
          final pending =
              (data['pending'] as List<dynamic>?) ?? const [];
          final cleared =
              (data['cleared'] as List<dynamic>?) ?? const [];
          final totalPending =
              double.tryParse(data['total_pending'].toString()) ?? 0;

          return Column(
            children: [
              Container(
                width: double.infinity,
                margin: const EdgeInsets.fromLTRB(16, 14, 16, 8),
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'TOTAL MONEY TO RECEIVE',
                      style: TextStyle(
                        fontWeight: FontWeight.w800,
                        letterSpacing: 0.8,
                        fontSize: 12,
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      _money.format(totalPending),
                      style: const TextStyle(
                        fontWeight: FontWeight.w900,
                        fontSize: 28,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      data['pending_count'].toString() +
                          ' pending • ' +
                          data['cleared_count'].toString() +
                          ' cleared',
                    ),
                  ],
                ),
              ),
              Expanded(
                child: TabBarView(
                  controller: _tabs,
                  children: [
                    RefreshIndicator(
                      onRefresh: _refresh,
                      child: ListView(
                        padding:
                            const EdgeInsets.fromLTRB(16, 8, 16, 100),
                        children: [
                          if (pending.isEmpty)
                            const Card(
                              child: Padding(
                                padding: EdgeInsets.all(18),
                                child: Text(
                                  'No pending money. Fully repaid people automatically move to Cleared.',
                                ),
                              ),
                            )
                          else
                            ...pending.map(
                              (raw) => _pendingCard(
                                Map<String, dynamic>.from(raw as Map),
                              ),
                            ),
                        ],
                      ),
                    ),
                    RefreshIndicator(
                      onRefresh: _refresh,
                      child: ListView(
                        padding:
                            const EdgeInsets.fromLTRB(16, 8, 16, 100),
                        children: [
                          if (cleared.isEmpty)
                            const Card(
                              child: Padding(
                                padding: EdgeInsets.all(18),
                                child: Text(
                                  'No cleared records yet.',
                                ),
                              ),
                            )
                          else
                            ...cleared.map(
                              (raw) => _clearedCard(
                                Map<String, dynamic>.from(raw as Map),
                              ),
                            ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
