import 'dart:async';

import 'package:in_app_purchase/in_app_purchase.dart';

class PlayBillingService {
  PlayBillingService({
    this.monthlyProductId = 'finpilot_pro_monthly',
    this.yearlyProductId = 'finpilot_pro_yearly',
  });

  final String monthlyProductId;
  final String yearlyProductId;
  final InAppPurchase _billing = InAppPurchase.instance;

  Stream<List<PurchaseDetails>> get purchaseStream => _billing.purchaseStream;

  Future<bool> isAvailable() => _billing.isAvailable();

  Future<List<ProductDetails>> loadProducts() async {
    final response = await _billing.queryProductDetails({
      monthlyProductId,
      yearlyProductId,
    });
    return response.productDetails;
  }

  Future<bool> buy(ProductDetails product) {
    return _billing.buyNonConsumable(
      purchaseParam: PurchaseParam(productDetails: product),
    );
  }

  Future<void> completePurchase(PurchaseDetails purchase) async {
    if (purchase.pendingCompletePurchase) {
      await _billing.completePurchase(purchase);
    }
  }
}
