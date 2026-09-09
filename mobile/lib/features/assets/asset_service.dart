import '../../core/api_client.dart';

class AssetService {
  AssetService(this._api);

  final ApiClient _api;

  Future<Map<String, dynamic>> overview() async {
    final response = await _api.dio.get('/assets/overview/summary');
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<void> createAsset({
    required String name,
    required String assetType,
    String? institution,
    required double quantity,
    required double costBasis,
    required double currentValue,
    DateTime? maturityDate,
    String? notes,
  }) async {
    await _api.dio.post(
      '/assets',
      data: {
        'name': name.trim(),
        'asset_type': assetType,
        'institution':
            institution?.trim().isEmpty == true ? null : institution?.trim(),
        'quantity': quantity,
        'cost_basis': costBasis,
        'current_value': currentValue,
        'maturity_date':
            maturityDate?.toIso8601String().split('T').first,
        'notes': notes?.trim().isEmpty == true ? null : notes?.trim(),
      },
    );
    _api.notifyDataChanged();
  }

  Future<void> updateAsset({
    required String assetId,
    required String name,
    required String assetType,
    String? institution,
    required double quantity,
    required double costBasis,
    required double currentValue,
    DateTime? maturityDate,
    String? notes,
  }) async {
    await _api.dio.patch(
      '/assets/$assetId',
      data: {
        'name': name.trim(),
        'asset_type': assetType,
        'institution':
            institution?.trim().isEmpty == true ? null : institution?.trim(),
        'quantity': quantity,
        'cost_basis': costBasis,
        'current_value': currentValue,
        'maturity_date':
            maturityDate?.toIso8601String().split('T').first,
        'notes': notes?.trim().isEmpty == true ? null : notes?.trim(),
      },
    );
    _api.notifyDataChanged();
  }

  Future<void> deleteAsset(String assetId) async {
    await _api.dio.delete('/assets/$assetId');
    _api.notifyDataChanged();
  }
}
