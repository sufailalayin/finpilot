import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/api_client.dart';
import '../finance/add_account_screen.dart';
import '../finance/finance_service.dart';
import 'transfer_screen.dart';

class AccountsScreen extends StatefulWidget {
  const AccountsScreen({super.key, required this.api});

  final ApiClient api;

  @override
  State<AccountsScreen> createState() => _AccountsScreenState();
}

class _AccountsScreenState extends State<AccountsScreen> {
  late final FinanceService _finance = FinanceService(widget.api);
  late Future<List<dynamic>> _future;
  late Future<Map<String, dynamic>> _netWorthFuture;

  final _money = NumberFormat.currency(
    locale: 'en_IN',
    symbol: '₹',
    decimalDigits: 0,
  );

  @override
  void initState() {
    super.initState();
    _future = _finance.listAccountBalances();
    _netWorthFuture = _finance.netWorthSummary();
  }

  Future<void> _refresh() async {
    setState(() {
      _future = _finance.listAccountBalances();
      _netWorthFuture = _finance.netWorthSummary();
    });
    await Future.wait([_future, _netWorthFuture]);
  }

  Future<void> _addAccount() async {
    final saved = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => AddAccountScreen(api: widget.api)),
    );
    if (saved == true) {
      await _refresh();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Account saved successfully.')),
      );
    }
  }

  Future<void> _transfer() async {
    final saved = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => TransferScreen(api: widget.api)),
    );
    if (saved == true) await _refresh();
  }

  Future<void> _editAccount(Map<String, dynamic> account) async {
    final name = TextEditingController(text: account['name'].toString());
    final opening = TextEditingController(
      text: account['opening_balance'].toString(),
    );
    String type = account['account_type'].toString();

    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setLocal) => AlertDialog(
          title: const Text('Edit account'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: name,
                decoration: const InputDecoration(labelText: 'Account name'),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: type,
                decoration: const InputDecoration(labelText: 'Account type'),
                items: const [
                  DropdownMenuItem(value: 'bank', child: Text('Bank')),
                  DropdownMenuItem(value: 'cash', child: Text('Cash')),
                  DropdownMenuItem(value: 'card', child: Text('Card')),
                  DropdownMenuItem(value: 'wallet', child: Text('Wallet')),
                  DropdownMenuItem(value: 'other', child: Text('Other')),
                ],
                onChanged: (value) {
                  if (value != null) setLocal(() => type = value);
                },
              ),
              const SizedBox(height: 12),
              TextField(
                controller: opening,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(
                  labelText: 'Opening balance',
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
                  opening.text.trim().replaceAll(',', ''),
                );
                if (name.text.trim().isEmpty || value == null) return;
                await _finance.updateAccount(
                  accountId: account['id'].toString(),
                  name: name.text,
                  accountType: type,
                  openingBalance: value,
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
      opening.dispose();
    });
    if (saved == true) await _refresh();
  }

  Future<void> _deleteAccount(Map<String, dynamic> account) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete account?'),
        content: const Text(
          'Only empty accounts can be deleted. Accounts with transactions are protected.',
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

    try {
      await _finance.deleteAccount(account['id'].toString());
      await _refresh();
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('This account has transactions and cannot be deleted.'),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Accounts & Net Worth',
          style: TextStyle(fontWeight: FontWeight.w800),
        ),
      ),
      body: FutureBuilder<List<dynamic>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(
              child: FilledButton.icon(
                onPressed: _refresh,
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
              ),
            );
          }

          final accounts = snapshot.data ?? const [];

          return FutureBuilder<Map<String, dynamic>>(
            future: _netWorthFuture,
            builder: (context, worthSnapshot) {
              if (worthSnapshot.connectionState != ConnectionState.done) {
                return const Center(child: CircularProgressIndicator());
              }

              final worth = worthSnapshot.data ?? const <String, dynamic>{};
              final netWorth =
                  double.tryParse(worth['net_worth']?.toString() ?? '0') ?? 0;
              final accountAssets =
                  double.tryParse(worth['account_assets']?.toString() ?? '0') ??
                      0;
              final investmentAssets = double.tryParse(
                    worth['investment_assets']?.toString() ?? '0',
                  ) ??
                  0;
              final liabilities =
                  double.tryParse(worth['liabilities']?.toString() ?? '0') ?? 0;

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
                            'NET WORTH',
                            style: TextStyle(
                              fontWeight: FontWeight.w800,
                              letterSpacing: 1,
                              fontSize: 12,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            _money.format(netWorth),
                            style: const TextStyle(
                              fontWeight: FontWeight.w900,
                              fontSize: 32,
                            ),
                          ),
                          const SizedBox(height: 10),
                          Text(
                            'Accounts ' +
                                _money.format(accountAssets) +
                                ' • Investments ' +
                                _money.format(investmentAssets) +
                                ' • Debt ' +
                                _money.format(liabilities),
                          ),
                        ],
                      ),
                    ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: FilledButton.tonalIcon(
                        onPressed: _addAccount,
                        icon: const Icon(Icons.add),
                        label: const Text('Add account'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: FilledButton.tonalIcon(
                        onPressed: accounts.length >= 2 ? _transfer : null,
                        icon: const Icon(Icons.swap_horiz),
                        label: const Text('Transfer'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                Text(
                  'Your accounts',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
                const SizedBox(height: 10),
                if (accounts.isEmpty)
                  const Card(
                    child: Padding(
                      padding: EdgeInsets.all(20),
                      child: Text('Add your first bank, cash or wallet account.'),
                    ),
                  )
                else
                  ...accounts.map((account) {
                    final current = double.tryParse(
                          account['current_balance'].toString(),
                        ) ??
                        0;
                    final opening = double.tryParse(
                          account['opening_balance'].toString(),
                        ) ??
                        0;
                    final isCard = account['account_type'].toString() == 'card';
                    final availableCredit = double.tryParse(
                          account['available_credit']?.toString() ?? '',
                        );
                    final utilization = double.tryParse(
                          account['utilization_pct']?.toString() ?? '',
                        );
                    final last4 = account['card_last4']?.toString();

                    return Card(
                      child: ListTile(
                        leading: const CircleAvatar(
                          child: Icon(Icons.account_balance_wallet_outlined),
                        ),
                        title: Text(
                          account['name'].toString(),
                          style: const TextStyle(fontWeight: FontWeight.w700),
                        ),
                        subtitle: Text(
                          isCard
                              ? [
                                  if (last4 != null && last4.isNotEmpty)
                                    '•••• ' + last4,
                                  'Outstanding ' + _money.format(current),
                                  if (availableCredit != null)
                                    'Available ' + _money.format(availableCredit),
                                  if (utilization != null)
                                    utilization.toStringAsFixed(0) + '% used',
                                ].join(' • ')
                              : account['account_type'].toString() +
                                  ' • Opening ' +
                                  _money.format(opening),
                        ),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            ConstrainedBox(
                              constraints: const BoxConstraints(maxWidth: 110),
                              child: Text(
                                isCard
                                    ? _money.format(current) + ' due'
                                    : _money.format(current),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(
                                  fontWeight: FontWeight.w900,
                                  fontSize: 16,
                                ),
                              ),
                            ),
                            PopupMenuButton<String>(
                              padding: EdgeInsets.zero,
                              constraints: const BoxConstraints(
                                minWidth: 40,
                                minHeight: 40,
                              ),
                              onSelected: (action) {
                                if (action == 'edit') {
                                  _editAccount(
                                    Map<String, dynamic>.from(account as Map),
                                  );
                                } else if (action == 'delete') {
                                  _deleteAccount(
                                    Map<String, dynamic>.from(account as Map),
                                  );
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
                    );
                  }),
                  ],
                ),
              );
            },
          );
        },
      ),
    );
  }
}
