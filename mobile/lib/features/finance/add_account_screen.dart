import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import 'finance_service.dart';

class AddAccountScreen extends StatefulWidget {
  const AddAccountScreen({super.key, required this.api});

  final ApiClient api;

  @override
  State<AddAccountScreen> createState() => _AddAccountScreenState();
}

class _AddAccountScreenState extends State<AddAccountScreen> {
  late final FinanceService _finance = FinanceService(widget.api);
  final _name = TextEditingController();
  final _openingBalance = TextEditingController(text: '0');

  String _accountType = 'bank';
  bool _saving = false;
  String? _error;

  Future<void> _save() async {
    final name = _name.text.trim();
    final opening = double.tryParse(_openingBalance.text.trim());

    if (name.isEmpty || opening == null) {
      setState(() => _error = 'Enter a valid account name and balance.');
      return;
    }

    setState(() {
      _saving = true;
      _error = null;
    });

    try {
      await _finance.createAccount(
        name: name,
        accountType: _accountType,
        openingBalance: opening,
      );
      if (!mounted) return;
      Navigator.of(context).pop(true);
    } catch (_) {
      setState(() => _error = 'Unable to create account.');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  void dispose() {
    _name.dispose();
    _openingBalance.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Add account')),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          TextField(
            controller: _name,
            textInputAction: TextInputAction.next,
            decoration: const InputDecoration(
              labelText: 'Account name',
              hintText: 'HDFC Bank, Cash, Wallet...',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          DropdownButtonFormField<String>(
            value: _accountType,
            decoration: const InputDecoration(
              labelText: 'Account type',
              border: OutlineInputBorder(),
            ),
            items: const [
              DropdownMenuItem(value: 'bank', child: Text('Bank')),
              DropdownMenuItem(value: 'cash', child: Text('Cash')),
              DropdownMenuItem(value: 'card', child: Text('Card')),
              DropdownMenuItem(value: 'wallet', child: Text('Wallet')),
              DropdownMenuItem(value: 'other', child: Text('Other')),
            ],
            onChanged: (value) {
              if (value != null) setState(() => _accountType = value);
            },
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _openingBalance,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(
              labelText: 'Opening balance',
              prefixText: '₹ ',
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
            onPressed: _saving ? null : _save,
            child: Text(_saving ? 'Saving...' : 'Create account'),
          ),
        ],
      ),
    );
  }
}
