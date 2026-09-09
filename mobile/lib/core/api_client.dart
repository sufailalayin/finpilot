import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter/foundation.dart';

class ApiClient {
  static const _retryKey = 'finpilot_retry_count';

  bool _isTransient(DioException error) {
    final code = error.response?.statusCode;
    return error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.sendTimeout ||
        error.type == DioExceptionType.connectionError ||
        (code != null && code >= 500);
  }

  bool _shouldRetry(DioException error) {
    if (error.requestOptions.method.toUpperCase() != 'GET') return false;
    if (!_isTransient(error)) return false;
    final count =
        (error.requestOptions.extra[_retryKey] as int?) ?? 0;
    return count < 2;
  }

  ApiClient({String? baseUrl})
      : _storage = const FlutterSecureStorage(),
        dio = Dio(
          BaseOptions(
            baseUrl: baseUrl ?? const String.fromEnvironment(
              'FINPILOT_API_BASE_URL',
              defaultValue: 'https://api.invalid/finpilot',
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
            handler.next(error);
            return;
          }

          if (error.response?.statusCode == 402) {
            subscriptionExpired.value = true;
            handler.next(error);
            return;
          }

          if (_shouldRetry(error)) {
            final options = error.requestOptions;
            final count = (options.extra[_retryKey] as int?) ?? 0;
            options.extra[_retryKey] = count + 1;
            await Future<void>.delayed(
              Duration(milliseconds: 450 * (count + 1)),
            );
            try {
              final response = await dio.fetch<dynamic>(options);
              handler.resolve(response);
              return;
            } on DioException catch (retryError) {
              handler.next(retryError);
              return;
            }
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
  final ValueNotifier<bool> subscriptionExpired = ValueNotifier<bool>(false);

  void notifyDataChanged() {
    dataRevision.value++;
  }

  Future<void> saveToken(String token) =>
      _storage.write(key: _tokenKey, value: token);

  Future<String?> readToken() => _storage.read(key: _tokenKey);

  Future<void> clearToken() => _storage.delete(key: _tokenKey);
}
