import 'package:flutter/material.dart';

class DeviceStatusWidget extends StatelessWidget {
  final Map<String, int> statusCodes;

  const DeviceStatusWidget({super.key, required this.statusCodes});

  Color getColorFromCode(int code) {
    switch (code) {
      case 0:
        return Colors.green;
      case 1:
        return Colors.yellow;
      case 2:
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.start, // 왼쪽 정렬
      crossAxisAlignment: CrossAxisAlignment.start,
      children:
          statusCodes.entries.map((entry) {
            return Expanded(
              // ✅ Row 안에서 박스들이 균등 분배
              child: Container(
                margin: const EdgeInsets.symmetric(
                  horizontal: 4.0,
                  vertical: 8.0,
                ),
                padding: const EdgeInsets.all(12.0),
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.secondary,
                  border: Border.all(color: Colors.black),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      width: 12,
                      height: 12,
                      decoration: BoxDecoration(
                        color: getColorFromCode(entry.value),
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Flexible(
                      // ✅ 텍스트 길면 자동 줄이기
                      child: Text(
                        entry.key,
                        style: const TextStyle(fontSize: 16),
                        overflow: TextOverflow.ellipsis, // 긴 텍스트 ... 처리
                        maxLines: 1,
                        softWrap: false,
                      ),
                    ),
                  ],
                ),
              ),
            );
          }).toList(),
    );
  }
}
