import 'package:flutter/material.dart';

class EquipmentStatus extends StatelessWidget {
  const EquipmentStatus({super.key});

  void handleStop() {
    print("Stop pressed");
    // TODO: FastAPI Stop API 호출
  }

  void handleInitialize() {
    print("Initialize pressed");
    // TODO: FastAPI Initialize API 호출
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // 좌우 버튼
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
          child: Row(
            children: [
              Expanded(
                child: ElevatedButton(
                  onPressed: handleStop,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color.fromARGB(255, 172, 11, 2),
                    padding: const EdgeInsets.symmetric(
                      vertical: 32.0,
                    ), // 버튼 높이
                  ),
                  child: const Text(
                    'Stop',
                    style: TextStyle(fontSize: 26), // 글자 크기
                  ),
                ),
              ),
              const SizedBox(width: 16.0), // 버튼 사이 간격
              Expanded(
                child: ElevatedButton(
                  onPressed: handleInitialize,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Theme.of(context).colorScheme.primary,
                    padding: const EdgeInsets.symmetric(vertical: 32.0),
                  ),
                  child: const Text(
                    'Initialize',
                    style: TextStyle(fontSize: 26),
                  ),
                ),
              ),
            ],
          ),
        ),
        const Center(
          child: Text(
            '-',
            style: TextStyle(fontSize: 16, fontStyle: FontStyle.italic),
          ),
        ),
      ],
    );
  }
}
