import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/api_client.dart';
import 'automation_service.dart';

class SmartAlertsScreen extends StatefulWidget {
  const SmartAlertsScreen({super.key, required this.api});
  final ApiClient api;

  @override
  State<SmartAlertsScreen> createState() => _SmartAlertsScreenState();
}

class _SmartAlertsScreenState extends State<SmartAlertsScreen> {
  late final AutomationService _automation = AutomationService(widget.api);
  late Future<Map<String, dynamic>> _future;
  final _money = NumberFormat.currency(locale: 'en_IN', symbol: '₹', decimalDigits: 0);

  @override
  void initState() {
    super.initState();
    _future = _automation.alerts();
  }

  Future<void> _refresh() async {
    setState(() => _future = _automation.alerts());
    await _future;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Smart Alerts', style: TextStyle(fontWeight: FontWeight.w800))),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) return const Center(child: CircularProgressIndicator());
          if (snapshot.hasError || !snapshot.hasData) return Center(child: FilledButton.icon(onPressed: _refresh, icon: const Icon(Icons.refresh), label: const Text('Retry')));
          final data = snapshot.data!;
          final alerts = (data['alerts'] as List<dynamic>?) ?? const [];
          return RefreshIndicator(
            onRefresh: _refresh,
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
              children: [
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(color: Theme.of(context).colorScheme.primaryContainer, borderRadius: BorderRadius.circular(24)),
                  child: Row(children: [
                    Expanded(child: _Metric(label: 'Critical', value: data['critical_count'].toString())),
                    Expanded(child: _Metric(label: 'Warnings', value: data['warning_count'].toString())),
                    Expanded(child: _Metric(label: 'Info', value: data['info_count'].toString())),
                  ]),
                ),
                const SizedBox(height: 20),
                if (alerts.isEmpty)
                  const Card(child: Padding(padding: EdgeInsets.all(18), child: Text('No bill or subscription alerts right now.')))
                else
                  ...alerts.map((raw) {
                    final item = Map<String, dynamic>.from(raw as Map);
                    final severity = item['severity'].toString();
                    final icon = severity == 'critical' ? Icons.error_outline : severity == 'warning' ? Icons.warning_amber_rounded : Icons.info_outline;
                    return Card(
                      child: ListTile(
                        leading: CircleAvatar(child: Icon(icon)),
                        title: Text(item['title'].toString(), style: const TextStyle(fontWeight: FontWeight.w800)),
                        subtitle: Text(item['message'].toString() + (item['due_on'] == null ? '' : '\nDue: ' + item['due_on'].toString())),
                        trailing: item['amount'] == null ? null : Text(_money.format(double.tryParse(item['amount'].toString()) ?? 0), style: const TextStyle(fontWeight: FontWeight.w800)),
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

class _Metric extends StatelessWidget {
  const _Metric({required this.label, required this.value});
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      Text(value, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 24)),
      Text(label),
    ]);
  }
}