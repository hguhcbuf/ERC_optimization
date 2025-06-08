import 'package:flutter/material.dart';
import 'screens/bo_screen.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

Future<void> main() async {
  // 1) .env 파일 로드 (프로젝트 루트의 .env)
  await dotenv.load(fileName: ".env");

  runApp(const BOApp());
}

class BOApp extends StatelessWidget {
  const BOApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Bayesian Optimization',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark, // 🌙 다크 테마 사용
        useMaterial3: false,
        scaffoldBackgroundColor: const Color(0xFF1E1E2E), // 🖤 메인 배경
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF2B2B3A), // 헤더 다크
          foregroundColor: Colors.white,
          elevation: 4,
          centerTitle: true,
        ),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF4E8AF0), // 💙 버튼 등 주요 강조 색
          secondary: Color(0xFF3A3F58), // 사이드바/카드 배경
          surface: Color(0xFF2B2B3A), // 컨테이너/Card
          background: Color(0xFF1E1E2E),
          onPrimary: Colors.white,
          onSecondary: Colors.white,
          onSurface: Colors.white70, // 일반 텍스트
        ),
      ),
      home: const BOScreen(),
    );
  }
}
