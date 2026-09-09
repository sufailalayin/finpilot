import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/api_client.dart';
import '../../core/app_error_state.dart';
import '../accounts/accounts_screen.dart';
import '../accounts/transfer_screen.dart';
import '../auth/auth_screen.dart';
import '../auth/auth_service.dart';
import '../automation/smart_alerts_screen.dart';
import '../finance/add_transaction_screen.dart';
import '../insights/insights_screen.dart';
import '../planning/planning_screen.dart';
import '../subscription/paywall_screen.dart';
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
    decimalDigits: 0,
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

  Future<void> _openTransfer() async {
    final saved = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (_) => TransferScreen(api: widget.api),
      ),
    );
    if (saved == true) await _refresh();
  }

  Future<void> _openAccounts() async {
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => AccountsScreen(api: widget.api),
      ),
    );
    if (mounted) await _refresh();
  }

  Future<void> _showQuickEntrySheet() async {
    final action = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (sheetContext) {
        final media = MediaQuery.of(sheetContext);
        final maxHeight = media.size.height * 0.82;

        return ConstrainedBox(
          constraints: BoxConstraints(maxHeight: maxHeight),
          child: SingleChildScrollView(
            padding: EdgeInsets.fromLTRB(
              18,
              4,
              18,
              18 + media.viewPadding.bottom,
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Quick entry',
                  style: Theme.of(sheetContext).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w900,
                      ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Record money movement in a few taps.',
                  style: TextStyle(
                    color:
                        Theme.of(sheetContext).colorScheme.onSurfaceVariant,
                  ),
                ),
                const SizedBox(height: 16),
                ListTile(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 4),
                  leading: const CircleAvatar(
                    child: Icon(Icons.remove_circle_outline),
                  ),
                  title: const Text('Add expense'),
                  subtitle: const Text('Record spending'),
                  onTap: () => Navigator.pop(sheetContext, 'expense'),
                ),
                ListTile(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 4),
                  leading: const CircleAvatar(
                    child: Icon(Icons.add_circle_outline),
                  ),
                  title: const Text('Add income'),
                  subtitle: const Text('Record salary or other income'),
                  onTap: () => Navigator.pop(sheetContext, 'income'),
                ),
                ListTile(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 4),
                  leading: const CircleAvatar(
                    child: Icon(Icons.swap_horiz_rounded),
                  ),
                  title: const Text('Transfer money'),
                  subtitle: const Text('Move money between your accounts'),
                  onTap: () => Navigator.pop(sheetContext, 'transfer'),
                ),
                ListTile(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 4),
                  leading: const CircleAvatar(
                    child: Icon(Icons.account_balance_wallet_outlined),
                  ),
                  title: const Text('Manage accounts'),
                  subtitle: const Text(
                    'Bank, cash, card and wallet balances',
                  ),
                  onTap: () => Navigator.pop(sheetContext, 'accounts'),
                ),
              ],
            ),
          ),
        );
      },
    );

    if (!mounted || action == null) return;
    if (action == 'expense' || action == 'income') {
      await _openTransaction(action);
    } else if (action == 'transfer') {
      await _openTransfer();
    } else if (action == 'accounts') {
      await _openAccounts();
    }
  }

  Future<void> _logout() async {
    await _auth.logout();
    if (!mounted) return;
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => AuthScreen(api: widget.api)),
      (_) => false,
    );
  }

  Widget _summaryTile({
    required String label,
    required String value,
    required IconData icon,
  }) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surface,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(
            color: Theme.of(context).colorScheme.outlineVariant,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, size: 20),
            const SizedBox(height: 14),
            Text(
              value,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w800,
                height: 1.1,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                fontSize: 12,
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _quickAction({
    required String label,
    required IconData icon,
    required VoidCallback onTap,
    required double width,
  }) {
    return SizedBox(
      width: width,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(18),
        child: Container(
          constraints: const BoxConstraints(minHeight: 88),
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(18),
            color: Theme.of(context).colorScheme.surfaceContainerHighest,
            border: Border.all(
              color: Theme.of(context).colorScheme.outlineVariant,
            ),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 24),
              const SizedBox(height: 8),
              Text(
                label,
                textAlign: TextAlign.center,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _accountBalanceCard(Map<String, dynamic> account) {
    final balance = double.tryParse(account['balance'].toString()) ?? 0;
    final type = account['account_type']?.toString() ?? 'account';
    final prettyType = type.isEmpty
        ? 'Account'
        : type[0].toUpperCase() + type.substring(1);

    IconData icon = Icons.account_balance_wallet_outlined;
    if (type == 'bank') icon = Icons.account_balance_outlined;
    if (type == 'cash') icon = Icons.payments_outlined;
    if (type == 'card') icon = Icons.credit_card_outlined;
    if (type == 'wallet') icon = Icons.wallet_outlined;

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: Theme.of(context).colorScheme.outlineVariant,
        ),
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 21,
            backgroundColor: Theme.of(context).colorScheme.primaryContainer,
            child: Icon(icon, size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  account['account_name'].toString(),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 3),
                Text(
                  prettyType + ' • ' + account['currency'].toString(),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 12,
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 10),
          Flexible(
            child: Text(
              _money.format(balance),
              textAlign: TextAlign.right,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                fontWeight: FontWeight.w900,
                fontSize: 16,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _cashflowTrendCard(DashboardData data) {
    final points = data.cashflowTrend
        .map((raw) => Map<String, dynamic>.from(raw as Map))
        .toList();

    if (points.isEmpty) {
      return const SizedBox.shrink();
    }

    double valueOf(Map<String, dynamic> item, String key) =>
        double.tryParse(item[key]?.toString() ?? '0') ?? 0;

    double maxValue = 1;
    for (final item in points) {
      final income = valueOf(item, 'income').abs();
      final expense = valueOf(item, 'expenses').abs();
      if (income > maxValue) maxValue = income;
      if (expense > maxValue) maxValue = expense;
    }

    String shortMonth(String value) {
      final parsed = DateTime.tryParse(value + '-01');
      if (parsed == null) return value;
      return DateFormat('MMM').format(parsed);
    }

    IconData directionIcon = Icons.remove_rounded;
    if (data.cashflowDirection == 'improving') {
      directionIcon = Icons.trending_up_rounded;
    } else if (data.cashflowDirection == 'declining') {
      directionIcon = Icons.trending_down_rounded;
    }

    final latest = points.last;
    final latestNet = valueOf(latest, 'net');

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.stacked_bar_chart_outlined),
                const SizedBox(width: 10),
                const Expanded(
                  child: Text(
                    '4-month cash flow',
                    style: TextStyle(fontWeight: FontWeight.w800),
                  ),
                ),
                Icon(directionIcon, size: 20),
                const SizedBox(width: 4),
                Text(
                  data.cashflowDirection[0].toUpperCase() +
                      data.cashflowDirection.substring(1),
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              'Latest net: ' + _money.format(latestNet),
              style: TextStyle(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 16),
            ...points.map((item) {
              final income = valueOf(item, 'income');
              final expense = valueOf(item, 'expenses');
              final incomeRatio = (income.abs() / maxValue).clamp(0.0, 1.0);
              final expenseRatio = (expense.abs() / maxValue).clamp(0.0, 1.0);

              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Row(
                  children: [
                    SizedBox(
                      width: 36,
                      child: Text(
                        shortMonth(item['month'].toString()),
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Column(
                        children: [
                          ClipRRect(
                            borderRadius: BorderRadius.circular(8),
                            child: LinearProgressIndicator(
                              value: incomeRatio,
                              minHeight: 7,
                            ),
                          ),
                          const SizedBox(height: 5),
                          ClipRRect(
                            borderRadius: BorderRadius.circular(8),
                            child: LinearProgressIndicator(
                              value: expenseRatio,
                              minHeight: 7,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 10),
                    SizedBox(
                      width: 90,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text(
                            _money.format(income),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontSize: 11),
                          ),
                          Text(
                            _money.format(expense),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontSize: 11),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              );
            }),
            Text(
              'Top bar = income • Bottom bar = expenses',
              style: TextStyle(
                fontSize: 11,
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).colorScheme.surfaceContainerLowest,
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showQuickEntrySheet,
        icon: const Icon(Icons.add_rounded),
        label: const Text('Add'),
      ),
      appBar: AppBar(
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'FinPilot',
              style: TextStyle(fontWeight: FontWeight.w800),
            ),
            Text(
              'by Hastron Ventures',
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.w400),
            ),
          ],
        ),
        actions: [
          IconButton(
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(
                builder: (_) => PaywallScreen(api: widget.api),
              ),
            ),
            icon: const Icon(Icons.workspace_premium_outlined),
          ),
          PopupMenuButton<String>(
            onSelected: (value) {
              if (value == 'logout') _logout();
            },
            itemBuilder: (_) => const [
              PopupMenuItem(value: 'logout', child: Text('Sign out')),
            ],
          ),
        ],
      ),
      body: FutureBuilder<DashboardData>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError || !snapshot.hasData) {
            return AppErrorState(
              error: snapshot.error,
              onRetry: _refresh,
              title: 'Dashboard unavailable',
            );
          }

          final data = snapshot.data!;

          return RefreshIndicator(
            onRefresh: _refresh,
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
              children: [
                Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        Theme.of(context).colorScheme.primary,
                        Theme.of(context).colorScheme.primaryContainer,
                      ],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(26),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'NET WORTH',
                        style: TextStyle(
                          color: Theme.of(context).colorScheme.onPrimary,
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1.2,
                        ),
                      ),
                      const SizedBox(height: 10),
                      Text(
                        _money.format(data.netWorth),
                        style: TextStyle(
                          color: Theme.of(context).colorScheme.onPrimary,
                          fontSize: 34,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      const SizedBox(height: 18),
                      Row(
                        children: [
                          Icon(
                            data.monthNet >= 0
                                ? Icons.trending_up
                                : Icons.trending_down,
                            color: Theme.of(context).colorScheme.onPrimary,
                            size: 18,
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'This month: ' + _money.format(data.monthNet),
                              style: TextStyle(
                                color: Theme.of(context).colorScheme.onPrimary,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                          Text(
                            'Accounts ' + _money.format(data.totalBalance),
                            style: TextStyle(
                              color: Theme.of(context).colorScheme.onPrimary,
                              fontWeight: FontWeight.w600,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        'Your balances',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.w800,
                            ),
                      ),
                    ),
                    TextButton(
                      onPressed: _openAccounts,
                      child: const Text('Manage'),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                if (data.accounts.isEmpty)
                  InkWell(
                    onTap: _openAccounts,
                    borderRadius: BorderRadius.circular(18),
                    child: Container(
                      padding: const EdgeInsets.all(18),
                      decoration: BoxDecoration(
                        color: Theme.of(context).colorScheme.surface,
                        borderRadius: BorderRadius.circular(18),
                        border: Border.all(
                          color: Theme.of(context).colorScheme.outlineVariant,
                        ),
                      ),
                      child: const Row(
                        children: [
                          Icon(Icons.add_circle_outline),
                          SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              'Add your first bank, cash or wallet account.',
                            ),
                          ),
                        ],
                      ),
                    ),
                  )
                else
                  ...data.accounts.map(
                    (raw) => _accountBalanceCard(
                      Map<String, dynamic>.from(raw as Map),
                    ),
                  ),
                const SizedBox(height: 18),
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        'Fast entry',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.w800,
                            ),
                      ),
                    ),
                    Text(
                      'Daily shortcuts',
                      style: TextStyle(
                        fontSize: 12,
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                LayoutBuilder(
                  builder: (context, constraints) {
                    final itemWidth = (constraints.maxWidth - 10) / 2;
                    return Wrap(
                      spacing: 10,
                      runSpacing: 10,
                      children: [
                        _quickAction(
                          label: 'Add expense',
                          icon: Icons.remove_circle_outline,
                          onTap: () => _openTransaction('expense'),
                          width: itemWidth,
                        ),
                        _quickAction(
                          label: 'Add income',
                          icon: Icons.add_circle_outline,
                          onTap: () => _openTransaction('income'),
                          width: itemWidth,
                        ),
                        _quickAction(
                          label: 'Transfer',
                          icon: Icons.swap_horiz_rounded,
                          onTap: data.accounts.length >= 2
                              ? _openTransfer
                              : _openAccounts,
                          width: itemWidth,
                        ),
                        _quickAction(
                          label: 'Accounts',
                          icon: Icons.account_balance_wallet_outlined,
                          onTap: _openAccounts,
                          width: itemWidth,
                        ),
                        _quickAction(
                          label: 'Planning',
                          icon: Icons.flag_outlined,
                          onTap: () => Navigator.of(context).push(
                            MaterialPageRoute(
                              builder: (_) => PlanningScreen(api: widget.api),
                            ),
                          ),
                          width: itemWidth,
                        ),
                        _quickAction(
                          label: 'Insights',
                          icon: Icons.insights_outlined,
                          onTap: () => Navigator.of(context).push(
                            MaterialPageRoute(
                              builder: (_) => InsightsScreen(api: widget.api),
                            ),
                          ),
                          width: itemWidth,
                        ),
                      ],
                    );
                  },
                ),
                const SizedBox(height: 22),
                Text(
                  'Financial position',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    _summaryTile(
                      label: 'Health',
                      value: data.healthScoreAvailable
                          ? data.healthScore.toString() + '/100'
                          : 'Not enough data',
                      icon: Icons.favorite_outline,
                    ),
                    const SizedBox(width: 12),
                    _summaryTile(
                      label: 'Savings rate',
                      value: data.savingsRate.toStringAsFixed(1) + '%',
                      icon: Icons.savings_outlined,
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    _summaryTile(
                      label: 'Investments',
                      value: _money.format(data.investmentAssets),
                      icon: Icons.trending_up,
                    ),
                    const SizedBox(width: 12),
                    _summaryTile(
                      label: 'Liabilities',
                      value: _money.format(data.liabilities),
                      icon: Icons.account_balance_outlined,
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    _summaryTile(
                      label: 'Active budgets',
                      value: data.activeBudgetCount.toString(),
                      icon: Icons.pie_chart_outline,
                    ),
                    const SizedBox(width: 12),
                    _summaryTile(
                      label: 'Alerts',
                      value: data.upcomingAlertCount.toString(),
                      icon: Icons.notifications_active_outlined,
                    ),
                  ],
                ),
                if (data.goals.isNotEmpty ||
                    data.emergencyFund.isNotEmpty) ...[
                  const SizedBox(height: 20),
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          'Goals & safety net',
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.w800,
                              ),
                        ),
                      ),
                      TextButton(
                        onPressed: () => Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => PlanningScreen(api: widget.api),
                          ),
                        ),
                        child: const Text('Planning'),
                      ),
                    ],
                  ),
                  Builder(
                    builder: (context) {
                      final emergency = data.emergencyFund;
                      final months = double.tryParse(
                        emergency['months_covered']?.toString() ?? '',
                      );
                      final monthlyExpense = double.tryParse(
                            emergency['monthly_expense']?.toString() ?? '0',
                          ) ??
                          0;
                      final liquidBalance = double.tryParse(
                            emergency['liquid_balance']?.toString() ?? '0',
                          ) ??
                          0;

                      return Card(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  const Icon(Icons.shield_outlined),
                                  const SizedBox(width: 10),
                                  Expanded(
                                    child: Text(
                                      'Emergency fund',
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w800,
                                      ),
                                    ),
                                  ),
                                  Text(
                                    months == null
                                        ? 'Not enough data'
                                        : months.toStringAsFixed(1) + ' mo',
                                    style: const TextStyle(
                                      fontWeight: FontWeight.w900,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              Text(
                                months == null
                                    ? 'Add monthly expenses to calculate how many months your liquid balance can cover.'
                                    : 'Liquid balance ' +
                                        _money.format(liquidBalance) +
                                        ' against monthly expenses ' +
                                        _money.format(monthlyExpense) +
                                        '.',
                                maxLines: 3,
                                overflow: TextOverflow.ellipsis,
                              ),
                              if (months != null) ...[
                                const SizedBox(height: 10),
                                LinearProgressIndicator(
                                  value: (months / 6).clamp(0.0, 1.0),
                                ),
                                const SizedBox(height: 6),
                                Text(
                                  months >= 6
                                      ? 'Strong emergency buffer.'
                                      : months >= 3
                                          ? 'Good progress toward a 6-month buffer.'
                                          : 'Aim to build toward at least 3–6 months of expenses.',
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: Theme.of(context)
                                        .colorScheme
                                        .onSurfaceVariant,
                                  ),
                                ),
                              ],
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                  if (data.goals.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    ...data.goals.take(2).map((raw) {
                      final goal = Map<String, dynamic>.from(raw as Map);
                      final current = double.tryParse(
                            goal['current_amount'].toString(),
                          ) ??
                          0;
                      final target = double.tryParse(
                            goal['target_amount'].toString(),
                          ) ??
                          0;
                      final progress = double.tryParse(
                            goal['progress_pct'].toString(),
                          ) ??
                          0;

                      return Card(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  const Icon(Icons.flag_outlined),
                                  const SizedBox(width: 10),
                                  Expanded(
                                    child: Text(
                                      goal['name'].toString(),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w800,
                                      ),
                                    ),
                                  ),
                                  Text(
                                    progress.toStringAsFixed(0) + '%',
                                    style: const TextStyle(
                                      fontWeight: FontWeight.w900,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 10),
                              LinearProgressIndicator(
                                value: (progress / 100).clamp(0.0, 1.0),
                              ),
                              const SizedBox(height: 8),
                              Text(
                                _money.format(current) +
                                    ' of ' +
                                    _money.format(target),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ],
                          ),
                        ),
                      );
                    }),
                  ],
                ],
                if (data.upcomingBills.isNotEmpty) ...[
                  const SizedBox(height: 20),
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          'Upcoming payments',
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.w800,
                              ),
                        ),
                      ),
                      TextButton(
                        onPressed: () => Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => PlanningScreen(api: widget.api),
                          ),
                        ),
                        child: const Text('Manage'),
                      ),
                    ],
                  ),
                  ...data.upcomingBills.take(3).map((raw) {
                    final bill = Map<String, dynamic>.from(raw as Map);
                    final amount =
                        double.tryParse(bill['amount'].toString()) ?? 0;
                    final isCard = bill['bill_type'] == 'credit_card';
                    final last4 = bill['card_last4']?.toString();
                    final generated = bill['bill_generated_on']?.toString();

                    return Card(
                      child: ListTile(
                        leading: Icon(
                          isCard
                              ? Icons.credit_card_outlined
                              : Icons.receipt_long_outlined,
                        ),
                        title: Text(
                          bill['name'].toString(),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontWeight: FontWeight.w800),
                        ),
                        subtitle: Text(
                          isCard
                              ? [
                                  if (last4 != null && last4.isNotEmpty)
                                    '•••• ' + last4,
                                  if (generated != null)
                                    'Statement ' + generated,
                                  'Pay by ' + bill['due_on'].toString(),
                                ].join(' • ')
                              : 'Due ' + bill['due_on'].toString(),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                        trailing: ConstrainedBox(
                          constraints: const BoxConstraints(maxWidth: 100),
                          child: Text(
                            _money.format(amount),
                            textAlign: TextAlign.right,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              fontWeight: FontWeight.w900,
                            ),
                          ),
                        ),
                      ),
                    );
                  }),
                ],
                if (data.alerts.isNotEmpty) ...[
                  const SizedBox(height: 20),
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          'Needs attention',
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.w800,
                              ),
                        ),
                      ),
                      TextButton(
                        onPressed: () => Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => SmartAlertsScreen(api: widget.api),
                          ),
                        ),
                        child: const Text('View alerts'),
                      ),
                    ],
                  ),
                  ...data.alerts.take(3).map((raw) {
                    final alert = Map<String, dynamic>.from(raw as Map);
                    return Card(
                      child: ListTile(
                        leading: Icon(
                          alert['severity'] == 'critical'
                              ? Icons.error_outline
                              : Icons.warning_amber_rounded,
                        ),
                        title: Text(
                          alert['title'].toString(),
                          style: const TextStyle(fontWeight: FontWeight.w800),
                        ),
                        subtitle: Text(alert['message'].toString()),
                      ),
                    );
                  }),
                ],
                if (data.cashflowTrend.isNotEmpty) ...[
                  const SizedBox(height: 20),
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          'Cash-flow trend',
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.w800,
                              ),
                        ),
                      ),
                      TextButton(
                        onPressed: () => Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => InsightsScreen(api: widget.api),
                          ),
                        ),
                        child: const Text('Reports'),
                      ),
                    ],
                  ),
                  _cashflowTrendCard(data),
                ],
                const SizedBox(height: 22),
                Text(
                  'Money intelligence',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
                const SizedBox(height: 10),
                SizedBox(
                  height: 126,
                  child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    itemCount: data.insights.length,
                    separatorBuilder: (_, __) => const SizedBox(width: 10),
                    itemBuilder: (context, index) {
                      final item = Map<String, dynamic>.from(
                        data.insights[index] as Map,
                      );
                      return Container(
                        width: 180,
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Theme.of(context).colorScheme.surface,
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(
                            color:
                                Theme.of(context).colorScheme.outlineVariant,
                          ),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              item['title'].toString(),
                              style: TextStyle(
                                fontSize: 12,
                                color: Theme.of(context)
                                    .colorScheme
                                    .onSurfaceVariant,
                              ),
                            ),
                            const SizedBox(height: 8),
                            Text(
                              item['value'].toString(),
                              style: const TextStyle(
                                fontWeight: FontWeight.w900,
                                fontSize: 20,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              item['subtitle']?.toString() ?? '',
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(fontSize: 12),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                ),
                const SizedBox(height: 18),
                Row(
                  children: [
                    _summaryTile(
                      label: 'Income',
                      value: _money.format(data.monthIncome),
                      icon: Icons.south_west_rounded,
                    ),
                    const SizedBox(width: 12),
                    _summaryTile(
                      label: 'Expenses',
                      value: _money.format(data.monthExpense),
                      icon: Icons.north_east_rounded,
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    _summaryTile(
                      label: 'Net',
                      value: _money.format(data.monthNet),
                      icon: Icons.account_balance_wallet_outlined,
                    ),
                    const SizedBox(width: 12),
                    _summaryTile(
                      label: 'Transactions',
                      value: data.transactionCount.toString(),
                      icon: Icons.receipt_long_outlined,
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Recent activity',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w800,
                          ),
                    ),
                    TextButton(
                      onPressed: () => Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => PlanningScreen(api: widget.api),
                        ),
                      ),
                      child: const Text('Planning'),
                    ),
                  ],
                ),
                if (data.recentTransactions.isEmpty)
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.surface,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: const Text(
                      'No transactions yet. Add your first income or expense.',
                    ),
                  )
                else
                  ...data.recentTransactions.map((transaction) {
                    final amount =
                        double.tryParse(transaction['amount'].toString()) ?? 0;
                    final type = transaction['transaction_type'].toString();
                    return Container(
                      margin: const EdgeInsets.only(bottom: 8),
                      padding: const EdgeInsets.symmetric(
                        horizontal: 14,
                        vertical: 12,
                      ),
                      decoration: BoxDecoration(
                        color: Theme.of(context).colorScheme.surface,
                        borderRadius: BorderRadius.circular(18),
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
                                  transaction['merchant']?.toString() ??
                                      (type == 'income' ? 'Income' : 'Expense'),
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                                Text(
                                  transaction['occurred_on'].toString(),
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
                          const SizedBox(width: 8),
                          Flexible(
                            child: Text(
                              (type == 'expense' ? '- ' : '+ ') +
                                  _money.format(amount),
                              textAlign: TextAlign.right,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                fontWeight: FontWeight.w800,
                              ),
                            ),
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
