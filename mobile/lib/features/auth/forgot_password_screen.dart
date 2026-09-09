import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import 'auth_service.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key, required this.api});

  final ApiClient api;

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  late final AuthService _auth = AuthService(widget.api);
  final _email = TextEditingController();
  final _code = TextEditingController();
  final _password = TextEditingController();
  final _confirm = TextEditingController();

  bool _codeSent = false;
  bool _loading = false;
  Timer? _timer;
  int _seconds = 0;
  bool _obscure = true;
  String? _error;
  String? _message;

  void _startCountdown() {
    _timer?.cancel();
    setState(() => _seconds = 60);
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) return;
      if (_seconds <= 1) {
        timer.cancel();
        setState(() => _seconds = 0);
      } else {
        setState(() => _seconds--);
      }
    });
  }

  Future<void> _sendCode() async {
    if (_loading) return;
    final email = _email.text.trim();
    if (!email.contains('@')) {
      setState(() => _error = 'Enter your registered email address.');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
      _message = null;
    });

    try {
      final message = await _auth.forgotPassword(email: email);
      if (!mounted) return;
      setState(() {
        _codeSent = true;
        _message = message;
      });
      _startCountdown();
    } catch (_) {
      if (!mounted) return;
      setState(() => _error = 'Unable to request a reset code right now.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _reset() async {
    if (_loading) return;

    final code = _code.text.trim();
    final password = _password.text;
    if (!RegExp(r'^\d{6}$').hasMatch(code)) {
      setState(() => _error = 'Enter the 6-digit reset code.');
      return;
    }
    if (password.length < 8) {
      setState(() => _error = 'Password must be at least 8 characters.');
      return;
    }
    if (password != _confirm.text) {
      setState(() => _error = 'Passwords do not match.');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
      _message = null;
    });

    try {
      final message = await _auth.resetPassword(
        email: _email.text.trim(),
        code: code,
        newPassword: password,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(message)),
      );
      Navigator.of(context).pop();
    } on DioException catch (error) {
      final data = error.response?.data;
      if (!mounted) return;
      setState(() {
        _error = data is Map<String, dynamic> && data['detail'] != null
            ? data['detail'].toString()
            : 'Unable to reset your password.';
      });
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    _email.dispose();
    _code.dispose();
    _password.dispose();
    _confirm.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Forgot password')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            const SizedBox(height: 20),
            const Icon(Icons.lock_reset_outlined, size: 54),
            const SizedBox(height: 16),
            Text(
              _codeSent ? 'Enter your reset code' : 'Reset your password',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.w900,
                  ),
            ),
            const SizedBox(height: 24),
            TextField(
              controller: _email,
              keyboardType: TextInputType.emailAddress,
              enabled: !_codeSent,
              decoration: const InputDecoration(
                labelText: 'Email address',
                prefixIcon: Icon(Icons.mail_outline),
              ),
            ),
            if (_codeSent) ...[
              const SizedBox(height: 16),
              TextField(
                controller: _code,
                keyboardType: TextInputType.number,
                maxLength: 6,
                decoration: const InputDecoration(
                  labelText: '6-digit reset code',
                  counterText: '',
                  prefixIcon: Icon(Icons.password_outlined),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _password,
                obscureText: _obscure,
                decoration: InputDecoration(
                  labelText: 'New password',
                  prefixIcon: const Icon(Icons.lock_outline),
                  suffixIcon: IconButton(
                    onPressed: () => setState(() => _obscure = !_obscure),
                    icon: Icon(
                      _obscure
                          ? Icons.visibility_outlined
                          : Icons.visibility_off_outlined,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _confirm,
                obscureText: _obscure,
                decoration: const InputDecoration(
                  labelText: 'Confirm new password',
                  prefixIcon: Icon(Icons.lock_outline),
                ),
              ),
            ],
            if (_error != null) ...[
              const SizedBox(height: 14),
              Text(
                _error!,
                textAlign: TextAlign.center,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ],
            if (_message != null) ...[
              const SizedBox(height: 14),
              Text(
                _message!,
                textAlign: TextAlign.center,
              ),
            ],
            const SizedBox(height: 22),
            SizedBox(
              height: 52,
              child: FilledButton(
                onPressed: _loading ? null : (_codeSent ? _reset : _sendCode),
                child: Text(
                  _loading
                      ? 'Please wait...'
                      : _codeSent
                          ? 'Reset password'
                          : 'Send reset code',
                ),
              ),
            ),
            if (_codeSent) ...[
              const SizedBox(height: 10),
              TextButton(
                onPressed:
                    _loading || _seconds > 0 ? null : _sendCode,
                child: Text(
                  _seconds > 0
                      ? 'Send code again in ${_seconds}s'
                      : 'Send code again',
                ),
              ),
              TextButton(
                onPressed: _loading
                    ? null
                    : () {
                        _timer?.cancel();
                        setState(() {
                          _codeSent = false;
                          _seconds = 0;
                          _message = null;
                          _error = null;
                          _code.clear();
                          _password.clear();
                          _confirm.clear();
                        });
                      },
                child: const Text('Use a different email'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
