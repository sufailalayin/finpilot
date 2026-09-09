import 'package:dio/dio.dart';

import '../../core/api_client.dart';

class AuthService {
  AuthService(this._api);

  final ApiClient _api;

  Future<Map<String, dynamic>> register({
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
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<void> verifyRegistration({
    required String email,
    required String code,
  }) async {
    final response = await _api.dio.post(
      '/auth/register/verify',
      data: {
        'email': email.trim(),
        'code': code.trim(),
      },
    );
    final token = response.data['access_token'] as String;
    await _api.saveToken(token);
  }

  Future<Map<String, dynamic>> resendRegistrationOtp({
    required String email,
  }) async {
    final response = await _api.dio.post(
      '/auth/register/resend',
      data: {'email': email.trim()},
    );
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<String> forgotPassword({
    required String email,
  }) async {
    final response = await _api.dio.post(
      '/auth/password/forgot',
      data: {'email': email.trim()},
    );
    return response.data['message'].toString();
  }

  Future<String> resetPassword({
    required String email,
    required String code,
    required String newPassword,
  }) async {
    final response = await _api.dio.post(
      '/auth/password/reset',
      data: {
        'email': email.trim(),
        'code': code.trim(),
        'new_password': newPassword,
      },
    );
    return response.data['message'].toString();
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
