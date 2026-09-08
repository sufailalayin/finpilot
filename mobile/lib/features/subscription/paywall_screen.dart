import 'dart:async';

import 'package:flutter/material.dart';
import 'package:in_app_purchase/in_app_purchase.dart';

import '../../core/api_client.dart';
import 'play_billing_service.dart';
import 'subscription_service.dart';

class PaywallScreen extends StatefulWidget {
  const PaywallScreen({super.key, required this.api});

  final ApiClient api;

  @override
  State<PaywallScreen> createState() => _PaywallScreenState();
}

class _PaywallScreenState extends State<PaywallScreen> {
  late final SubscriptionService _subscriptions = SubscriptionService(widget.api);
  late final PlayBillingService _billing = PlayBillingService();

  StreamSubscription<List<PurchaseDetails>>? _purchaseSubscription;

  bool _loading = true;
  bool _billingAvailable = false;
  bool _purchaseBusy = false;
  Map<String, dynamic>? _status;
  List<ProductDetails> _products = const [];
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
      final available = await _billing.isAvailable();
      final products = available ? await _billing.loadProducts() : <ProductDetails>[];

      if (!mounted) return;
      setState(() {
        _status = status;
        _billingAvailable = available;
        _products = products;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _message = 'Unable to load FinPilot Pro status.';
      });
    }
  }

  ProductDetails? _product(String id) {
    for (final product in _products) {
      if (product.id == id) return product;
    }
    return null;
  }

  Future<void> _buy(ProductDetails product) async {
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
        final token = purchase.verificationData.serverVerificationData;

        try {
          final result = await _subscriptions.verifyGooglePlay(
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
              _message = 'FinPilot Pro activated successfully.';
            });
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
            _message = 'Purchase received, but verification failed. Please retry later.';
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
    final monthly = _product(_billing.monthlyProductId);
    final yearly = _product(_billing.yearlyProductId);

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
                  onPressed: _purchaseBusy || monthly == null
                      ? null
                      : () => _buy(monthly),
                  child: Text(
                    monthly == null
                        ? 'Monthly plan unavailable'
                        : 'Monthly — ' + monthly.price,
                  ),
                ),
                const SizedBox(height: 12),
                OutlinedButton(
                  onPressed: _purchaseBusy || yearly == null
                      ? null
                      : () => _buy(yearly),
                  child: Text(
                    yearly == null
                        ? 'Yearly plan unavailable'
                        : 'Yearly — ' + yearly.price,
                  ),
                ),
                if (_message != null) ...[
                  const SizedBox(height: 16),
                  Text(
                    _message!,
                    textAlign: TextAlign.center,
                  ),
                ],
                const SizedBox(height: 20),
                Text(
                  _billingAvailable
                      ? 'Payments are processed by Google Play. Pro access is enabled only after server verification.'
                      : 'Google Play Billing is unavailable on this device or build.',
                  textAlign: TextAlign.center,
                ),
              ],
            ),
    );
  }
}
