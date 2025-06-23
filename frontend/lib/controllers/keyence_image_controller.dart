import 'package:flutter/foundation.dart';

class KeyenceImageController {
  VoidCallback? _reloadImage; // 여전히 private

  // KeyenceImage 가 자신을 등록할 때 사용
  void attach(VoidCallback cb) => _reloadImage = cb;

  // 외부 호출용
  void reload() => _reloadImage?.call();
}
