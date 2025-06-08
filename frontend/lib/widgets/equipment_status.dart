import 'package:flutter/material.dart';

class EquipmentStatus extends StatelessWidget {
  final Map<String, dynamic>? result;

  const EquipmentStatus({super.key, this.result});

  @override
  Widget build(BuildContext context) {
    if (result == null || result!['history'] == null) {
      return const Center(
        child: Text(
          'No equipments registered',
          style: TextStyle(fontSize: 16, fontStyle: FontStyle.italic),
        ),
      );
    }

    // 🔥 일단 더미 heatmap 모양으로 대체
    // (나중에 진짜 heatmap 데이터 나오면 수정)
    return Container(
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey),
        borderRadius: BorderRadius.circular(8),
        color: Colors.blue[50],
      ),
      padding: const EdgeInsets.all(12.0),
      child: const Center(
        child: Text(
          'Acquisition Function Heatmap\n(Placeholder)',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 24),
        ),
      ),
    );
  }
}
