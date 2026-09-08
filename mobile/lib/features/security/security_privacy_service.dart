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
    if (token != null && token.isNotEmpty) {
      await _api.saveToken(token);
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
