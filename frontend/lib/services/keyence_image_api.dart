import 'package:http/http.dart' as http;
import 'package:flutter_dotenv/flutter_dotenv.dart';

class KeyenceImageAPI {
  static final String _baseUrl = dotenv.env['API_BASE_URL']!;

  /// GET latest Keyence image as bytes
  static Future<http.Response?> fetchLastImage() async {
    try {
      final uri = Uri.parse('$_baseUrl/image/last_image');
      final response = await http.get(uri);

      if (response.statusCode == 200) {
        return response;
      } else {
        print('Keyence 이미지 가져오기 실패: ${response.statusCode}');
        return null;
      }
    } catch (e) {
      print('Keyence 이미지 요청 중 오류: $e');
      return null;
    }
  }
}
