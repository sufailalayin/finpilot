import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../auth/auth_screen.dart';
import 'app_security_service.dart';
import 'security_privacy_service.dart';

class SecurityPrivacyScreen extends StatefulWidget {
  const SecurityPrivacyScreen({super.key, required this.api});

  final ApiClient api;

  @override
  State<SecurityPrivacyScreen> createState() => _SecurityPrivacyScreenState();
}

class _SecurityPrivacyScreenState extends State<SecurityPrivacyScreen> {
  late final AppSecurityService _appSecurity = AppSecurityService();
  late final SecurityPrivacyService _privacy =
      SecurityPrivacyService(widget.api);

  bool _loading = true;
  bool _lockEnabled = false;
  bool _biometricEnabled = false;
  bool _biometricAvailable = false;
  List<dynamic> _events = const [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final lock = await _appSecurity.isLockEnabled();
    final biometric = await _appSecurity.isBiometricEnabled();
    final available = await _appSecurity.biometricAvailable();

    List<dynamic> events = const [];
    try {
      events = await _privacy.events();
    } catch (_) {}

    if (!mounted) return;
    setState(() {
      _lockEnabled = lock;
      _biometricEnabled = biometric;
      _biometricAvailable = available;
      _events = events;
      _loading = false;
    });
  }

  Future<void> _setPin() async {
    final pin = TextEditingController();
    final confirm = TextEditingController();

    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(_lockEnabled ? 'Change app PIN' : 'Enable app PIN'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: pin,
              obscureText: true,
              keyboardType: TextInputType.number,
              maxLength: 8,
              decoration: const InputDecoration(labelText: 'New PIN'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: confirm,
              obscureText: true,
              keyboardType: TextInputType.number,
              maxLength: 8,
              decoration: const InputDecoration(labelText: 'Confirm PIN'),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () async {
              final value = pin.text.trim();
              if (value.length < 4 || value != confirm.text.trim()) return;
              await _appSecurity.setPin(value);
              if (context.mounted) Navigator.pop(context, true);
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );

    pin.dispose();
    confirm.dispose();

    if (saved == true) {
      setState(() => _lockEnabled = true);
    }
  }

  Future<void> _disableLock() async {
    await _appSecurity.disableLock();
    if (!mounted) return;
    setState(() {
      _lockEnabled = false;
      _biometricEnabled = false;
    });
  }

  Future<void> _toggleBiometric(bool enabled) async {
    try {
      await _appSecurity.setBiometricEnabled(enabled);
      if (!mounted) return;
      setState(() => _biometricEnabled = enabled);
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Biometric authentication is unavailable.')),
      );
    }
  }

  Future<void> _revokeSessions() async {
    await _privacy.revokeSessions();
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Older sessions have been revoked.')),
    );
    await _load();
  }

  Future<void> _exportData() async {
    try {
      await _privacy.exportData();
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Unable to export data right now.')),
      );
    }
  }

  Future<void> _deleteAccount() async {
    final password = TextEditingController();
    final phrase = TextEditingController();

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Permanently delete account?'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              'This permanently deletes your FinPilot account and recorded financial data.',
            ),
            const SizedBox(height: 14),
            TextField(
              controller: password,
              obscureText: true,
              decoration: const InputDecoration(labelText: 'Password'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: phrase,
              decoration: const InputDecoration(
                labelText: 'Type DELETE MY ACCOUNT',
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () {
              Navigator.pop(
                context,
                phrase.text.trim().toUpperCase() == 'DELETE MY ACCOUNT',
              );
            },
            child: const Text('Delete permanently'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      try {
        await _privacy.deleteAccount(password: password.text);
        await _appSecurity.disableLock();
        if (!mounted) return;
        Navigator.of(context).pushAndRemoveUntil(
          MaterialPageRoute(builder: (_) => AuthScreen(api: widget.api)),
          (_) => false,
        );
      } catch (_) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Account deletion failed. Check your password.')),
        );
      }
    }

    password.dispose();
    phrase.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Security & Privacy',
          style: TextStyle(fontWeight: FontWeight.w800),
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
              children: [
                Card(
                  child: Column(
                    children: [
                      ListTile(
                        leading: const Icon(Icons.pin_outlined),
                        title: const Text('App PIN'),
                        subtitle: Text(
                          _lockEnabled
                              ? 'Required when FinPilot opens'
                              : 'Not enabled',
                        ),
                        trailing: TextButton(
                          onPressed: _setPin,
                          child: Text(_lockEnabled ? 'Change' : 'Enable'),
                        ),
                      ),
                      if (_lockEnabled)
                        ListTile(
                          leading: const Icon(Icons.lock_open_outlined),
                          title: const Text('Disable app lock'),
                          onTap: _disableLock,
                        ),
                      SwitchListTile(
                        secondary: const Icon(Icons.fingerprint),
                        title: const Text('Biometric unlock'),
                        subtitle: Text(
                          _biometricAvailable
                              ? 'Use device biometrics to unlock'
                              : 'Not available on this device',
                        ),
                        value: _biometricEnabled,
                        onChanged: _lockEnabled && _biometricAvailable
                            ? _toggleBiometric
                            : null,
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 14),
                Card(
                  child: Column(
                    children: [
                      ListTile(
                        leading: const Icon(Icons.devices_outlined),
                        title: const Text('Revoke older sessions'),
                        subtitle: const Text(
                          'Signs out access tokens issued before this action.',
                        ),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: _revokeSessions,
                      ),
                      ListTile(
                        leading: const Icon(Icons.download_outlined),
                        title: const Text('Export my data'),
                        subtitle: const Text(
                          'Create a JSON copy of your recorded FinPilot data.',
                        ),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: _exportData,
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 18),
                Text(
                  'Recent security activity',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
                const SizedBox(height: 8),
                if (_events.isEmpty)
                  const Card(
                    child: Padding(
                      padding: EdgeInsets.all(16),
                      child: Text('No security events to show yet.'),
                    ),
                  )
                else
                  ..._events.take(10).map((raw) {
                    final item = Map<String, dynamic>.from(raw as Map);
                    return Card(
                      child: ListTile(
                        leading: const Icon(Icons.security_outlined),
                        title: Text(item['event_type'].toString()),
                        subtitle: Text(
                          (item['description']?.toString() ?? '') +
                              '\n' +
                              item['created_at'].toString(),
                        ),
                      ),
                    );
                  }),
                const SizedBox(height: 24),
                Text(
                  'Danger zone',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
                const SizedBox(height: 8),
                OutlinedButton.icon(
                  onPressed: _deleteAccount,
                  icon: const Icon(Icons.delete_forever_outlined),
                  label: const Text('Delete FinPilot account'),
                ),
              ],
            ),
    );
  }
}
