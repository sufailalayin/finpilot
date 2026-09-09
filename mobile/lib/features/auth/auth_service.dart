import 'package:dio/dio.dart';

import '../../core/api_client.dart';

class AuthService {
  AuthService(this._api);

  final ApiClient _api;

  Future<void> register({
    required String email,
    required String password,
    required String fullName,
  }) async {
    final response = await _api.dio.post(
      '/auth/register',
      data: {
        'email': email.trim(),
        'password': password,
        'full_name': fullName.trim().isEmpty ? null : fullName.trim(),
      },
    );

    final token = response.data['access_token'] as String;
    await _api.saveToken(token);
  }

  Future<void> login({
    required String email,
    required String password,
  }) async {
    final response = await _api.dio.post(
      '/auth/login',
      data: {
        'email': email.trim(),
        'password': password,
      },
    );

    final token = response.data['access_token'] as String;
    await _api.saveToken(token);
  }

  Future<bool> hasSession() async {
    final token = await _api.readToken();
    if (token == null || token.isEmpty) return false;

    try {
      await _api.dio.get('/auth/me');
      return true;
    } on DioException catch (error) {
      if (error.response?.statusCode == 401) {
        await _api.clearToken();
        return false;
      }

      // If the backend/network is temporarily unavailable, keep the local
      // session and allow normal screen-level retry handling to recover.
      return true;
    }
  }

  Future<void> logout() => _api.clearToken();
}
