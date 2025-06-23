import 'package:flutter/material.dart';
import '../widgets/camera_widget.dart';
import '../widgets/keyence_image.dart';
import '../controllers/keyence_image_controller.dart';

class CalculateScoreWidget extends StatefulWidget {
  final KeyenceImageController imgController;
  const CalculateScoreWidget({super.key, required this.imgController});

  @override
  State<CalculateScoreWidget> createState() => _CalculateScoreWidgetState();
}

class _CalculateScoreWidgetState extends State<CalculateScoreWidget> {
  final List<String> methodOptions = ['bus 1', 'bus 2'];
  String selectedMethod1 = 'bus 1';
  String selectedMethod2 = 'bus 1';

  String? linkedFile1;
  String? linkedFile2;

  void _openFileSelectDialog(int index) async {
    final selected = await showDialog<String>(
      context: context,
      builder:
          (context) => Dialog(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
            ),
            backgroundColor: Theme.of(context).colorScheme.surface,
            child: SizedBox(
              width: 400,
              height: 320,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  const Text(
                    'Select a Python script:',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 12),
                  ...[
                    'cross_sectional_area.py',
                    'surface_area_to_volume.py',
                    'average_height.py',
                  ].map(
                    (file) => ListTile(
                      leading: const Icon(Icons.description_outlined),
                      title: Text(file),
                      onTap: () => Navigator.pop(context, file),
                    ),
                  ),
                ],
              ),
            ),
          ),
    );

    if (selected != null) {
      setState(() {
        if (index == 1) {
          linkedFile1 = selected;
        } else {
          linkedFile2 = selected;
        }
      });
    }
  }

  Widget buildDropdownRow(
    int index,
    String selectedMethod,
    ValueChanged<String?> onChanged,
    String? linkedFile,
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: DropdownButton<String>(
                value: selectedMethod,
                isExpanded: true,
                onChanged: onChanged,
                items:
                    methodOptions.map((method) {
                      return DropdownMenuItem(
                        value: method,
                        child: Text(method),
                      );
                    }).toList(),
              ),
            ),
            const SizedBox(width: 8),
            SizedBox(
              height: 48,
              child: ElevatedButton.icon(
                onPressed: () => _openFileSelectDialog(index),
                icon: const Icon(Icons.folder_open),
                label: const Text("Select File"),
                style: ElevatedButton.styleFrom(
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ),
          ],
        ),
        if (linkedFile != null)
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Container(
              constraints: const BoxConstraints(maxWidth: 250),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.green[100],
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                'file: $linkedFile',
                style: const TextStyle(
                  fontWeight: FontWeight.w500,
                  color: Colors.black87,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ),
          ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(12.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          /// 고정 높이 카메라 영역
          Container(
            height: 300,
            padding: const EdgeInsets.all(16.0),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surface,
              borderRadius: BorderRadius.circular(12),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.2),
                  blurRadius: 8,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: const CameraWidget(),
          ),

          const SizedBox(height: 12),

          Expanded(
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16.0),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surface,
                borderRadius: BorderRadius.circular(12),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.2),
                    blurRadius: 8,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  // 왼쪽 화살표 (클릭 가능)
                  GestureDetector(
                    onTap: () {
                      // TODO: 이전 이미지 로직
                    },
                    child: const Padding(
                      padding: EdgeInsets.symmetric(horizontal: 12),
                      child: Icon(Icons.arrow_left, size: 70),
                    ),
                  ),

                  // 이미지 영역
                  Expanded(
                    child: Column(
                      children: [
                        Expanded(
                          child: KeyenceImage(controller: widget.imgController),
                        ),
                      ],
                    ),
                  ),

                  // 오른쪽 화살표 (비활성화)
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 12),
                    child: Icon(
                      Icons.arrow_right,
                      size: 70,
                      color: Colors.grey,
                    ),
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 12),

          /// 설정 + 파일 선택
          Container(
            padding: const EdgeInsets.all(16.0),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surface,
              borderRadius: BorderRadius.circular(12),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.2),
                  blurRadius: 8,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Select Scoring Method',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 12),
                buildDropdownRow(1, selectedMethod1, (val) {
                  if (val != null) setState(() => selectedMethod1 = val);
                }, linkedFile1),
                const SizedBox(height: 16),
                buildDropdownRow(2, selectedMethod2, (val) {
                  if (val != null) setState(() => selectedMethod2 = val);
                }, linkedFile2),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
