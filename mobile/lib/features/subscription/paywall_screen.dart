import 'dart:async';

import 'package:flutter/material.dart';
import 'package:in_app_purchase/in_app_purchase.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/api_client.dart';
import 'play_billing_service.dart';
import 'subscription_service.dart';

class PaywallScreen extends StatefulWidget {
  const PaywallScreen({
    super.key,
    required this.api,
    this.onActivated,
  });

  final ApiClient api;
  final VoidCallback? onActivated;

  @override
  State<PaywallScreen> createState() => _PaywallScreenState();
}

class _PaywallScreenState extends State<PaywallScreen> {
  late final SubscriptionService _subscriptions =
      SubscriptionService(widget.api);
  late final PlayBillingService _billing = PlayBillingService();

  final _money = NumberFormat.currency(
    locale: 'en_IN',
    symbol: '₹',
    decimalDigits: 0,
  );

  StreamSubscription<List<PurchaseDetails>>? _purchaseSubscription;
  bool _loading = true;
  bool _billingAvailable = false;
  bool _purchaseBusy = false;
  Map<String, dynamic>? _status;
  List<Map<String, dynamic>> _plans = const [];
  Map<String, ProductDetails> _productsById = const {};
  String? _selectedPlanId;
  String? _message;
  bool _messageIsError = false;

  @override
  void initState() {
    super.initState();
    _purchaseSubscription = _billing.purchaseStream.listen(
      _handlePurchaseUpdates,
      onError: (_) {
        if (!mounted) return;
        setState(() {
          _purchaseBusy = false;
          _message = 'Unable to process Google Play purchase updates.';
          _messageIsError = true;
        });
      },
    );
    _load();
  }

  Future<void> _load() async {
    try {
      final status = await _subscriptions.status();
      final plans = await _subscriptions.plans();
      final available = await _billing.isAvailable();

      final productIds = plans
          .map((plan) => plan['google_play_product_id']?.toString())
          .whereType<String>()
          .where((id) => id.isNotEmpty)
          .toSet();

      final products = available
          ? await _billing.loadProducts(productIds)
          : <ProductDetails>[];

      if (!mounted) return;

      String? initialSelectedId;
      if (plans.isNotEmpty) {
        final yearly = plans.firstWhere(
          (p) =>
              p['billing_period']?.toString().toLowerCase().contains('year') ==
              true,
          orElse: () => plans.first,
        );
        initialSelectedId = yearly['id']?.toString();
      }

      setState(() {
        _status = status;
        _plans = plans;
        _billingAvailable = available;
        _productsById = {
          for (final product in products) product.id: product,
        };
        _selectedPlanId = initialSelectedId;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _message = 'Unable to load FinPilot subscription plans.';
        _messageIsError = true;
      });
    }
  }

  ProductDetails? _productForPlan(Map<String, dynamic> plan) {
    final productId = plan['google_play_product_id']?.toString();
    if (productId == null || productId.isEmpty) return null;
    return _productsById[productId];
  }

  Map<String, dynamic>? get _selectedPlan {
    if (_selectedPlanId == null) return null;
    for (final plan in _plans) {
      if (plan['id']?.toString() == _selectedPlanId) return plan;
    }
    return _plans.isNotEmpty ? _plans.first : null;
  }

