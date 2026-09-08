import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../finance/finance_service.dart';

class EditTransactionScreen extends StatefulWidget {
  const EditTransactionScreen({
    super.key,
    required this.api,
    required this.transaction,
  });

  final ApiClient api;
  final Map<String, dynamic> transaction;

  @override
  State<EditTransactionScreen> createState() => _EditTransactionScreenState();
}

class _EditTransactionScreenState extends State<EditTransactionScreen> {
  late final FinanceService _finance = FinanceService(widget.api);
  late final TextEditingController _amount;
  late final TextEditingController _merchant;
  late final TextEditingController _note;

  List<dynamic> _accounts = const [];
  List<dynamic> _categories = const [];
  String? _accountId;
  String? _categoryId;
  late String _type;
  late DateTime _date;
  bool _loading = true;
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    final tx = widget.transaction;
    _amount = TextEditingController(text: tx['amount'].toString());
    _merchant = TextEditingController(text: tx['merchant']?.toString() ?? '');
    _note = TextEditingController(text: tx['note']?.toString() ?? '');
    _type = tx['transaction_type']?.toString() ?? 'expense';
    _date =
        DateTime.tryParse(tx['occurred_on']?.toString() ?? '') ?? DateTime.now();
    _accountId = tx['account_id']?.toString();
    _categoryId = tx['category_id']?.toString();
    _load();
  }

  Future<void> _load() async {
    try {
      final accounts = await _finance.listAccounts();
      var categories = await _finance.listCategories();
      if (categories.isEmpty) {
        categories = await _finance.bootstrapCategories();
      }
      if (!mounted) return;
      setState(() {
        _accounts = accounts;
        _categories = categories;
        if (_accountId == null && accounts.isNotEmpty) {
          _accountId = accounts.first['id'].toString();
        }
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _error = 'Unable to load transaction details.';
        _loading = false;
      });
    }
  }

  List<dynamic> get _filteredCategories => _categories.where((category) {
        return category['transaction_type'].toString() == _type;
      }).toList();

  Future<void> _save() async {
    final amount = double.tryParse(_amount.text.trim().replaceAll(',', ''));
    if (_accountId == null || amount == null || amount <= 0) {
      setState(() => _error = 'Select an account and enter a valid amount.');
      return;
    }

    setState(() {
      _saving = true;
      _error = null;
    });

    try {
      await _finance.updateTransaction(
        transactionId: widget.transaction['id'].toString(),
        accountId: _accountId!,
        categoryId: _categoryId,
        transactionType: _type,
        amount: amount,
        occurredOn: _date,
        merchant: _merchant.text,
        note: _note.text,
      );
      if (!mounted) return;
      Navigator.of(context).pop(true);
    } catch (_) {
      if (!mounted) return;
      setState(() => _error = 'Unable to update transaction.');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  void dispose() {
    _amount.dispose();
    _merchant.dispose();
    _note.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Edit transaction')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(24),
              children: [
                SegmentedButton<String>(
                  segments: const [
                    ButtonSegment(value: 'expense', label: Text('Expense')),
                    ButtonSegment(value: 'income', label: Text('Income')),
                  ],
                  selected: {_type},
                  onSelectionChanged: (selection) {
                    setState(() {
                      _type = selection.first;
                      _categoryId = null;
                    });
                  },
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<String>(
                  initialValue: _accountId,
                  decoration: const InputDecoration(labelText: 'Account'),
                  items: _accounts
                      .map(
                        (account) => DropdownMenuItem<String>(
                          value: account['id'].toString(),
                          child: Text(account['name'].toString()),
                        ),
                      )
                      .toList(),
                  onChanged: (value) => setState(() => _accountId = value),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _amount,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                    labelText: 'Amount',
                    prefixText: '₹ ',
                  ),
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<String?>(
                  initialValue: _categoryId,
                  decoration: const InputDecoration(labelText: 'Category'),
                  items: [
                    const DropdownMenuItem<String?>(
                      value: null,
                      child: Text('No category'),
                    ),
                    ..._filteredCategories.map(
                      (category) => DropdownMenuItem<String?>(
                        value: category['id'].toString(),
                        child: Text(category['name'].toString()),
                      ),
                    ),
                  ],
                  onChanged: (value) => setState(() => _categoryId = value),
                ),
                const SizedBox(height: 16),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Date'),
                  subtitle: Text(
                    _date.day.toString().padLeft(2, '0') +
                        '/' +
                        _date.month.toString().padLeft(2, '0') +
                        '/' +
                        _date.year.toString(),
                  ),
                  trailing: const Icon(Icons.calendar_today_outlined),
                  onTap: () async {
                    final picked = await showDatePicker(
                      context: context,
                      firstDate: DateTime(2000),
                      lastDate: DateTime.now().add(const Duration(days: 365)),
                      initialDate: _date,
                    );
                    if (picked != null) setState(() => _date = picked);
                  },
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: _merchant,
                  decoration: const InputDecoration(
                    labelText: 'Merchant / source',
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _note,
                  minLines: 2,
                  maxLines: 4,
                  decoration: const InputDecoration(labelText: 'Note'),
                ),
                if (_error != null) ...[
                  const SizedBox(height: 16),
                  Text(
                    _error!,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    ),
                  ),
                ],
                const SizedBox(height: 24),
                FilledButton(
                  onPressed: _saving ? null : _save,
                  child: Text(_saving ? 'Saving...' : 'Save changes'),
                ),
              ],
            ),
    );
  }
}
