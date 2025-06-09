import 'package:flutter/material.dart';
import '../services/pressure_api.dart';
import 'dart:async';

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

  void handleMove(String direction) {
    print("Move $direction pressed");
    // TODO: FastAPI Move API 호출
  }

  void handleMoveExecute() {
    print("Move Execute pressed");
    // TODO: FastAPI Move Execute API 호출
  }

  void changePressurePressed(double pressure) async {
    await PressureApi.changePressure(pressure);
  }

  void handleCapture() {
    print("Capture pressed");
    // TODO: FastAPI Capture API 호출
  }

  // void handleExtrude() async {
  //   await PressureApi.extrudeOn();
  // }

  void handleLoop() {
    print("Loop pressed");
    // TODO: FastAPI Loop API 호출
  }

  @override
  Widget build(BuildContext context) {
    final TextEditingController pressureController = TextEditingController();

    return SingleChildScrollView(
      child: Column(
        children: [
          // Stop & Initialize 버튼
          Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: 16.0,
              vertical: 8.0,
            ),
            child: Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    onPressed: handleStop,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color.fromARGB(255, 172, 11, 2),
                      padding: const EdgeInsets.symmetric(vertical: 32.0),
                    ),
                    child: const Text('Stop', style: TextStyle(fontSize: 26)),
                  ),
                ),
                const SizedBox(width: 16.0),
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

          // Stop/Initialize 버튼 밑 간격
          const SizedBox(height: 16.0),

          // 앞/뒤/좌/우/상/하 이동 버튼 (좌우로 꽉 차게)
          Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: 16.0,
              vertical: 8.0,
            ),
            child: Wrap(
              spacing: 8.0,
              runSpacing: 8.0,
              alignment: WrapAlignment.center,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton(
                        onPressed: () => handleMove("Forward"),
                        child: const Text('Forward'),
                      ),
                    ),
                    const SizedBox(width: 8.0),
                    Expanded(
                      child: ElevatedButton(
                        onPressed: () => handleMove("Backward"),
                        child: const Text('Backward'),
                      ),
                    ),
                  ],
                ),
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton(
                        onPressed: () => handleMove("Left"),
                        child: const Text('Left'),
                      ),
                    ),
                    const SizedBox(width: 8.0),
                    Expanded(
                      child: ElevatedButton(
                        onPressed: () => handleMove("Right"),
                        child: const Text('Right'),
                      ),
                    ),
                  ],
                ),
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton(
                        onPressed: () => handleMove("Up"),
                        child: const Text('Up'),
                      ),
                    ),
                    const SizedBox(width: 8.0),
                    Expanded(
                      child: ElevatedButton(
                        onPressed: () => handleMove("Down"),
                        child: const Text('Down'),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          // 이동 버튼
          Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: 16.0,
              vertical: 8.0,
            ),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: handleMoveExecute,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 24.0),
                ),
                child: const Text('Move', style: TextStyle(fontSize: 20)),
              ),
            ),
          ),

          // 압력 분사 버튼 + 입력란
          Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: 16.0,
              vertical: 8.0,
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: pressureController,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                      labelText: 'Pressure [kPa]',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                const SizedBox(width: 16.0),
                ElevatedButton(
                  onPressed: () {
                    final pressure = double.tryParse(pressureController.text);
                    if (pressure != null) {
                      changePressurePressed(pressure);
                    } else {
                      print("Invalid pressure value");
                    }
                  },
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(
                      vertical: 24.0,
                      horizontal: 24.0,
                    ),
                  ),
                  child: const Text('Change', style: TextStyle(fontSize: 20)),
                ),
              ],
            ),
          ),

          // Extrude 버튼
          Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: 16.0,
              vertical: 8.0,
            ),
            child: SizedBox(
              width: double.infinity,
              child: GestureDetector(
                onTapDown: (_) async {
                  await PressureApi.extrudeOn();
                },
                onTapUp: (_) async {
                  await PressureApi.extrudeOff();
                },
                onTapCancel: () async {
                  // 드래그로 취소되는 경우도 잡기
                  await PressureApi.extrudeOff();
                },
                child: Container(
                  width: 200,
                  height: 50,
                  color: Theme.of(context).colorScheme.primary,
                  child: Center(
                    child: Text(
                      'Extrude',
                      style: TextStyle(color: Colors.white, fontSize: 20),
                    ),
                  ),
                ),
              ),
            ),
          ),

          // 촬영 버튼
          Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: 16.0,
              vertical: 8.0,
            ),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: handleCapture,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 24.0),
                ),
                child: const Text(
                  'Scan Profiler',
                  style: TextStyle(fontSize: 20),
                ),
              ),
            ),
          ),

          // Loop 버튼
          Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: 16.0,
              vertical: 8.0,
            ),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: handleLoop,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 24.0),
                ),
                child: const Text('Loop', style: TextStyle(fontSize: 20)),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
