import 'dart:async';

import 'package:in_app_purchase/in_app_purchase.dart';

class PlayBillingService {
  final InAppPurchase _billing = InAppPurchase.instance;

  Stream<List<PurchaseDetails>> get purchaseStream => _billing.purchaseStream;

  Future<bool> isAvailable() => _billing.isAvailable();

  Future<List<ProductDetails>> loadProducts(Set<String> productIds) async {
    if (productIds.isEmpty) return const [];
    final response = await _billing.queryProductDetails(productIds);
    return response.productDetails;
  }

  Future<void> restorePurchases() async {
    await _billing.restorePurchases();
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
