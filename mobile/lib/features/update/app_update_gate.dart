import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/api_client.dart';
import 'app_update_service.dart';

class AppUpdateGate extends StatefulWidget {
  const AppUpdateGate({
    super.key,
    required this.api,
    required this.child,
  });

  final ApiClient api;
  final Widget child;

  @override
  State<AppUpdateGate> createState() => _AppUpdateGateState();
}

class _AppUpdateGateState extends State<AppUpdateGate> {
  late final Future<AppUpdateState?> _future = _check();
  bool _optionalPromptScheduled = false;

  Future<AppUpdateState?> _check() async {
    try {
      return await AppUpdateService(widget.api).check();
    } catch (_) {
      return null;
    }
  }

  Future<void> _openUpdate(AppUpdateState state) async {
    final raw = state.updateUrl?.trim();
    if (raw == null || raw.isEmpty) return;
    final uri = Uri.tryParse(raw);
    if (uri == null) return;
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  void _showOptionalUpdate(AppUpdateState state) {
    if (_optionalPromptScheduled) return;
    _optionalPromptScheduled = true;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      showDialog<void>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          title: const Text('FinPilot update available'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Version ${state.latestVersion} is available. '
                  'You are using ${state.currentVersion}.',
                ),
                if (state.releaseNotes != null &&
                    state.releaseNotes!.trim().isNotEmpty) ...[
                  const SizedBox(height: 12),
                  const Text(
                    'What’s new',
                    style: TextStyle(fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 6),
                  Text(state.releaseNotes!),
                ],
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(),
              child: const Text('Later'),
            ),
            FilledButton(
              onPressed: () {
                Navigator.of(dialogContext).pop();
                _openUpdate(state);
              },
              child: const Text('Update now'),
            ),
          ],
        ),
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<AppUpdateState?>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        final state = snapshot.data;
        if (state == null || !state.enabled || !state.updateAvailable) {
          return widget.child;
        }

        if (state.updateRequired) {
          return Scaffold(
            body: SafeArea(
              child: Center(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(28),
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 480),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.system_update_alt, size: 64),
                        const SizedBox(height: 20),
                        const Text(
                          'Update required',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontWeight: FontWeight.w900,
                            fontSize: 28,
                          ),
                        ),
                        const SizedBox(height: 12),
                        Text(
                          'This FinPilot build is no longer supported. '
                          'Please update to version ${state.latestVersion} to continue.',
                          textAlign: TextAlign.center,
                        ),
                        if (state.releaseNotes != null &&
                            state.releaseNotes!.trim().isNotEmpty) ...[
                          const SizedBox(height: 16),
                          Text(
                            state.releaseNotes!,
                            textAlign: TextAlign.center,
                          ),
                        ],
                        const SizedBox(height: 24),
                        SizedBox(
                          width: double.infinity,
                          child: FilledButton.icon(
                            onPressed: state.updateUrl?.trim().isNotEmpty == true
                                ? () => _openUpdate(state)
                                : null,
                            icon: const Icon(Icons.download_outlined),
                            label: Text(
                              state.distribution == 'play_store'
                                  ? 'Open Google Play'
                                  : 'Get latest FinPilot',
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          );
        }

        _showOptionalUpdate(state);
        return widget.child;
      },
    );
  }
}
