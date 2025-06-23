import 'package:flutter/material.dart';
import '../controllers/keyence_image_controller.dart';

class KeyenceImage extends StatefulWidget {
  final KeyenceImageController? controller;
  const KeyenceImage({super.key, this.controller});

  @override
  State<KeyenceImage> createState() => _KeyenceImageState();
}

class _KeyenceImageState extends State<KeyenceImage> {
  ImageProvider? _provider; // ← nullable 로 변경

  @override
  void initState() {
    super.initState();
    widget.controller?.attach(_reload);
    _reload(); // 최초 1회 로드
  }

  void _reload() {
    final ts = DateTime.now().millisecondsSinceEpoch;
    final url = 'http://localhost:8000/image/last_image?t=$ts';
    setState(() => _provider = NetworkImage(url));
  }

  @override
  Widget build(BuildContext context) {
    if (_provider == null) {
      // 아직 로딩 전
      return const Center(child: CircularProgressIndicator());
    }
    return Image(
      image: _provider!,
      key: UniqueKey(), // 캐시 우회
      fit: BoxFit.cover,
      errorBuilder:
          (_, __, ___) => const Text('❌  image not found'), // 404 등 오류 시
    );
  }
}
