import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import 'finance_service.dart';

class AddTransactionScreen extends StatefulWidget {
  const AddTransactionScreen({
    super.key,
    required this.api,
    required this.initialType,
  });

  final ApiClient api;
  final String initialType;

  @override
  State<AddTransactionScreen> createState() => _AddTransactionScreenState();
}

class _AddTransactionScreenState extends State<AddTransactionScreen> {
  late final FinanceService _finance = FinanceService(widget.api);

  final _amount = TextEditingController();
  final _merchant = TextEditingController();
  final _note = TextEditingController();

  List<dynamic> _accounts = const [];
  List<dynamic> _categories = const [];
  String? _accountId;
  String? _categoryId;
  late String _type;
  DateTime _date = DateTime.now();
  bool _loading = true;
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _type = widget.initialType;
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
        _accountId = accounts.isNotEmpty ? accounts.first['id'].toString() : null;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _error = 'Unable to load accounts and categories.';
        _loading = false;
      });
    }
  }

  List<dynamic> get _filteredCategories => _categories.where((category) {
        return category['transaction_type'].toString() == _type;
      }).toList();

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      firstDate: DateTime(2000),
      lastDate: DateTime.now().add(const Duration(days: 365)),
      initialDate: _date,
    );
    if (picked != null) setState(() => _date = picked);
  }

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
      await _finance.createTransaction(
        accountId: _accountId!,
        categoryId: _categoryId,
        transactionType: _type,
        amount: amount,
        occurredOn: _date,
        merchant: _merchant.text,
        note: _note.text,
      );
      if (!mounted) return;

      FocusManager.instance.primaryFocus?.unfocus();
      Navigator.of(context).pop(true);
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Unable to save transaction.');
      }
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
    final dateText =
        _date.day.toString().padLeft(2, '0') +
        '/' +
        _date.month.toString().padLeft(2, '0') +
        '/' +
        _date.year.toString();

    return Scaffold(
      appBar: AppBar(
        title: Text(_type == 'income' ? 'Add income' : 'Add expense'),
      ),
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
                const SizedBox(height: 20),
                if (_accounts.isEmpty)
                  const Card(
                    child: Padding(
                      padding: EdgeInsets.all(16),
                      child: Text('Create an account before adding a transaction.'),
                    ),
                  )
                else
                  DropdownButtonFormField<String>(
                    value: _accountId,
                    decoration: const InputDecoration(
                      labelText: 'Account',
                      border: OutlineInputBorder(),
                    ),
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
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                    labelText: 'Amount',
                    prefixText: '₹ ',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<String?>(
                  value: _categoryId,
                  decoration: const InputDecoration(
                    labelText: 'Category',
                    border: OutlineInputBorder(),
                  ),
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
                  subtitle: Text(dateText),
                  trailing: const Icon(Icons.calendar_today_outlined),
                  onTap: _pickDate,
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: _merchant,
                  decoration: const InputDecoration(
                    labelText: 'Merchant / source',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _note,
                  minLines: 2,
                  maxLines: 4,
                  decoration: const InputDecoration(
                    labelText: 'Note',
                    border: OutlineInputBorder(),
                  ),
                ),
                if (_error != null) ...[
                  const SizedBox(height: 16),
                  Text(
                    _error!,
                    style: TextStyle(color: Theme.of(context).colorScheme.error),
                  ),
                ],
                const SizedBox(height: 24),
                FilledButton(
                  onPressed: _saving || _accounts.isEmpty ? null : _save,
                  child: Text(_saving ? 'Saving...' : 'Save transaction'),
                ),
              ],
            ),
    );
  }
}
