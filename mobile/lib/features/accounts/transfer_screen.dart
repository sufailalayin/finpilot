import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../finance/finance_service.dart';

class TransferScreen extends StatefulWidget {
  const TransferScreen({super.key, required this.api});

  final ApiClient api;

  @override
  State<TransferScreen> createState() => _TransferScreenState();
}

class _TransferScreenState extends State<TransferScreen> {
  late final FinanceService _finance = FinanceService(widget.api);
  final _amount = TextEditingController();
  final _note = TextEditingController();

  List<dynamic> _accounts = const [];
  String? _from;
  String? _to;
  DateTime _date = DateTime.now();
  bool _loading = true;
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final accounts = await _finance.listAccounts();
      if (!mounted) return;
      setState(() {
        _accounts = accounts;
        if (accounts.length >= 2) {
          _from = accounts[0]['id'].toString();
          _to = accounts[1]['id'].toString();
        }
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _error = 'Unable to load accounts.';
        _loading = false;
      });
    }
  }

  Future<void> _save() async {
    final amount = double.tryParse(_amount.text.trim().replaceAll(',', ''));
    if (_from == null ||
        _to == null ||
        _from == _to ||
        amount == null ||
        amount <= 0) {
      setState(
        () => _error = 'Select two different accounts and a valid amount.',
      );
      return;
    }

    setState(() {
      _saving = true;
      _error = null;
    });

    try {
      await _finance.createTransfer(
        fromAccountId: _from!,
        toAccountId: _to!,
        amount: amount,
        occurredOn: _date,
        note: _note.text,
      );
      if (!mounted) return;
      Navigator.of(context).pop(true);
    } catch (_) {
      if (!mounted) return;
      setState(() => _error = 'Unable to complete transfer.');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  void dispose() {
    _amount.dispose();
    _note.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Transfer money')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(24),
              children: [
                DropdownButtonFormField<String>(
                  initialValue: _from,
                  decoration: const InputDecoration(labelText: 'From account'),
                  items: _accounts
                      .map(
                        (a) => DropdownMenuItem<String>(
                          value: a['id'].toString(),
                          child: Text(a['name'].toString()),
                        ),
                      )
                      .toList(),
                  onChanged: (value) => setState(() => _from = value),
                ),
                const SizedBox(height: 16),
                DropdownButtonFormField<String>(
                  initialValue: _to,
                  decoration: const InputDecoration(labelText: 'To account'),
                  items: _accounts
                      .map(
                        (a) => DropdownMenuItem<String>(
                          value: a['id'].toString(),
                          child: Text(a['name'].toString()),
                        ),
                      )
                      .toList(),
                  onChanged: (value) => setState(() => _to = value),
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
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Transfer date'),
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
                  onPressed: _saving || _accounts.length < 2 ? null : _save,
                  child: Text(_saving ? 'Transferring...' : 'Transfer money'),
                ),
              ],
            ),
    );
  }
}
