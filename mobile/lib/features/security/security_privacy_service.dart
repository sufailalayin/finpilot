import 'dart:convert';
import 'dart:io';

import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

import '../../core/api_client.dart';

class SecurityPrivacyService {
  SecurityPrivacyService(this._api);

  final ApiClient _api;

  Future<List<dynamic>> events() async {
    final response = await _api.dio.get('/security/events');
    return response.data as List<dynamic>;
  }

  Future<void> revokeSessions() async {
    final response = await _api.dio.post('/security/revoke-sessions');
    final token = response.data['access_token']?.toString();
    final refreshToken = response.data['refresh_token']?.toString();
    if (token != null &&
        token.isNotEmpty &&
        refreshToken != null &&
        refreshToken.isNotEmpty) {
      await _api.saveSession(
        accessToken: token,
        refreshToken: refreshToken,
      );
    }
  }

  Future<void> exportData() async {
    final response = await _api.dio.get('/security/export');
    final dir = await getTemporaryDirectory();
    final file = File(
      dir.path + '/finpilot-data-export.json',
    );
    await file.writeAsString(
      const JsonEncoder.withIndent('  ').convert(response.data),
      flush: true,
    );
    await Share.shareXFiles(
      [XFile(file.path)],
      text: 'FinPilot account data export',
    );
  }

  String _csvCell(dynamic value) {
    final text = value?.toString() ?? '';
    return '"' + text.replaceAll('"', '""') + '"';
  }

  Future<void> exportTransactionsCsv() async {
    final response = await _api.dio.get('/security/export');
    final root = Map<String, dynamic>.from(response.data as Map);
    final payload = Map<String, dynamic>.from(root['data'] as Map);
    final transactions =
        (payload['transactions'] as List<dynamic>?) ?? const [];

    final rows = <String>[
      'date,type,amount,merchant,note,account_id,category_id',
    ];
    for (final raw in transactions) {
      final item = Map<String, dynamic>.from(raw as Map);
      rows.add([
        item['occurred_on'],
        item['transaction_type'],
        item['amount'],
        item['merchant'],
        item['note'],
        item['account_id'],
        item['category_id'],
      ].map(_csvCell).join(','));
    }

    final dir = await getTemporaryDirectory();
    final file = File(dir.path + '/finpilot-transactions.csv');
    await file.writeAsString(rows.join('\n'), flush: true);
    await Share.shareXFiles(
      [XFile(file.path)],
      text: 'FinPilot transaction export',
    );
  }

  Future<void> deleteAccount({
    required String password,
  }) async {
    await _api.dio.delete(
      '/security/account',
      data: {
        'password': password,
        'confirmation': 'DELETE MY ACCOUNT',
      },
    );
    await _api.clearToken();
  }
}
