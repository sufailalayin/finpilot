import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../ai/ai_screen.dart';
import '../auth/auth_screen.dart';
import '../dashboard/dashboard_screen.dart';
import '../planning/planning_screen.dart';
import '../profile/profile_screen.dart';
import '../subscription/pro_feature_gate.dart';
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

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _revision = widget.api.dataRevision.value;
    widget.api.dataRevision.addListener(_handleRevision);
    widget.api.sessionExpired.addListener(_handleSessionExpired);
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
    }
  }

  @override
  void dispose() {
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
          } else {
            setState(() => _index = value);
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