  Future<void> _buy(Map<String, dynamic> plan) async {
    final product = _productForPlan(plan);
    if (product == null) {
      setState(() {
        _message =
            'This plan is not ready in Google Play Console yet. In production, purchases are fulfilled via Google Play.';
        _messageIsError = false;
      });
      return;
    }

    setState(() {
      _purchaseBusy = true;
      _message = null;
    });

    try {
      final started = await _billing.buy(product);
      if (!started && mounted) {
        setState(() {
          _purchaseBusy = false;
          _message = 'Google Play could not start the purchase sheet.';
          _messageIsError = true;
        });
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _purchaseBusy = false;
        _message = 'Unable to start purchase: $e';
        _messageIsError = true;
      });
    }
  }

  Future<void> _restore() async {
    if (_purchaseBusy) return;
    setState(() {
      _purchaseBusy = true;
      _message = 'Querying past Google Play purchases...';
      _messageIsError = false;
    });
    try {
      await _billing.restorePurchases();
      if (!mounted) return;
      setState(() {
        _message = 'Restore request sent to Google Play.';
        _messageIsError = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _purchaseBusy = false;
        _message = 'Unable to restore purchases right now. Please try again.';
        _messageIsError = true;
      });
    }
  }

  Map<String, dynamic>? _planForProduct(String productId) {
    for (final plan in _plans) {
      if (plan['google_play_product_id']?.toString() == productId) {
        return plan;
      }
    }
    return null;
  }

  Future<void> _handlePurchaseUpdates(List<PurchaseDetails> purchases) async {
    for (final purchase in purchases) {
      if (!mounted) return;

      if (purchase.status == PurchaseStatus.pending) {
        setState(() {
          _purchaseBusy = true;
          _message = 'Purchase pending in Google Play...';
          _messageIsError = false;
        });
        continue;
      }

      if (purchase.status == PurchaseStatus.error) {
        setState(() {
          _purchaseBusy = false;
          _message = purchase.error?.message ?? 'Google Play purchase failed.';
          _messageIsError = true;
        });
        continue;
      }

      if (purchase.status == PurchaseStatus.canceled) {
        setState(() {
          _purchaseBusy = false;
          _message = 'Purchase cancelled.';
          _messageIsError = false;
        });
        continue;
      }

      if (purchase.status == PurchaseStatus.purchased ||
          purchase.status == PurchaseStatus.restored) {
        final plan = _planForProduct(purchase.productID);
        if (plan == null) {
          setState(() {
            _purchaseBusy = false;
            _message =
                'Purchase product is not linked to an active FinPilot plan.';
            _messageIsError = true;
          });
          continue;
        }

        final token = purchase.verificationData.serverVerificationData;

        try {
          final result = await _subscriptions.verifyGooglePlay(
            billingPlanId: plan['id'].toString(),
            productId: purchase.productID,
            purchaseToken: token,
          );

          if (result['verified'] == true) {
            await _billing.completePurchase(purchase);
            final status = await _subscriptions.status();

            if (!mounted) return;
            setState(() {
              _status = status;
              _purchaseBusy = false;
              _message = 'FinPilot Pro activated successfully!';
              _messageIsError = false;
            });
            widget.api.notifyDataChanged();
            widget.onActivated?.call();
          } else {
            if (!mounted) return;
            setState(() {
              _purchaseBusy = false;
              _message =
                  'Purchase received, but server verification is processing. It will activate shortly.';
              _messageIsError = false;
            });
          }
        } catch (_) {
          if (!mounted) return;
          setState(() {
            _purchaseBusy = false;
            _message =
                'Purchase received, but server verification failed. Please tap Restore.';
            _messageIsError = true;
          });
        }
      }
    }
  }

  Future<void> _openExternal(String path) async {
    final base = widget.api.dio.options.baseUrl
        .replaceAll('/api/v1', '')
        .replaceAll(RegExp(r'/+$'), '');
    final uri = Uri.tryParse('$base/$path');
    if (uri != null && await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  String _formatDate(String? iso) {
    if (iso == null || iso.isEmpty) return '—';
    try {
      final date = DateTime.parse(iso).toLocal();
      return DateFormat.yMMMMd().format(date);
    } catch (_) {
      return iso.split('T').first;
    }
  }

  @override
  void dispose() {
    _purchaseSubscription?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final active = _status?['status']?.toString() ?? 'unknown';
    final trialEnds = _status?['trial_ends_at']?.toString();
    final paidUntil = _status?['paid_until']?.toString();
    final currentPlan = _status?['billing_plan_name']?.toString();
    final isTrial = active == 'trial';
    final isPro = active == 'active' || active == 'pro';

    return Scaffold(
      appBar: AppBar(
        title: const Text('FinPilot Pro'),
        actions: [
          IconButton(
            tooltip: 'Restore purchase',
            icon: const Icon(Icons.restore),
            onPressed: _purchaseBusy || !_billingAvailable ? null : _restore,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
                children: [
                  // --- HERO BANNER ---
                  Container(
                    padding: const EdgeInsets.all(22),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFF10463A), Color(0xFF1B6B59)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0x33124D40),
                          blurRadius: 16,
                          offset: const Offset(0, 6),
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 10,
                                vertical: 4,
                              ),
                              decoration: BoxDecoration(
                                color: const Color(0xFFF59E0B),
                                borderRadius: BorderRadius.circular(20),
                              ),
                              child: const Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(
                                    Icons.workspace_premium,
                                    size: 14,
                                    color: Colors.white,
                                  ),
                                  SizedBox(width: 4),
                                  Text(
                                    'PRO',
                                    style: TextStyle(
                                      color: Colors.white,
                                      fontSize: 11,
                                      fontWeight: FontWeight.w900,
                                      letterSpacing: 0.5,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const Spacer(),
                            if (isTrial)
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 10,
                                  vertical: 4,
                                ),
                                decoration: BoxDecoration(
                                  color: const Color(0x2EFFFFFF),
                                  borderRadius: BorderRadius.circular(20),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    const Icon(
                                      Icons.access_time_rounded,
                                      size: 13,
                                      color: Colors.white,
                                    ),
                                    const SizedBox(width: 5),
                                    Text(
                                      'Trial ends ${_formatDate(trialEnds)}',
                                      style: const TextStyle(
                                        color: Colors.white,
                                        fontSize: 11,
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                          ],
                        ),
                        const SizedBox(height: 14),
                        const Text(
                          'Master Your Money with AI',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 22,
                            fontWeight: FontWeight.w900,
                            letterSpacing: -0.2,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          isPro
                              ? 'You have full Pro access with personalized AI guidance and unlimited tools.'
                              : isTrial
                                  ? 'Your 7-day Pro trial is active. Subscribe to keep lifetime access to your financial data.'
                                  : 'Unlock intelligent cash-flow analysis, AI Copilot guidance, and multi-account automation.',
                          style: const TextStyle(
                            color: Color(0xE6FFFFFF),
                            fontSize: 13.5,
                            height: 1.4,
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 24),

                  // --- STATUS CARD (IF NOT EMPTY) ---
                  if (currentPlan != null && currentPlan.isNotEmpty) ...[
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 14,
                        ),
                        child: Row(
                          children: [
                            const Icon(
                              Icons.verified_outlined,
                              color: Color(0xFF124D40),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    currentPlan,
                                    style: const TextStyle(
                                      fontWeight: FontWeight.w800,
                                      fontSize: 14,
                                    ),
                                  ),
                                  if (paidUntil != null)
                                    Text(
                                      'Renews: ${_formatDate(paidUntil)}',
                                      style: TextStyle(
                                        color: theme.colorScheme.onSurfaceVariant,
                                        fontSize: 12,
                                      ),
                                    ),
                                ],
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 10,
                                vertical: 4,
                              ),
                              decoration: BoxDecoration(
                                color: const Color(0xFFE8F5F1),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                active.toUpperCase(),
                                style: const TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w800,
                                  color: Color(0xFF124D40),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),
                  ],

                  // --- PRO FEATURES LIST ---
                  Text(
                    'What Pro Unlocks',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        children: [
                          _buildFeatureRow(
                            icon: Icons.auto_awesome_rounded,
                            iconColor: const Color(0xFF10B981),
                            title: 'Personal AI Copilot',
                            subtitle:
                                'Conversational financial guidance, monthly breakdowns, and custom savings insights.',
                          ),
                          const Divider(height: 20),
                          _buildFeatureRow(
                            icon: Icons.account_balance_wallet_rounded,
                            iconColor: const Color(0xFF3B82F6),
                            title: 'Multi-Account & Cash Flow',
                            subtitle:
                                'Connect Cash, Bank, Credit Cards & Wallets with accurate net worth tracking.',
                          ),
                          const Divider(height: 20),
                          _buildFeatureRow(
                            icon: Icons.handshake_rounded,
                            iconColor: const Color(0xFF8B5CF6),
                            title: 'Receivables & Liabilities',
                            subtitle:
                                'Track loans and money lent to individuals with repayment account linking.',
                          ),
                          const Divider(height: 20),
                          _buildFeatureRow(
                            icon: Icons.track_changes_rounded,
                            iconColor: const Color(0xFFF59E0B),
                            title: 'Smart Budgets & Goal Tracking',
                            subtitle:
                                'Proactive spending threshold alerts and visual progress milestones.',
                          ),
                          const Divider(height: 20),
                          _buildFeatureRow(
                            icon: Icons.shield_rounded,
                            iconColor: const Color(0xFF124D40),
                            title: 'Reports & Biometric Security',
                            subtitle:
                                'Instant CSV/PDF exports, device PIN, fingerprint lock, and zero ads.',
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 24),

                  // --- PLAN SELECTION ---
                  Text(
                    'Select a Subscription Plan',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const SizedBox(height: 10),

                  if (_plans.isEmpty)
                    const Card(
                      child: Padding(
                        padding: EdgeInsets.all(20),
                        child: Text(
                          'No public Pro plans are configured right now. Please check back soon or contact support.',
                          textAlign: TextAlign.center,
                        ),
                      ),
                    )
                  else
                    ..._plans.map((plan) {
                      final planId = plan['id']?.toString();
                      final isSelected = planId == _selectedPlanId;
                      final product = _productForPlan(plan);
                      final price =
                          double.tryParse(plan['price'].toString()) ?? 0;
                      final period = plan['billing_period']?.toString() ?? '';
                      final isYearly =
                          period.toLowerCase().contains('year');
                      final name = plan['name']?.toString() ?? 'Pro Plan';
                      final displayPrice =
                          product?.price ?? _money.format(price);

                      return Padding(
                        padding: const EdgeInsets.only(bottom: 12),
                        child: InkWell(
                          onTap: () => setState(() => _selectedPlanId = planId),
                          borderRadius: BorderRadius.circular(16),
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 200),
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: isSelected
                                  ? const Color(0xFFF0FDF4)
                                  : Colors.white,
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(
                                color: isSelected
                                    ? const Color(0xFF124D40)
                                    : const Color(0xFFE5EBE8),
                                width: isSelected ? 2 : 1,
                              ),
                              boxShadow: isSelected
                                  ? [
                                      BoxShadow(
                                        color: const Color(0x14124D40),
                                        blurRadius: 10,
                                        offset: const Offset(0, 3),
                                      ),
                                    ]
                                  : null,
                            ),
                            child: Row(
                              children: [
                                Icon(
                                  isSelected
                                      ? Icons.check_circle_rounded
                                      : Icons.radio_button_unchecked_rounded,
                                  color: isSelected
                                      ? const Color(0xFF124D40)
                                      : const Color(0xFF9CA3AF),
                                  size: 22,
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Row(
                                        children: [
                                          Text(
                                            name,
                                            style: const TextStyle(
                                              fontWeight: FontWeight.w800,
                                              fontSize: 16,
                                            ),
                                          ),
                                          if (isYearly) ...[
                                            const SizedBox(width: 8),
                                            Container(
                                              padding:
                                                  const EdgeInsets.symmetric(
                                                horizontal: 8,
                                                vertical: 2,
                                              ),
                                              decoration: BoxDecoration(
                                                color: const Color(0xFFDCFCE7),
                                                borderRadius:
                                                    BorderRadius.circular(8),
                                              ),
                                              child: const Text(
                                                'SAVE 30%',
                                                style: TextStyle(
                                                  color: Color(0xFF166534),
                                                  fontWeight: FontWeight.w800,
                                                  fontSize: 10,
                                                ),
                                              ),
                                            ),
                                          ],
                                        ],
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        isYearly
                                            ? 'Billed annually · Full access'
                                            : 'Billed monthly · Cancel anytime',
                                        style: TextStyle(
                                          color: theme
                                              .colorScheme.onSurfaceVariant,
                                          fontSize: 12,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.end,
                                  children: [
                                    Text(
                                      displayPrice,
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w900,
                                        fontSize: 17,
                                        color: Color(0xFF124D40),
                                      ),
                                    ),
                                    Text(
                                      isYearly ? '/ year' : '/ month',
                                      style: TextStyle(
                                        fontSize: 11,
                                        color: theme
                                            .colorScheme.onSurfaceVariant,
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    }),

                  const SizedBox(height: 12),

                  // --- MESSAGING ---
                  if (_message != null) ...[
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: _messageIsError
                            ? const Color(0xFFFEE2E2)
                            : const Color(0xFFE0F2FE),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: _messageIsError
                              ? const Color(0xFFF87171)
                              : const Color(0xFF7DD3FC),
                        ),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            _messageIsError
                                ? Icons.error_outline_rounded
                                : Icons.info_outline_rounded,
                            size: 20,
                            color: _messageIsError
                                ? const Color(0xFF991B1B)
                                : const Color(0xFF075985),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              _message!,
                              style: TextStyle(
                                fontSize: 13,
                                color: _messageIsError
                                    ? const Color(0xFF991B1B)
                                    : const Color(0xFF075985),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // --- ACTION BUTTON ---
                  SizedBox(
                    width: double.infinity,
                    height: 52,
                    child: FilledButton.icon(
                      style: FilledButton.styleFrom(
                        backgroundColor: const Color(0xFF124D40),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14),
                        ),
                      ),
                      onPressed: _purchaseBusy || _selectedPlan == null
                          ? null
                          : () => _buy(_selectedPlan!),
                      icon: _purchaseBusy
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : const Icon(Icons.shopping_bag_outlined, size: 20),
                      label: Text(
                        _purchaseBusy
                            ? 'Contacting Google Play...'
                            : _selectedPlan != null
                                ? 'Continue with ${_selectedPlan!['name']}'
                                : 'Select a Plan',
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                  ),

                  const SizedBox(height: 14),

                  Center(
                    child: TextButton.icon(
                      onPressed: _purchaseBusy || !_billingAvailable
                          ? null
                          : _restore,
                      icon: const Icon(Icons.restore_rounded, size: 18),
                      label: const Text(
                        'Restore Google Play Purchase',
                        style: TextStyle(fontWeight: FontWeight.w700),
                      ),
                    ),
                  ),

                  const SizedBox(height: 16),

                  // --- LEGAL & TRUST FOOTER ---
                  Text(
                    _billingAvailable
                        ? 'Payments are securely processed through Google Play. Subscriptions auto-renew unless cancelled at least 24 hours before the end of the current billing cycle in your Google Play account settings.'
                        : 'Google Play Billing is active in production builds. If testing in development without Play Services, use the Admin console to grant Pro access.',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                      height: 1.4,
                      fontSize: 11,
                    ),
                  ),

                  const SizedBox(height: 14),

                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      TextButton(
                        onPressed: () => _openExternal('privacy'),
                        child: const Text(
                          'Privacy Policy',
                          style: TextStyle(fontSize: 12),
                        ),
                      ),
                      const Text('•', style: TextStyle(color: Colors.grey)),
                      TextButton(
                        onPressed: () => _openExternal('terms'),
                        child: const Text(
                          'Terms of Service',
                          style: TextStyle(fontSize: 12),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
    );
  }

  Widget _buildFeatureRow({
    required IconData icon,
    required Color iconColor,
    required String title,
    required String subtitle,
  }) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: iconColor.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(icon, size: 18, color: iconColor),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontWeight: FontWeight.w800,
                  fontSize: 14,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                subtitle,
                style: const TextStyle(
                  color: Color(0xFF6B7280),
                  fontSize: 12,
                  height: 1.35,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
