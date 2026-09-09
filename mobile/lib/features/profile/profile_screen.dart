import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/api_client.dart';
import '../auth/auth_screen.dart';
import '../categories/categories_screen.dart';
import '../auth/auth_service.dart';
import '../subscription/paywall_screen.dart';
import '../subscription/subscription_service.dart';
import '../security/security_privacy_screen.dart';
import '../update/app_update_service.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key, required this.api});

  final ApiClient api;

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  late final AuthService _auth = AuthService(widget.api);
  late final SubscriptionService _subscriptions =
      SubscriptionService(widget.api);

  Map<String, dynamic>? _status;
  bool _loading = true;
  bool _checkingUpdate = false;
  String? _versionText;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final status = await _subscriptions.status();
      if (!mounted) return;
      setState(() {
        _status = status;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _loading = false);
    }
  }

  Future<void> _checkForUpdates() async {
    if (_checkingUpdate) return;
    setState(() => _checkingUpdate = true);
    try {
      final update = await AppUpdateService(widget.api).check();
      if (!mounted) return;
      setState(() {
        _versionText =
            'Installed ${update.currentVersion} (${update.currentBuild}) • Latest ${update.latestVersion} (${update.latestBuild})';
      });

      await showDialog<void>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          title: Text(
            update.updateAvailable
                ? 'FinPilot update available'
                : 'FinPilot is up to date',
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Installed: ${update.currentVersion} (${update.currentBuild})'),
              const SizedBox(height: 4),
              Text('Latest: ${update.latestVersion} (${update.latestBuild})'),
              if (update.releaseNotes != null &&
                  update.releaseNotes!.trim().isNotEmpty) ...[
                const SizedBox(height: 14),
                const Text(
                  'What’s new',
                  style: TextStyle(fontWeight: FontWeight.w800),
                ),
                const SizedBox(height: 6),
                Text(update.releaseNotes!),
              ],
              if (update.updateAvailable &&
                  (update.updateUrl == null ||
                      update.updateUrl!.trim().isEmpty)) ...[
                const SizedBox(height: 12),
                const Text(
                  'An update is configured, but the download link has not been added in Admin yet.',
                ),
              ],
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(),
              child: const Text('Close'),
            ),
            if (update.updateAvailable &&
                update.updateUrl != null &&
                update.updateUrl!.trim().isNotEmpty)
              FilledButton(
                onPressed: () async {
                  final uri = Uri.tryParse(update.updateUrl!.trim());
                  if (uri == null) return;
                  Navigator.of(dialogContext).pop();
                  await launchUrl(uri, mode: LaunchMode.externalApplication);
                },
                child: Text(
                  update.distribution == 'play_store'
                      ? 'Open Google Play'
                      : 'Update now',
                ),
              ),
          ],
        ),
      );
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Unable to check for updates right now.'),
        ),
      );
    } finally {
      if (mounted) setState(() => _checkingUpdate = false);
    }
  }

  Future<void> _logout() async {
    await _auth.logout();
    if (!mounted) return;
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => AuthScreen(api: widget.api)),
      (_) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    final status = _status?['status']?.toString() ?? 'unknown';
    final plan = _status?['plan_code']?.toString() ?? 'free';
    final trialEnd = _status?['trial_ends_at']?.toString();
    final paidUntil = _status?['paid_until']?.toString();
    final billingPlanName = _status?['billing_plan_name']?.toString();

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Profile',
          style: TextStyle(fontWeight: FontWeight.w800),
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
        children: [
          Container(
            padding: const EdgeInsets.all(22),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surface,
              borderRadius: BorderRadius.circular(24),
              border: Border.all(
                color: Theme.of(context).colorScheme.outlineVariant,
              ),
            ),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 28,
                  backgroundColor:
                      Theme.of(context).colorScheme.primaryContainer,
                  child: const Icon(Icons.person, size: 28),
                ),
                const SizedBox(width: 16),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'FinPilot Account',
                        style: TextStyle(
                          fontWeight: FontWeight.w800,
                          fontSize: 18,
                        ),
                      ),
                      SizedBox(height: 3),
                      Text('Personal finance workspace'),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 18),
          if (_loading)
            const Center(child: CircularProgressIndicator())
          else
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.primaryContainer,
                borderRadius: BorderRadius.circular(22),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'FINPILOT PRO',
                    style: TextStyle(
                      fontWeight: FontWeight.w800,
                      letterSpacing: 1,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    plan.toUpperCase() + ' • ' + status.toUpperCase(),
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  if (billingPlanName != null && billingPlanName.isNotEmpty) ...[
                    const SizedBox(height: 6),
                    Text(billingPlanName),
                  ],
                  if (status == 'trial' && trialEnd != null) ...[
                    const SizedBox(height: 8),
                    Text('Trial ends: ' + trialEnd),
                  ],
                  if (status == 'active' && paidUntil != null) ...[
                    const SizedBox(height: 8),
                    Text('Paid until: ' + paidUntil),
                  ],
                  const SizedBox(height: 14),
                  FilledButton(
                    onPressed: () => Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => PaywallScreen(api: widget.api),
                      ),
                    ),
                    child: const Text('Manage subscription'),
                  ),
                ],
              ),
            ),
          const SizedBox(height: 18),
          ListTile(
            leading: const Icon(Icons.shield_outlined),
            title: const Text('Security & Privacy'),
            subtitle: const Text(
              'App lock, sessions, export and account controls',
            ),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute(
                builder: (_) => SecurityPrivacyScreen(api: widget.api),
              ),
            ),
          ),
          const ListTile(
            leading: Icon(Icons.currency_rupee),
            title: Text('Currency'),
            subtitle: Text('Indian Rupee (INR)'),
          ),
          ListTile(
            leading: const Icon(Icons.category_outlined),
            title: const Text('Categories'),
            subtitle: const Text('Manage income and expense categories'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute(
                builder: (_) => CategoriesScreen(api: widget.api),
              ),
            ),
          ),
          ListTile(
            leading: const Icon(Icons.system_update_alt),
            title: const Text('App update'),
            subtitle: Text(
              _versionText ??
                  'Check installed version and available FinPilot updates',
            ),
            trailing: _checkingUpdate
                ? const SizedBox(
                    width: 22,
                    height: 22,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.chevron_right),
            onTap: _checkingUpdate ? null : _checkForUpdates,
          ),
          const ListTile(
            leading: Icon(Icons.info_outline),
            title: Text('About'),
            subtitle: Text('FinPilot by Hastron Ventures'),
          ),
          const SizedBox(height: 20),
          OutlinedButton.icon(
            onPressed: _logout,
            icon: const Icon(Icons.logout),
            label: const Text('Sign out'),
          ),
        ],
      ),
    );
  }
}
