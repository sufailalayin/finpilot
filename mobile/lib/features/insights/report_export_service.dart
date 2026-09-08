import 'dart:convert';
import 'dart:io';

import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

class ReportExportService {
  String _csvCell(dynamic value) {
    final text = value?.toString() ?? '';
    return '"' + text.replaceAll('"', '""') + '"';
  }

  Future<void> shareJson(Map<String, dynamic> report) async {
    final dir = await getTemporaryDirectory();
    final file = File(dir.path + '/finpilot-finance-report.json');
    await file.writeAsString(
      const JsonEncoder.withIndent('  ').convert(report),
      flush: true,
    );
    await Share.shareXFiles(
      [XFile(file.path)],
      text: 'FinPilot finance report',
    );
  }

  Future<void> shareTrendCsv(Map<String, dynamic> report) async {
    final trend = (report['trend'] as List<dynamic>?) ?? const [];
    final rows = <String>[
      'month,income,expenses,net,savings_rate,net_worth',
    ];
    for (final raw in trend) {
      final item = Map<String, dynamic>.from(raw as Map);
      rows.add([
        item['month'],
        item['income'],
        item['expenses'],
        item['net'],
        item['savings_rate'],
        item['net_worth'],
      ].map(_csvCell).join(','));
    }

    final dir = await getTemporaryDirectory();
    final file = File(dir.path + '/finpilot-financial-trend.csv');
    await file.writeAsString(rows.join('\n'), flush: true);
    await Share.shareXFiles(
      [XFile(file.path)],
      text: 'FinPilot financial trend report',
    );
  }
}
