import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/api_client.dart';
import 'asset_service.dart';

class AssetsScreen extends StatefulWidget {
  const AssetsScreen({super.key, required this.api});

  final ApiClient api;

  @override
  State<AssetsScreen> createState() => _AssetsScreenState();
}

class _AssetsScreenState extends State<AssetsScreen> {
  late final AssetService _assets = AssetService(widget.api);
  late Future<Map<String, dynamic>> _future;

  final _money = NumberFormat.currency(
    locale: 'en_IN',
    symbol: '₹',
    decimalDigits: 0,
  );

  @override
  void initState() {
    super.initState();
    _future = _assets.overview();
  }

  Future<void> _refresh() async {
    setState(() => _future = _assets.overview());
    await _future;
  }

  Future<void> _openForm([Map<String, dynamic>? item]) async {
    final name = TextEditingController(text: item?['name']?.toString() ?? '');
    final institution = TextEditingController(
      text: item?['institution']?.toString() ?? '',
    );
    final quantity = TextEditingController(
      text: item?['quantity']?.toString() ?? '1',
    );
    final cost = TextEditingController(
      text: item?['cost_basis']?.toString() ?? '0',
    );
    final value = TextEditingController(
      text: item?['current_value']?.toString() ?? '',
    );
    final notes = TextEditingController(
      text: item?['notes']?.toString() ?? '',
    );
    String type = item?['asset_type']?.toString() ?? 'gold';
    DateTime? maturity = item?['maturity_date'] == null
        ? null
        : DateTime.tryParse(item!['maturity_date'].toString());

    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setLocal) => AlertDialog(
          title: Text(item == null ? 'Add asset' : 'Edit asset'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: name,
                  decoration: const InputDecoration(labelText: 'Asset name'),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: type,
                  decoration: const InputDecoration(labelText: 'Asset type'),
                  items: const [
                    DropdownMenuItem(value: 'gold', child: Text('Gold')),
                    DropdownMenuItem(value: 'fd', child: Text('Fixed deposit')),
                    DropdownMenuItem(value: 'rd', child: Text('Recurring deposit')),
                    DropdownMenuItem(value: 'mutual_fund', child: Text('Mutual fund')),
                    DropdownMenuItem(value: 'stock', child: Text('Stock')),
                    DropdownMenuItem(value: 'property', child: Text('Property')),
                    DropdownMenuItem(value: 'vehicle', child: Text('Vehicle')),
                    DropdownMenuItem(value: 'crypto', child: Text('Crypto')),
                    DropdownMenuItem(value: 'business', child: Text('Business asset')),
                    DropdownMenuItem(value: 'other', child: Text('Other')),
                  ],
                  onChanged: (v) {
                    if (v != null) setLocal(() => type = v);
                  },
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: institution,
                  decoration: const InputDecoration(
                    labelText: 'Institution / platform',
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: quantity,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(labelText: 'Quantity'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: cost,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                    labelText: 'Total cost basis',
                    prefixText: '₹ ',
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: value,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                    labelText: 'Current value',
                    prefixText: '₹ ',
                  ),
                ),
                const SizedBox(height: 12),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Maturity date'),
                  subtitle: Text(
                    maturity == null
                        ? 'Optional'
                        : DateFormat('dd MMM yyyy').format(maturity!),
                  ),
                  onTap: () async {
                    final picked = await showDatePicker(
                      context: context,
                      firstDate: DateTime(2000),
                      lastDate: DateTime.now().add(
                        const Duration(days: 7300),
                      ),
                      initialDate: maturity ?? DateTime.now(),
                    );
                    if (picked != null) setLocal(() => maturity = picked);
                  },
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: notes,
                  minLines: 2,
                  maxLines: 4,
                  decoration: const InputDecoration(labelText: 'Notes'),
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
                final quantityValue = double.tryParse(
                      quantity.text.trim().replaceAll(',', ''),
                    ) ??
                    1;
                final costValue = double.tryParse(
                      cost.text.trim().replaceAll(',', ''),
                    ) ??
                    0;
                final currentValue = double.tryParse(
                  value.text.trim().replaceAll(',', ''),
                );
                if (name.text.trim().isEmpty ||
                    currentValue == null ||
                    currentValue <= 0 ||
                    quantityValue <= 0) {
                  return;
                }

                if (item == null) {
                  await _assets.createAsset(
                    name: name.text,
                    assetType: type,
                    institution: institution.text,
                    quantity: quantityValue,
                    costBasis: costValue,
                    currentValue: currentValue,
                    maturityDate: maturity,
                    notes: notes.text,
                  );
                } else {
                  await _assets.updateAsset(
                    assetId: item['id'].toString(),
                    name: name.text,
                    assetType: type,
                    institution: institution.text,
                    quantity: quantityValue,
                    costBasis: costValue,
                    currentValue: currentValue,
                    maturityDate: maturity,
                    notes: notes.text,
                  );
                }
                if (context.mounted) Navigator.pop(context, true);
              },
              child: const Text('Save'),
            ),
          ],
        ),
      ),
    );

    name.dispose();
    institution.dispose();
    quantity.dispose();
    cost.dispose();
    value.dispose();
    notes.dispose();

    if (saved == true) await _refresh();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Assets & Investments',
          style: TextStyle(fontWeight: FontWeight.w800),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _openForm(),
        icon: const Icon(Icons.add),
        label: const Text('Add asset'),
      ),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError || !snapshot.hasData) {
            return Center(
              child: FilledButton.icon(
                onPressed: _refresh,
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
              ),
            );
          }

          final data = snapshot.data!;
          final assets = (data['assets'] as List<dynamic>?) ?? const [];
          final allocation = (data['allocation'] as List<dynamic>?) ?? const [];
          final total = double.tryParse(data['total_assets'].toString()) ?? 0;
          final gain =
              double.tryParse(data['unrealized_gain'].toString()) ?? 0;
          final gainPct = data['unrealized_gain_pct'] == null
              ? null
              : double.tryParse(data['unrealized_gain_pct'].toString());

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
                        'TOTAL ASSET VALUE',
                        style: TextStyle(
                          fontWeight: FontWeight.w800,
                          letterSpacing: 1,
                          fontSize: 12,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        _money.format(total),
                        style: const TextStyle(
                          fontWeight: FontWeight.w900,
                          fontSize: 30,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Unrealized gain: ' +
                            _money.format(gain) +
                            (gainPct == null
                                ? ''
                                : ' (' + gainPct.toStringAsFixed(1) + '%)'),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),
                Text(
                  'Allocation',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
                const SizedBox(height: 10),
                if (allocation.isEmpty)
                  const Card(
                    child: Padding(
                      padding: EdgeInsets.all(16),
                      child: Text('Add assets to see allocation.'),
                    ),
                  )
                else
                  ...allocation.map((raw) {
                    final row = Map<String, dynamic>.from(raw as Map);
                    final pct =
                        double.tryParse(row['percentage'].toString()) ?? 0;
                    return Card(
                      child: Padding(
                        padding: const EdgeInsets.all(14),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Expanded(
                                  child: Text(
                                    row['asset_type'].toString(),
                                    style: const TextStyle(
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                ),
                                Text(
                                  _money.format(
                                    double.tryParse(
                                          row['value'].toString(),
                                        ) ??
                                        0,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            LinearProgressIndicator(
                              value: (pct / 100).clamp(0.0, 1.0),
                            ),
                            const SizedBox(height: 5),
                            Text(pct.toStringAsFixed(1) + '%'),
                          ],
                        ),
                      ),
                    );
                  }),
                const SizedBox(height: 24),
                Text(
                  'Holdings',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
                const SizedBox(height: 10),
                if (assets.isEmpty)
                  const Card(
                    child: Padding(
                      padding: EdgeInsets.all(18),
                      child: Text('No assets or investments recorded.'),
                    ),
                  )
                else
                  ...assets.map((raw) {
                    final item = Map<String, dynamic>.from(raw as Map);
                    final current =
                        double.tryParse(item['current_value'].toString()) ?? 0;
                    final cost =
                        double.tryParse(item['cost_basis'].toString()) ?? 0;
                    final itemGain = current - cost;

                    return Card(
                      child: ListTile(
                        leading: const CircleAvatar(
                          child: Icon(Icons.savings_outlined),
                        ),
                        title: Text(
                          item['name'].toString(),
                          style: const TextStyle(fontWeight: FontWeight.w700),
                        ),
                        subtitle: Text(
                          item['asset_type'].toString() +
                              ' • Gain ' +
                              _money.format(itemGain),
                        ),
                        trailing: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            Text(
                              _money.format(current),
                              style: const TextStyle(
                                fontWeight: FontWeight.w900,
                              ),
                            ),
                            PopupMenuButton<String>(
                              padding: EdgeInsets.zero,
                              onSelected: (action) async {
                                if (action == 'edit') {
                                  await _openForm(item);
                                } else if (action == 'delete') {
                                  await _assets.deleteAsset(
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
      ),
    );
  }
}
