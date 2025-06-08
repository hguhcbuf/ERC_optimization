// lib/services/bo_api.dart (fixed)
import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'dart:async';
// Ensure you have defined Parameter in lib/models/parameter.dart:
// class Parameter { final String name; final double min, max; Map<String,dynamic> toJson() => {'name':name,'min':min,'max':max}; }
import '../models/parameter.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

/// Service class for communicating with the Bayesian Optimization backend
class BoApi {
  static final String _baseUrl = dotenv.env['API_BASE_URL']!;
  // static const String _baseUrl = 'http://localhost:8000';

  /// Fetches next single candidate point via POST /get_suggestion
  static Future<List<double>> fetchNextSuggestion(
    String acquisition,
    List<Parameter> parameters,
  ) async {
    final uri = Uri.parse('$_baseUrl/get_suggestion');
    final body = jsonEncode({
      'acquisition': acquisition,
      'parameters': parameters.map((p) => p.toJson()).toList(),
    });

    final response = await http
        .post(uri, headers: {'Content-Type': 'application/json'}, body: body)
        .timeout(const Duration(seconds: 10));

    if (response.statusCode != 200) {
      throw Exception('Failed to fetch suggestion: ${response.statusCode}');
    }

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final raw = data['next_x'];
    if (raw is! List) {
      throw Exception('Unexpected response format: next_x is not a list');
    }
    return raw.map((v) {
      if (v is num) return v.toDouble();
      throw Exception('Invalid element in next_x: \$v');
    }).toList();
  }

  /// Submits evaluated scores and returns total evaluations count
  static Future<int> submitScores(
    List<List<double>> candidates,
    List<double> scores,
  ) async {
    final uri = Uri.parse('$_baseUrl/submit');
    final response = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'candidates': candidates, 'scores': scores}),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to submit scores: ${response.statusCode}');
    }
    debugPrint('bo_api response : $response');
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final total = body['total_evaluations'];
    if (total is! int) {
      throw Exception('Unexpected response: total_evaluations is not int');
    }
    return total;
  }

  static Future<void> resetBackend() async {
    try {
      final res = await http.post(Uri.parse('$_baseUrl/reset'));
      if (res.statusCode == 200) {
        debugPrint('Backend reset successful');
      } else {
        debugPrint('Reset failed: ${res.body}');
      }
    } catch (e) {
      debugPrint('Error calling reset: $e');
    }
  }
}
