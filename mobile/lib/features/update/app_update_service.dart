import 'package:package_info_plus/package_info_plus.dart';

import '../../core/api_client.dart';

class AppUpdateState {
  const AppUpdateState({
    required this.currentVersion,
    required this.currentBuild,
    required this.latestVersion,
    required this.latestBuild,
    required this.minimumVersion,
    required this.minimumBuild,
    required this.updateUrl,
    required this.releaseNotes,
    required this.distribution,
    required this.enabled,
  });

  final String currentVersion;
  final int currentBuild;
  final String latestVersion;
  final int latestBuild;
  final String minimumVersion;
  final int minimumBuild;
  final String? updateUrl;
  final String? releaseNotes;
  final String distribution;
  final bool enabled;

  bool get updateAvailable => enabled && currentBuild < latestBuild;
  bool get updateRequired => enabled && currentBuild < minimumBuild;
}

class AppUpdateService {
  AppUpdateService(this._api);

  final ApiClient _api;

  Future<AppUpdateState> check() async {
    final package = await PackageInfo.fromPlatform();
    final response = await _api.dio.get('/app-release');
    final data = Map<String, dynamic>.from(response.data as Map);

    return AppUpdateState(
      currentVersion: package.version,
      currentBuild: int.tryParse(package.buildNumber) ?? 1,
      latestVersion: data['latest_version']?.toString() ?? package.version,
      latestBuild: int.tryParse(data['latest_build_number']?.toString() ?? '') ??
          (int.tryParse(package.buildNumber) ?? 1),
      minimumVersion: data['minimum_version']?.toString() ?? package.version,
      minimumBuild:
          int.tryParse(data['minimum_build_number']?.toString() ?? '') ?? 1,
      updateUrl: data['update_url']?.toString(),
      releaseNotes: data['release_notes']?.toString(),
      distribution: data['distribution']?.toString() ?? 'apk',
      enabled: data['is_update_enabled'] == true,
    );
  }
}
