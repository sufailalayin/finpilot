import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter/foundation.dart';

class ApiClient {
  ApiClient({String? baseUrl})
      : _storage = const FlutterSecureStorage(),
        dio = Dio(
          BaseOptions(
            baseUrl: baseUrl ?? const String.fromEnvironment(
              'FINPILOT_API_BASE_URL',
              defaultValue:
                  'https://finpilot-backend-production-1cb7.up.railway.app/api/v1',
            ),
            connectTimeout: const Duration(seconds: 15),
            receiveTimeout: const Duration(seconds: 20),
          ),
        ) {
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _storage.read(key: _tokenKey);
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (error, handler) async {
          if (error.response?.statusCode == 401) {
            await _storage.delete(key: _tokenKey);
            sessionExpired.value = true;
          }
          handler.next(error);
        },
      ),
    );
  }

  static const _tokenKey = 'finpilot_access_token';

  final Dio dio;
  final FlutterSecureStorage _storage;
  final ValueNotifier<int> dataRevision = ValueNotifier<int>(0);
  final ValueNotifier<bool> sessionExpired = ValueNotifier<bool>(false);

  void notifyDataChanged() {
    dataRevision.value++;
  }

  Future<void> saveToken(String token) =>
      _storage.write(key: _tokenKey, value: token);

  Future<String?> readToken() => _storage.read(key: _tokenKey);

  Future<void> clearToken() => _storage.delete(key: _tokenKey);
}
