import 'dart:convert';
import 'dart:html' as html; // ⭐ 핵심
import 'package:http/http.dart' as http;
import 'package:flutter_dotenv/flutter_dotenv.dart';

class OptimizationService {
  static final String _base = dotenv.env['API_BASE_URL']!;
  static String get _resetUrl => '$_base/line_reset';
  static String get _sseUrl => '$_base/run_optimization';

  /// 서버 reset 후 브라우저 EventSource 로 실시간 구독
  static Future<void> startAndListen(
    void Function(Map<String, dynamic>) onData,
  ) async {
    // ① 초기화
    final reset = await http.post(Uri.parse(_resetUrl));
    print('RESET ▶ ${reset.statusCode}');

    // ② EventSource
    final es = html.EventSource(_sseUrl);
    print('🌐 EventSource opened ($_sseUrl)');

    es.onError.listen((e) => print('🚨 SSE error: $e'));
    es.onMessage.listen((html.MessageEvent e) {
      try {
        final map = jsonDecode(e.data as String);
        print('📥 $map');
        onData(map);
      } catch (err) {
        print('💥 JSON decode error: $err');
      }
    });
  }
}
