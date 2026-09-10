import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiClient {
  static const _retryKey = 'finpilot_retry_count';
  static const _authRetryKey = 'finpilot_auth_retry';
  static const _tokenKey = 'finpilot_access_token';
  static const _refreshTokenKey = 'finpilot_refresh_token';

  ApiClient({String? baseUrl})
      : _storage = const FlutterSecureStorage(),
        _baseUrl = baseUrl ??
            const String.fromEnvironment(
              'FINPILOT_API_BASE_URL',
              defaultValue: 'https://api.invalid/finpilot',
            ) {
    dio = Dio(
      BaseOptions(
        baseUrl: _baseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 20),
      ),
    );
    _refreshDio = Dio(
      BaseOptions(
        baseUrl: _baseUrl,
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 20),
      ),
    );

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
            final path = error.requestOptions.path;
            final isPublicAuth = _isPublicAuthPath(path);
            final alreadyRetried =
                error.requestOptions.extra[_authRetryKey] == true;

            if (!isPublicAuth && !alreadyRetried) {
              final refreshed = await _refreshAccessToken();
              if (refreshed) {
                try {
                  final options = error.requestOptions;
                  options.extra[_authRetryKey] = true;
                  final token = await readToken();
                  if (token != null && token.isNotEmpty) {
                    options.headers['Authorization'] = 'Bearer $token';
                  }
                  final response = await dio.fetch<dynamic>(options);
                  handler.resolve(response);
                  return;
                } on DioException catch (retryError) {
                  if (retryError.response?.statusCode != 401) {
                    handler.next(retryError);
                    return;
                  }
                }
              }

              await clearSession();
              sessionExpired.value = true;
            }

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

  final FlutterSecureStorage _storage;
  final String _baseUrl;
  late final Dio dio;
  late final Dio _refreshDio;
  Future<bool>? _refreshInFlight;

  final ValueNotifier<int> dataRevision = ValueNotifier<int>(0);
  final ValueNotifier<bool> sessionExpired = ValueNotifier<bool>(false);
  final ValueNotifier<bool> subscriptionExpired = ValueNotifier<bool>(false);

  bool _isPublicAuthPath(String path) {
    if (!path.startsWith('/auth/')) return false;
    return path != '/auth/me';
  }

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
    final count = (error.requestOptions.extra[_retryKey] as int?) ?? 0;
    return count < 2;
  }

  Future<bool> _refreshAccessToken() {
    final existing = _refreshInFlight;
    if (existing != null) return existing;

    final future = _performRefresh();
    _refreshInFlight = future;
    return future.whenComplete(() {
      _refreshInFlight = null;
    });
  }

  Future<bool> _performRefresh() async {
    final refresh = await readRefreshToken();
    if (refresh == null || refresh.isEmpty) return false;

    try {
      final response = await _refreshDio.post(
        '/auth/refresh',
        data: {'refresh_token': refresh},
      );
      final data = Map<String, dynamic>.from(response.data as Map);
      final accessToken = data['access_token']?.toString();
      final refreshToken = data['refresh_token']?.toString();
      if (accessToken == null ||
          accessToken.isEmpty ||
          refreshToken == null ||
          refreshToken.isEmpty) {
        return false;
      }
      await saveSession(
        accessToken: accessToken,
        refreshToken: refreshToken,
      );
      return true;
    } on DioException {
      return false;
    }
  }

  void notifyDataChanged() {
    dataRevision.value++;
  }

  Future<void> saveSession({
    required String accessToken,
    required String refreshToken,
  }) async {
    await _storage.write(key: _tokenKey, value: accessToken);
    await _storage.write(key: _refreshTokenKey, value: refreshToken);
  }

  Future<void> saveToken(String token) =>
      _storage.write(key: _tokenKey, value: token);

  Future<void> saveRefreshToken(String token) =>
      _storage.write(key: _refreshTokenKey, value: token);

  Future<String?> readToken() => _storage.read(key: _tokenKey);

  Future<String?> readRefreshToken() =>
      _storage.read(key: _refreshTokenKey);

  Future<void> clearToken() => clearSession();

  Future<void> clearSession() async {
    await _storage.delete(key: _tokenKey);
    await _storage.delete(key: _refreshTokenKey);
  }
}
