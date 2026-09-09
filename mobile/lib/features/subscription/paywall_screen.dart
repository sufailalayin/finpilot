import 'dart:async';

import 'package:flutter/material.dart';
import 'package:in_app_purchase/in_app_purchase.dart';
import 'package:intl/intl.dart';

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
  late final SubscriptionService _subscriptions = SubscriptionService(widget.api);
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
  String? _message;

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
      setState(() {
        _status = status;
        _plans = plans;
        _billingAvailable = available;
        _productsById = {
          for (final product in products) product.id: product,
        };
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _message = 'Unable to load FinPilot subscription plans.';
      });
    }
  }

  ProductDetails? _productForPlan(Map<String, dynamic> plan) {
    final productId = plan['google_play_product_id']?.toString();
    if (productId == null || productId.isEmpty) return null;
    return _productsById[productId];
  }

  Future<void> _buy(Map<String, dynamic> plan) async {
    final product = _productForPlan(plan);
    if (product == null) {
      setState(() {
        _message = 'This plan is not ready for Google Play payment yet.';
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
          _message = 'Google Play could not start the purchase.';
        });
      }
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _purchaseBusy = false;
        _message = 'Unable to start purchase.';
      });
    }
  }

  Future<void> _restore() async {
    if (_purchaseBusy) return;
    setState(() {
      _purchaseBusy = true;
      _message = 'Checking previous Google Play purchases...';
    });
    try {
      await _billing.restorePurchases();
      if (!mounted) return;
      setState(() {
        _message = 'Restore request sent to Google Play.';
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _purchaseBusy = false;
        _message = 'Unable to restore purchases right now.';
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
        });
        continue;
      }

      if (purchase.status == PurchaseStatus.error) {
        setState(() {
          _purchaseBusy = false;
          _message = purchase.error?.message ?? 'Google Play purchase failed.';
        });
        continue;
      }

      if (purchase.status == PurchaseStatus.canceled) {
        setState(() {
          _purchaseBusy = false;
          _message = 'Purchase cancelled.';
        });
        continue;
      }

      if (purchase.status == PurchaseStatus.purchased ||
          purchase.status == PurchaseStatus.restored) {
        final plan = _planForProduct(purchase.productID);
        if (plan == null) {
          setState(() {
            _purchaseBusy = false;
            _message = 'Purchase product is not linked to an active FinPilot plan.';
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
              _message = 'FinPilot activated successfully.';
            });
            widget.api.notifyDataChanged();
            widget.onActivated?.call();
          } else {
            if (!mounted) return;
            setState(() {
              _purchaseBusy = false;
              _message = 'Purchase received, but server verification is not complete yet.';
            });
          }
        } catch (_) {
          if (!mounted) return;
          setState(() {
            _purchaseBusy = false;
            _message = 'Purchase received, but verification failed. Please try again.';
          });
        }
      }
    }
  }

  @override
  void dispose() {
    _purchaseSubscription?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final active = _status?['status']?.toString() ?? 'unknown';
    final trialEnds = _status?['trial_ends_at']?.toString();
    final paidUntil = _status?['paid_until']?.toString();
    final currentPlan = _status?['billing_plan_name']?.toString();

    return Scaffold(
      appBar: AppBar(title: const Text('FinPilot Plans')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  Text(
                    'Choose your FinPilot plan',
                    style: Theme.of(context)
                        .textTheme
                        .headlineMedium
                        ?.copyWith(fontWeight: FontWeight.w900),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    active == 'trial'
                        ? 'Your trial is active. Choose a plan anytime to continue without interruption.'
                        : 'Your trial or paid access has ended. Select a plan to unlock FinPilot.',
                  ),
                  const SizedBox(height: 16),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Status: ' + active),
                          if (currentPlan != null && currentPlan.isNotEmpty)
                            Text('Current plan: ' + currentPlan),
                          if (trialEnds != null) Text('Trial ends: ' + trialEnds),
                          if (paidUntil != null) Text('Paid until: ' + paidUntil),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  if (_plans.isEmpty)
                    const Card(
                      child: Padding(
                        padding: EdgeInsets.all(20),
                        child: Text(
                          'No active paid plans are available right now. Please contact support.',
                        ),
                      ),
                    )
                  else
                    ..._plans.map((plan) {
                      final product = _productForPlan(plan);
                      final price = double.tryParse(plan['price'].toString()) ?? 0;
                      final period = plan['billing_period']?.toString() ?? '';
                      final description = plan['description']?.toString();
                      final productReady = product != null;

                      return Padding(
                        padding: const EdgeInsets.only(bottom: 12),
                        child: Card(
                          child: Padding(
                            padding: const EdgeInsets.all(18),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Expanded(
                                      child: Text(
                                        plan['name'].toString(),
                                        style: const TextStyle(
                                          fontSize: 20,
                                          fontWeight: FontWeight.w900,
                                        ),
                                      ),
                                    ),
                                    Text(
                                      product?.price ?? _money.format(price),
                                      style: const TextStyle(
                                        fontSize: 18,
                                        fontWeight: FontWeight.w900,
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 6),
                                Text(period.toUpperCase()),
                                if (description != null && description.isNotEmpty) ...[
                                  const SizedBox(height: 8),
                                  Text(description),
                                ],
                                const SizedBox(height: 14),
                                SizedBox(
                                  width: double.infinity,
                                  child: FilledButton(
                                    onPressed: _purchaseBusy || !productReady
                                        ? null
                                        : () => _buy(plan),
                                    child: Text(
                                      productReady
                                          ? 'Select & pay'
                                          : 'Payment setup pending',
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    }),
                  const SizedBox(height: 8),
                  TextButton.icon(
                    onPressed: _purchaseBusy || !_billingAvailable ? null : _restore,
                    icon: const Icon(Icons.restore),
                    label: const Text('Restore Google Play purchase'),
                  ),
                  if (_message != null) ...[
                    const SizedBox(height: 12),
                    Text(
                      _message!,
                      textAlign: TextAlign.center,
                    ),
                  ],
                  const SizedBox(height: 16),
                  Text(
                    _billingAvailable
                        ? 'Payments are processed by Google Play. Access is activated only after server verification.'
                        : 'Google Play Billing is unavailable on this device or build.',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ),
    );
  }
}
