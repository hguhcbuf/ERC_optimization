import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'dart:async';
import '../models/parameter.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

class PressureApi {
  static final String _baseUrl = dotenv.env['API_BASE_URL']!;

  static Future<void> extrudeOn() async {
    final uri = Uri.parse('$_baseUrl/pressure/extrude/on');

    final response = await http.post(uri);

    if (response.statusCode == 200) {
      print(response.body);
    } else {
      print('Extrude ON 실패: ${response.statusCode}');
    }
  }

  static Future<void> extrudeOff() async {
    final uri = Uri.parse('$_baseUrl/pressure/extrude/off');

    final response = await http.post(uri);

    if (response.statusCode == 200) {
      print(response.body);
    } else {
      print('Extrude OFF 실패: ${response.statusCode}');
    }
  }

  static Future<void> changePressure(double pressure) async {
    final uri = Uri.parse('$_baseUrl/pressure/apply');

    try {
      final response = await http.post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'pressure': pressure}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        print('[SUCCESS] ${data["message"]}');
      } else {
        print('[ERROR] ${response.statusCode}: ${response.body}');
      }
    } catch (e) {
      print('[ERROR] API 호출 실패: $e');
    }
  }
}
