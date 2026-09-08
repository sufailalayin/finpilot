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
    return token != null && token.isNotEmpty;
  }

  Future<void> logout() => _api.clearToken();
}
