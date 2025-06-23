import 'package:flutter/material.dart';
import '../services/joggerMode_api.dart';
import 'dart:async';

class JoggerModeWidget extends StatelessWidget {
  const JoggerModeWidget({super.key});

  // void HomePositionPressed() {
  //   print("Stop pressed");
  //   // TODO: FastAPI Stop API 호출
  // }

  void HomePositionPressed() async {
    await JoggerModeAPI.MoveToHomePosition();
  }

  void SetOriginPressed() async {
    await JoggerModeAPI.SetOrigin();
  }

  @override
  Widget build(BuildContext context) {
    /* ───── 공통 버튼 스타일 ───── */
    final buttonStyle = ElevatedButton.styleFrom(
      minimumSize: const Size(64, 64), // 조이스틱 기본 크기
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      backgroundColor: Theme.of(context).colorScheme.primary,
      foregroundColor: Colors.white,
      elevation: 4,
    );

    // 폭은 레이아웃에 맡기고 높이만 48 px 로 고정(상단·하단용)
    final bigButtonStyle = buttonStyle.copyWith(
      minimumSize: MaterialStateProperty.all(const Size.fromHeight(48)),
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        /* ───── 1. Home / Set Origin ───── */
        ElevatedButton.icon(
          onPressed: () {
            HomePositionPressed();
          },
          icon: const Icon(Icons.home),
          label: const Text('Home Position'),
          style: bigButtonStyle,
        ),
        const SizedBox(height: 16),
        ElevatedButton.icon(
          onPressed: () {
            SetOriginPressed();
          },
          icon: const Icon(Icons.my_location),
          label: const Text('Set Origin'),
          style: bigButtonStyle,
        ),

        /* ───── 2. XY + Z 조이스틱 ───── */
        const SizedBox(height: 32),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // ■ XY 4-way
            Column(
              children: [
                ElevatedButton(
                  onPressed: () {
                    /* Y+ */
                  },
                  style: buttonStyle,
                  child: const Icon(Icons.keyboard_arrow_up_rounded, size: 32),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    ElevatedButton(
                      onPressed: () {
                        /* X- */
                      },
                      style: buttonStyle,
                      child: const Icon(
                        Icons.keyboard_arrow_left_rounded,
                        size: 32,
                      ),
                    ),
                    const SizedBox(width: 8),
                    ElevatedButton(
                      onPressed: null, // 중앙 더미(정지)
                      style: buttonStyle,
                      child: const Icon(Icons.stop),
                    ),
                    const SizedBox(width: 8),
                    ElevatedButton(
                      onPressed: () {
                        /* X+ */
                      },
                      style: buttonStyle,
                      child: const Icon(
                        Icons.keyboard_arrow_right_rounded,
                        size: 32,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                ElevatedButton(
                  onPressed: () {
                    /* Y- */
                  },
                  style: buttonStyle,
                  child: const Icon(
                    Icons.keyboard_arrow_down_rounded,
                    size: 32,
                  ),
                ),
              ],
            ),

            const SizedBox(width: 24),

            // ■ Z+ / Z-
            Column(
              children: [
                ElevatedButton(
                  onPressed: () {
                    /* Z+ */
                  },
                  style: buttonStyle,
                  child: const Icon(Icons.arrow_upward, size: 28),
                ),
                const SizedBox(height: 8),
                ElevatedButton(
                  onPressed: () {
                    /* Z- */
                  },
                  style: buttonStyle,
                  child: const Icon(Icons.arrow_downward, size: 28),
                ),
              ],
            ),
          ],
        ),

        /* ───── 3. 압력 입력 + Change ───── */
        const SizedBox(height: 32),
        Row(
          children: [
            Expanded(
              child: TextField(
                keyboardType: const TextInputType.numberWithOptions(
                  decimal: true,
                ),
                decoration: InputDecoration(
                  hintText: 'Pressure [kPa]',
                  filled: true,
                  fillColor: Theme.of(context).colorScheme.background,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(8),
                    borderSide: BorderSide.none,
                  ),
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 14,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 12),
            ElevatedButton(
              onPressed: () {
                /* Change pressure */
              },
              style: bigButtonStyle.copyWith(
                minimumSize: MaterialStateProperty.all(
                  const Size(100, 48),
                ), // 최소폭 100
              ),
              child: const Text('Change'),
            ),
          ],
        ),

        /* ───── 4. Extrude / Scan Profiler ───── */
        const SizedBox(height: 24),
        Row(
          children: [
            Expanded(
              child: ElevatedButton(
                onPressed: () {
                  /* Extrude */
                },
                style: bigButtonStyle,
                child: const Text('Extrude'),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: ElevatedButton(
                onPressed: () {
                  /* Scan profiler */
                },
                style: bigButtonStyle,
                child: const Text('Scan Profiler'),
              ),
            ),
          ],
        ),
      ],
    );
  }
}
