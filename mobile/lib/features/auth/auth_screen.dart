import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../dashboard/dashboard_screen.dart';
import 'auth_service.dart';

class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key, required this.api});

  final ApiClient api;

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  late final AuthService _auth = AuthService(widget.api);
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _name = TextEditingController();

  bool _registerMode = false;
  bool _loading = false;
  String? _error;

  Future<void> _submit() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      if (_registerMode) {
        await _auth.register(
          email: _email.text,
          password: _password.text,
          fullName: _name.text,
        );
      } else {
        await _auth.login(
          email: _email.text,
          password: _password.text,
        );
      }

      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => DashboardScreen(api: widget.api),
        ),
      );
    } on DioException catch (error) {
      final data = error.response?.data;
      final message = data is Map<String, dynamic> && data['detail'] != null
          ? data['detail'].toString()
          : 'Unable to connect to FinPilot.';
      setState(() => _error = message);
    } catch (_) {
      setState(() => _error = 'Something went wrong. Please try again.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    _name.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            const SizedBox(height: 48),
            Text(
              'FinPilot',
              style: Theme.of(context)
                  .textTheme
                  .displaySmall
                  ?.copyWith(fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 8),
            Text(
              _registerMode
                  ? 'Start your 7-day Pro trial'
                  : 'Welcome back',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 32),
            if (_registerMode) ...[
              TextField(
                controller: _name,
                textInputAction: TextInputAction.next,
                decoration: const InputDecoration(
                  labelText: 'Full name',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
            ],
            TextField(
              controller: _email,
              keyboardType: TextInputType.emailAddress,
              textInputAction: TextInputAction.next,
              autocorrect: false,
              decoration: const InputDecoration(
                labelText: 'Email',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _password,
              obscureText: true,
              onSubmitted: (_) => _submit(),
              decoration: const InputDecoration(
                labelText: 'Password',
                border: OutlineInputBorder(),
              ),
            ),
            if (_error != null) ...[
              const SizedBox(height: 16),
              Text(
                _error!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ],
            const SizedBox(height: 24),
            FilledButton(
              onPressed: _loading ? null : _submit,
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 14),
                child: Text(
                  _loading
                      ? 'Please wait...'
                      : _registerMode
                          ? 'Create account'
                          : 'Sign in',
                ),
              ),
            ),
            TextButton(
              onPressed: _loading
                  ? null
                  : () => setState(() {
                        _registerMode = !_registerMode;
                        _error = null;
                      }),
              child: Text(
                _registerMode
                    ? 'Already have an account? Sign in'
                    : 'New to FinPilot? Start free trial',
              ),
            ),
            const SizedBox(height: 32),
            const Center(child: Text('FinPilot by Hastron Ventures')),
          ],
        ),
      ),
    );
  }
}
