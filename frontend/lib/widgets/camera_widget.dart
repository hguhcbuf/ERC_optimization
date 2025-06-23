import 'package:flutter/material.dart';
import 'package:camera/camera.dart';

/// 실시간 웹캠 미리보기 위젯
///
/// - Logitech 등 USB·내장 카메라를 자동 검색해 첫 번째 장치를 사용.
/// - 권한 거부·장치 미연결 등 실패 시 Placeholder(아이콘 + 메시지) 표시.
/// - 백엔드 없이 로컬에서 `flutter run -d chrome` 으로 테스트 가능
class CameraWidget extends StatefulWidget {
  const CameraWidget({super.key});

  @override
  State<CameraWidget> createState() => _CameraWidgetState();
}

class _CameraWidgetState extends State<CameraWidget> {
  CameraController? _controller;
  Future<void>? _initializeFuture;
  String? _errorMessage; // ‘No camera found’ 또는 예외 메시지

  @override
  void initState() {
    super.initState();
    _initCamera();
  }

  Future<void> _initCamera() async {
    try {
      final List<CameraDescription> cams = await availableCameras();
      if (cams.isEmpty) {
        setState(() => _errorMessage = 'No camera found');
        return;
      }

      // 첫 번째 카메라 사용 (필요하면 cams.firstWhere 로 조건 걸어 선택)
      _controller = CameraController(
        cams.first,
        ResolutionPreset.medium, // 720p 이하 권장(웹)
        enableAudio: false,
      );

      _initializeFuture = _controller!.initialize();
      await _initializeFuture;
      if (mounted) setState(() {});
    } catch (e) {
      setState(() => _errorMessage = 'Camera error: $e');
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // 오류 시 placeholder
    if (_errorMessage != null) {
      return _buildPlaceholder(context, _errorMessage!);
    }

    // 초기화 진행 중
    if (_controller == null || !_controller!.value.isInitialized) {
      return const Center(child: CircularProgressIndicator());
    }

    // 성공적으로 초기화된 경우 미리보기
    return AspectRatio(
      aspectRatio: _controller!.value.aspectRatio,
      child: CameraPreview(_controller!),
    );
  }

  /* ───────── 헬퍼: 빈 화면 UI ───────── */
  Widget _buildPlaceholder(BuildContext context, String msg) {
    return Container(
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.background,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.videocam_off, size: 64, color: Colors.grey),
            const SizedBox(height: 12),
            Text(msg, style: Theme.of(context).textTheme.bodyLarge),
          ],
        ),
      ),
    );
  }
}
