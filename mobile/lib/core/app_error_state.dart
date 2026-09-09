import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

class AppErrorState extends StatelessWidget {
  const AppErrorState({
    super.key,
    required this.error,
    required this.onRetry,
    this.title = 'Unable to load data',
  });

  final Object? error;
  final Future<void> Function() onRetry;
  final String title;

  String get _message {
    if (error is DioException) {
      final dio = error as DioException;
      final code = dio.response?.statusCode;

      if (code == 401) {
        return 'Your session has expired. FinPilot will return you to sign in.';
      }
      if (code == 402) {
        return 'This feature requires FinPilot Pro.';
      }
      if (code != null && code >= 500) {
        return 'FinPilot server is temporarily unavailable. Your saved data is not lost.';
      }
      if (dio.type == DioExceptionType.connectionError ||
          dio.type == DioExceptionType.connectionTimeout ||
          dio.type == DioExceptionType.receiveTimeout ||
          dio.type == DioExceptionType.sendTimeout) {
        return 'Check your internet connection. FinPilot already retried automatically.';
      }
    }

    return 'FinPilot could not refresh this screen. Your previously saved data remains on the server.';
  }

  @override
  Widget build(BuildContext context) {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(28),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: Column(
            children: [
              CircleAvatar(
                radius: 34,
                backgroundColor:
                    Theme.of(context).colorScheme.errorContainer,
                child: Icon(
                  Icons.cloud_off_outlined,
                  size: 32,
                  color: Theme.of(context).colorScheme.onErrorContainer,
                ),
              ),
              const SizedBox(height: 18),
              Text(
                title,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w900,
                    ),
              ),
              const SizedBox(height: 8),
              Text(
                _message,
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                  height: 1.45,
                ),
              ),
              const SizedBox(height: 20),
              FilledButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh),
                label: const Text('Try again'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
