import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import 'subscription_service.dart';

class PaywallScreen extends StatefulWidget {
  const PaywallScreen({super.key, required this.api});

  final ApiClient api;

  @override
  State<PaywallScreen> createState() => _PaywallScreenState();
}

class _PaywallScreenState extends State<PaywallScreen> {
  late final SubscriptionService _subscriptions = SubscriptionService(widget.api);
  bool _loading = true;
  Map<String, dynamic>? _status;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final status = await _subscriptions.status();
      if (!mounted) return;
      setState(() {
        _status = status;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final active = _status?['status']?.toString() ?? 'unknown';

    return Scaffold(
      appBar: AppBar(title: const Text('FinPilot Pro')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(24),
              children: [
                Text(
                  'FinPilot Pro',
                  style: Theme.of(context)
                      .textTheme
                      .displaySmall
                      ?.copyWith(fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 12),
                const Text(
                  'Unlock AI money insights, advanced planning, and premium finance tools.',
                ),
                const SizedBox(height: 24),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Text('Current status: ' + active),
                  ),
                ),
                const SizedBox(height: 20),
                const ListTile(
                  leading: Icon(Icons.auto_awesome_outlined),
                  title: Text('FinPilot AI'),
                  subtitle: Text('Personalized insights from your finance data'),
                ),
                const ListTile(
                  leading: Icon(Icons.track_changes_outlined),
                  title: Text('Advanced goals & budgets'),
                  subtitle: Text('Plan and track your financial targets'),
                ),
                const ListTile(
                  leading: Icon(Icons.insights_outlined),
                  title: Text('Advanced reports'),
                  subtitle: Text('Understand where your money is going'),
                ),
                const SizedBox(height: 24),
                FilledButton(
                  onPressed: null,
                  child: const Text('Monthly plan — coming after Play setup'),
                ),
                const SizedBox(height: 12),
                OutlinedButton(
                  onPressed: null,
                  child: const Text('Yearly plan — coming after Play setup'),
                ),
                const SizedBox(height: 20),
                const Text(
                  'Google Play Billing will be enabled after the app package and Play Console products are configured.',
                  textAlign: TextAlign.center,
                ),
              ],
            ),
    );
  }
}
