import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../ai/ai_screen.dart';
import '../auth/auth_screen.dart';
import '../dashboard/dashboard_screen.dart';
import '../planning/planning_screen.dart';
import '../profile/profile_screen.dart';
import '../subscription/pro_feature_gate.dart';
import '../subscription/subscription_service.dart';
import '../transactions/transactions_screen.dart';

class AppShell extends StatefulWidget {
  const AppShell({super.key, required this.api});

  final ApiClient api;

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> with WidgetsBindingObserver {
  int _index = 0;
  late int _revision;
  late final SubscriptionService _subscriptions =
      SubscriptionService(widget.api);
  Timer? _entitlementTimer;
  String? _entitlementFingerprint;
  bool _syncingEntitlement = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _revision = widget.api.dataRevision.value;
    widget.api.dataRevision.addListener(_handleRevision);
    widget.api.sessionExpired.addListener(_handleSessionExpired);
    _syncEntitlement();
    _entitlementTimer = Timer.periodic(
      const Duration(seconds: 10),
      (_) => _syncEntitlement(),
    );
  }

  Future<void> _syncEntitlement() async {
    if (_syncingEntitlement) return;
    _syncingEntitlement = true;
    try {
      final status = await _subscriptions.status();
      final fingerprint = [
        status['plan_code'],
        status['status'],
        status['trial_ends_at'],
        status['paid_until'],
        status['provider'],
      ].join('|');

      if (_entitlementFingerprint == null) {
        _entitlementFingerprint = fingerprint;
      } else if (_entitlementFingerprint != fingerprint) {
        _entitlementFingerprint = fingerprint;
        widget.api.notifyDataChanged();
      }
    } catch (_) {
      // Normal network retry/session handling is managed by ApiClient.
    } finally {
      _syncingEntitlement = false;
    }
  }

  void _handleRevision() {
    if (!mounted) return;
    setState(() => _revision = widget.api.dataRevision.value);
  }

  void _handleSessionExpired() {
    if (!mounted || widget.api.sessionExpired.value != true) return;
    widget.api.sessionExpired.value = false;
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => AuthScreen(api: widget.api)),
      (_) => false,
    );
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      widget.api.notifyDataChanged();
      _syncEntitlement();
    }
  }

  @override
  void dispose() {
    _entitlementTimer?.cancel();
    widget.api.dataRevision.removeListener(_handleRevision);
    widget.api.sessionExpired.removeListener(_handleSessionExpired);
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final pages = [
      DashboardScreen(
        key: ValueKey('dashboard-$_revision'),
        api: widget.api,
      ),
      TransactionsScreen(
        key: ValueKey('transactions-$_revision'),
        api: widget.api,
      ),
      PlanningScreen(
        key: ValueKey('planning-$_revision'),
        api: widget.api,
      ),
      ProFeatureGate(
        key: ValueKey('ai-$_revision'),
        api: widget.api,
        featureCode: 'ai_copilot',
        child: AIScreen(api: widget.api),
      ),
      ProfileScreen(
        key: ValueKey('profile-$_revision'),
        api: widget.api,
      ),
    ];

    return Scaffold(
      body: IndexedStack(
        index: _index,
        children: pages,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (value) {
          if (value == _index) {
            widget.api.notifyDataChanged();
            _syncEntitlement();
          } else {
            setState(() => _index = value);
            _syncEntitlement();
          }
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home),
            label: 'Home',
          ),
          NavigationDestination(
            icon: Icon(Icons.receipt_long_outlined),
            selectedIcon: Icon(Icons.receipt_long),
            label: 'Activity',
          ),
          NavigationDestination(
            icon: Icon(Icons.track_changes_outlined),
            selectedIcon: Icon(Icons.track_changes),
            label: 'Plan',
          ),
          NavigationDestination(
            icon: Icon(Icons.auto_awesome_outlined),
            selectedIcon: Icon(Icons.auto_awesome),
            label: 'AI',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline),
            selectedIcon: Icon(Icons.person),
            label: 'Profile',
          ),
        ],
      ),
    );
  }
}
