import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/api_client.dart';
import '../auth/auth_screen.dart';
import '../auth/auth_service.dart';
import '../finance/add_account_screen.dart';
import '../finance/add_transaction_screen.dart';
import 'dashboard_service.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key, required this.api});

  final ApiClient api;

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  late final DashboardService _dashboard = DashboardService(widget.api);
  late final AuthService _auth = AuthService(widget.api);
  late Future<DashboardData> _future;

  final _money = NumberFormat.currency(
    locale: 'en_IN',
    symbol: '₹',
    decimalDigits: 2,
  );

  @override
  void initState() {
    super.initState();
    _future = _dashboard.load();
  }

  Future<void> _refresh() async {
    setState(() => _future = _dashboard.load());
    await _future;
  }

  Future<void> _openAccount() async {
    final created = await Navigator.of(context).push<bool>(
      MaterialPageRoute(builder: (_) => AddAccountScreen(api: widget.api)),
    );
    if (created == true) await _refresh();
  }

  Future<void> _openTransaction(String type) async {
    final created = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (_) => AddTransactionScreen(
          api: widget.api,
          initialType: type,
        ),
      ),
    );
    if (created == true) await _refresh();
  }

  Future<void> _logout() async {
    await _auth.logout();
    if (!mounted) return;
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => AuthScreen(api: widget.api)),
      (_) => false,
    );
  }

  Widget _metric(String label, double value) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label),
              const SizedBox(height: 8),
              Text(
                label == 'Transactions'
                    ? value.toInt().toString()
                    : _money.format(value),
                style: const TextStyle(
                  fontWeight: FontWeight.w700,
                  fontSize: 18,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('FinPilot'),
        actions: [
          IconButton(
            onPressed: _logout,
            icon: const Icon(Icons.logout),
            tooltip: 'Sign out',
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _openTransaction('expense'),
        icon: const Icon(Icons.add),
        label: const Text('Add transaction'),
      ),
      body: FutureBuilder<DashboardData>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError || !snapshot.hasData) {
            return Center(
              child: FilledButton(
                onPressed: _refresh,
                child: const Text('Retry dashboard'),
              ),
            );
          }

          final data = snapshot.data!;

          return RefreshIndicator(
            onRefresh: _refresh,
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Text(
                  'Total balance',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                Text(
                  _money.format(data.totalBalance),
                  style: Theme.of(context)
                      .textTheme
                      .displaySmall
                      ?.copyWith(fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 20),
                Row(
                  children: [
                    _metric('Income', data.monthIncome),
                    _metric('Expenses', data.monthExpense),
                  ],
                ),
                Row(
                  children: [
                    _metric('Net', data.monthNet),
                    _metric('Transactions', data.transactionCount.toDouble()),
                  ],
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: _openAccount,
                        icon: const Icon(Icons.account_balance_wallet_outlined),
                        label: const Text('Add account'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () => _openTransaction('income'),
                        icon: const Icon(Icons.south_west),
                        label: const Text('Add income'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                Text(
                  'Accounts',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 8),
                if (data.accounts.isEmpty)
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('No accounts yet.'),
                          const SizedBox(height: 12),
                          FilledButton.tonal(
                            onPressed: _openAccount,
                            child: const Text('Create your first account'),
                          ),
                        ],
                      ),
                    ),
                  )
                else
                  ...data.accounts.map(
                    (account) => Card(
                      child: ListTile(
                        leading: const CircleAvatar(
                          child: Icon(Icons.account_balance_wallet_outlined),
                        ),
                        title: Text(account['account_name'].toString()),
                        subtitle: Text(account['currency'].toString()),
                        trailing: Text(
                          _money.format(
                            double.parse(account['balance'].toString()),
                          ),
                        ),
                      ),
                    ),
                  ),
                const SizedBox(height: 20),
                Text(
                  'Recent activity',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 8),
                if (data.recentTransactions.isEmpty)
                  const Card(
                    child: Padding(
                      padding: EdgeInsets.all(20),
                      child: Text('Your recent transactions will appear here.'),
                    ),
                  )
                else
                  ...data.recentTransactions.map(
                    (transaction) => ListTile(
                      title: Text(
                        transaction['merchant']?.toString() ??
                            transaction['transaction_type'].toString(),
                      ),
                      subtitle: Text(transaction['occurred_on'].toString()),
                      trailing: Text(
                        _money.format(
                          double.parse(transaction['amount'].toString()),
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
