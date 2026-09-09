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
  final _creditLimit = TextEditingController();
  final _cardLast4 = TextEditingController();
  final _statementDay = TextEditingController();
  final _paymentDueDay = TextEditingController();

  String _accountType = 'bank';
  bool _saving = false;
  String? _error;

  Future<void> _save() async {
    final name = _name.text.trim();
    final opening = double.tryParse(_openingBalance.text.trim().replaceAll(',', ''));
    final isCard = _accountType == 'card';
    final creditLimit = isCard
        ? double.tryParse(_creditLimit.text.trim().replaceAll(',', ''))
        : null;
    final statementDay = isCard ? int.tryParse(_statementDay.text.trim()) : null;
    final paymentDueDay = isCard ? int.tryParse(_paymentDueDay.text.trim()) : null;
    final cardLast4 = isCard ? _cardLast4.text.trim() : null;

    if (name.isEmpty || opening == null) {
      setState(() => _error = 'Enter a valid account name and balance.');
      return;
    }
    if (isCard &&
        (creditLimit == null ||
            creditLimit <= 0 ||
            cardLast4 == null ||
            !RegExp(r'^\d{4}
    setState(() {
      _saving = true;
      _error = null;
    });

    try {
      await _finance.createAccount(
        name: name,
        accountType: _accountType,
        openingBalance: opening,
        creditLimit: creditLimit,
        cardLast4: cardLast4,
        statementDay: statementDay,
        paymentDueDay: paymentDueDay,
      );
      if (!mounted) return;

      // Remove focus/keyboard dependencies before this route is disposed.
      FocusManager.instance.primaryFocus?.unfocus();

      // Let the parent route refresh and show any success feedback. Do not
      // access inherited widgets such as ScaffoldMessenger after popping
      // this route; doing so during disposal can trigger Flutter's
      // _dependents.isEmpty assertion on some Android devices.
      Navigator.of(context).pop(true);
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Unable to create account.');
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  void dispose() {
    _name.dispose();
    _openingBalance.dispose();
    _creditLimit.dispose();
    _cardLast4.dispose();
    _statementDay.dispose();
    _paymentDueDay.dispose();
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
          if (_accountType == 'card') ...[
            const SizedBox(height: 16),
            TextField(
              controller: _creditLimit,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(
                labelText: 'Credit limit',
                prefixText: '₹ ',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _cardLast4,
              keyboardType: TextInputType.number,
              maxLength: 4,
              decoration: const InputDecoration(
                labelText: 'Last 4 digits',
                hintText: '1234',
                border: OutlineInputBorder(),
                counterText: '',
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _statementDay,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                      labelText: 'Statement day',
                      hintText: '5',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextField(
                    controller: _paymentDueDay,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                      labelText: 'Due day',
                      hintText: '25',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
              ],
            ),
          ],
          const SizedBox(height: 16),
          TextField(
            controller: _openingBalance,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(
              labelText: _accountType == 'card'
                  ? 'Current outstanding'
                  : 'Opening balance',
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
).hasMatch(cardLast4) ||
            statementDay == null ||
            statementDay < 1 ||
            statementDay > 31 ||
            paymentDueDay == null ||
            paymentDueDay < 1 ||
            paymentDueDay > 31)) {
      setState(() => _error =
          'For cards, enter limit, last 4 digits, statement day and due day.');
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

      // Remove focus/keyboard dependencies before this route is disposed.
      FocusManager.instance.primaryFocus?.unfocus();

      // Let the parent route refresh and show any success feedback. Do not
      // access inherited widgets such as ScaffoldMessenger after popping
      // this route; doing so during disposal can trigger Flutter's
      // _dependents.isEmpty assertion on some Android devices.
      Navigator.of(context).pop(true);
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Unable to create account.');
      }
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
