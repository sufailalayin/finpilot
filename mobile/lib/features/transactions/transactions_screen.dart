import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/api_client.dart';
import '../finance/add_transaction_screen.dart';
import '../finance/finance_service.dart';

class TransactionsScreen extends StatefulWidget {
  const TransactionsScreen({super.key, required this.api});

  final ApiClient api;

  @override
  State<TransactionsScreen> createState() => _TransactionsScreenState();
}

class _TransactionsScreenState extends State<TransactionsScreen> {
  late final FinanceService _finance = FinanceService(widget.api);
  late Future<List<dynamic>> _future;

  final _money = NumberFormat.currency(
    locale: 'en_IN',
    symbol: '₹',
    decimalDigits: 0,
  );

  String _filter = 'all';
  String _query = '';

  @override
  void initState() {
    super.initState();
    _future = _finance.listTransactions();
  }

  Future<void> _refresh() async {
    setState(() => _future = _finance.listTransactions());
    await _future;
  }

  Future<void> _add(String type) async {
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Transactions',
          style: TextStyle(fontWeight: FontWeight.w800),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _add('expense'),
        icon: const Icon(Icons.add),
        label: const Text('Add'),
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

          final all = snapshot.data ?? const [];
          final filtered = _filter == 'all'
              ? all
              : all
                  .where(
                    (item) =>
                        item['transaction_type']?.toString() == _filter,
                  )
                  .toList();
          final items = filtered.where((item) {
            if (_query.trim().isEmpty) return true;
            final q = _query.trim().toLowerCase();
            return (item['merchant']?.toString().toLowerCase().contains(q) ?? false) ||
                (item['note']?.toString().toLowerCase().contains(q) ?? false) ||
                item['amount'].toString().contains(q);
          }).toList();

          return RefreshIndicator(
            onRefresh: _refresh,
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 100),
              children: [
                TextField(
                  decoration: const InputDecoration(
                    hintText: 'Search transactions',
                    prefixIcon: Icon(Icons.search),
                  ),
                  onChanged: (value) => setState(() => _query = value),
                ),
                const SizedBox(height: 14),
                SegmentedButton<String>(
                  segments: const [
                    ButtonSegment(value: 'all', label: Text('All')),
                    ButtonSegment(value: 'income', label: Text('Income')),
                    ButtonSegment(value: 'expense', label: Text('Expense')),
                  ],
                  selected: {_filter},
                  onSelectionChanged: (selection) {
                    setState(() => _filter = selection.first);
                  },
                ),
                const SizedBox(height: 18),
                Row(
                  children: [
                    Expanded(
                      child: FilledButton.tonalIcon(
                        onPressed: () => _add('income'),
                        icon: const Icon(Icons.south_west_rounded),
                        label: const Text('Income'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: FilledButton.tonalIcon(
                        onPressed: () => _add('expense'),
                        icon: const Icon(Icons.north_east_rounded),
                        label: const Text('Expense'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 22),
                if (items.isEmpty)
                  Container(
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.surface,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: const Text(
                      'No transactions yet. Add your first income or expense.',
                    ),
                  )
                else
                  ...items.map((item) {
                    final type =
                        item['transaction_type']?.toString() ?? 'expense';
                    final amount =
                        double.tryParse(item['amount'].toString()) ?? 0;
                    final title = item['merchant']?.toString().trim();

                    return Container(
                      margin: const EdgeInsets.only(bottom: 10),
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: Theme.of(context).colorScheme.surface,
                        borderRadius: BorderRadius.circular(18),
                        border: Border.all(
                          color: Theme.of(context)
                              .colorScheme
                              .outlineVariant,
                        ),
                      ),
                      child: Row(
                        children: [
                          CircleAvatar(
                            child: Icon(
                              type == 'income'
                                  ? Icons.south_west_rounded
                                  : Icons.north_east_rounded,
                              size: 18,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  title == null || title.isEmpty
                                      ? (type == 'income'
                                          ? 'Income'
                                          : 'Expense')
                                      : title,
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                                const SizedBox(height: 3),
                                Text(
                                  item['occurred_on']?.toString() ?? '',
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: Theme.of(context)
                                        .colorScheme
                                        .onSurfaceVariant,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              Text(
                                (type == 'income' ? '+ ' : '- ') +
                                    _money.format(amount),
                                style: const TextStyle(
                                  fontWeight: FontWeight.w800,
                                  fontSize: 15,
                                ),
                              ),
                              PopupMenuButton<String>(
                                tooltip: 'Transaction actions',
                                onSelected: (action) async {
                                  if (action == 'delete') {
                                    final confirmed = await showDialog<bool>(
                                      context: context,
                                      builder: (context) => AlertDialog(
                                        title: const Text('Delete transaction?'),
                                        content: const Text(
                                          'This will permanently remove this transaction.',
                                        ),
                                        actions: [
                                          TextButton(
                                            onPressed: () =>
                                                Navigator.pop(context, false),
                                            child: const Text('Cancel'),
                                          ),
                                          FilledButton(
                                            onPressed: () =>
                                                Navigator.pop(context, true),
                                            child: const Text('Delete'),
                                          ),
                                        ],
                                      ),
                                    );
                                    if (confirmed == true) {
                                      await _finance.deleteTransaction(
                                        item['id'].toString(),
                                      );
                                      await _refresh();
                                    }
                                  }
                                },
                                itemBuilder: (context) => const [
                                  PopupMenuItem(
                                    value: 'delete',
                                    child: Text('Delete'),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ],
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
