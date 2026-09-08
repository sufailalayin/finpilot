import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import 'paywall_screen.dart';
import 'subscription_service.dart';

class ProFeatureGate extends StatefulWidget {
  const ProFeatureGate({
    super.key,
    required this.api,
    required this.featureCode,
    required this.child,
  });

  final ApiClient api;
  final String featureCode;
  final Widget child;

  @override
  State<ProFeatureGate> createState() => _ProFeatureGateState();
}

class _ProFeatureGateState extends State<ProFeatureGate> {
  late final SubscriptionService _subscriptions =
      SubscriptionService(widget.api);
  late Future<bool> _access;

  @override
  void initState() {
    super.initState();
    _access = _hasAccess();
  }

  Future<bool> _hasAccess() async {
    final result = await _subscriptions.features();
    final features = (result['features'] as List<dynamic>?) ?? const [];
    for (final raw in features) {
      final item = Map<String, dynamic>.from(raw as Map);
      if (item['code']?.toString() == widget.featureCode) {
        return item['included'] == true;
      }
    }
    return false;
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<bool>(
      future: _access,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }
        if (snapshot.data == true) return widget.child;
        return PaywallScreen(api: widget.api);
      },
    );
  }
}
