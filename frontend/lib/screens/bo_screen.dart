import 'package:flutter/material.dart';
import '../widgets/result_chart.dart';
import '../widgets/device_status_widget.dart';
import '../widgets/bo_control_panel.dart';
import '../widgets/equipment_status.dart';
import '../widgets/sidebar_widget.dart';
import '../services/bo_api.dart';
import 'dart:math';
import '../models/parameter.dart';

class BOScreen extends StatefulWidget {
  const BOScreen({super.key});

  @override
  State<BOScreen> createState() => _BOScreenState();
}

class _BOScreenState extends State<BOScreen> {
  String acquisition = 'ei';
  final GlobalKey<BOControlPanelState> _panelKey =
      GlobalKey<BOControlPanelState>();
  int _evalCount = 0;
  bool _loading = false;
  List<List<double>> _currentBatch = [];

  final initController = TextEditingController(text: '5');
  final iterController = TextEditingController(text: '10');

  Map<String, dynamic>? result;
  bool loading = false;
  Map<String, dynamic>? _lastConfig;
  List<Map<String, dynamic>> _history = [];
  List<double>? currentX;
  final TextEditingController scoreController = TextEditingController();

  final Map<String, int> deviceStatusCodes = {
    'Linear Stage': 0,
    'Pneumatic Controller': 0,
    'Air Compressor': 0,
    'Laser Profiler': 1,
    'OCT': 2,
    'IR Camera': 2,
  };

  // Sidebar 부분

  bool _isSidebarVisible = true;

  final TextEditingController searchController = TextEditingController();
  List<String> filteredMenuLists = [];
  List<String> sidebarMenuLists = [
    'optimization log 1',
    'optimization log 2',
    'optimization log 3',
  ];

  // bo 설정 부분
  final List<String> parameterOptions = [
    'Line Speed',
    'Standoff Distance',
    'Extrusion Pressure',
    'Reservior Temperature',
    'Ink Viscosity',
  ];

  @override
  void initState() {
    super.initState();
    filteredMenuLists = sidebarMenuLists; // 처음에는 모두 보이게
    searchController.addListener(applySearchFilter); // 검색창 리스너 등록
    BoApi.resetBackend();
  }

  //debug log 보여주기
  final List<String> _debugLog = [];
  final ScrollController _logScrollController = ScrollController();

  // 새로운 로그를 찍는 헬퍼
  void _appendLog(String message) {
    setState(() {
      _debugLog.add(message);
      // 메모리 절약을 위해 오래된 로그를 잘라내고 싶다면:
      // if (_debugLog.length > 200) _debugLog.removeAt(0);
    });
    // 빌드가 끝난 뒤 스크롤을 맨 아래로
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_logScrollController.hasClients) {
        _logScrollController.jumpTo(
          _logScrollController.position.maxScrollExtent,
        );
      }
    });
  }

  void handleAddNewOptimization() async {
    String? newName = await showDialog<String>(
      context: context,
      builder: (context) {
        final TextEditingController nameController = TextEditingController();
        return AlertDialog(
          title: const Text('새 최적화 로그 추가'),
          content: TextField(
            controller: nameController,
            decoration: const InputDecoration(hintText: '파일명 입력'),
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop(); // 아무것도 추가 안함
              },
              child: const Text('취소'),
            ),
            TextButton(
              onPressed: () {
                final text = nameController.text.trim();
                if (text.isNotEmpty) {
                  Navigator.of(context).pop(text); // 입력한 텍스트 반환
                }
              },
              child: const Text('추가'),
            ),
          ],
        );
      },
    );

    if (newName != null && newName.isNotEmpty) {
      setState(() {
        sidebarMenuLists.add(newName);
        applySearchFilter(); // 검색필터 리스트도 새로고침
      });
    }
  }

  void applySearchFilter() {
    final query = searchController.text.toLowerCase();
    setState(() {
      filteredMenuLists =
          sidebarMenuLists.where((item) {
            return item.toLowerCase().contains(query);
          }).toList();
    });
  }

  @override
  void dispose() {
    searchController.dispose();
    super.dispose();
  }

  List<String> openedTabs = []; // 열려 있는 탭 목록
  String activeTab = ''; // 현재 선택된 탭

  void handleItemSelected(String itemName) {
    setState(() {
      if (!openedTabs.contains(itemName)) {
        openedTabs.add(itemName);
      }
      activeTab = itemName;
    });
  }

  void handleSidebarSelection(String selectedItem) {
    // 예시: 콘솔 출력 또는 향후 기능 확장
    print('Selected sidebar item: $selectedItem');
  }

  int objectiveCount = 1;
  int parameterCount = 1;

  Future<void> _runOptimization() async {
    debugPrint('running optimization…');
    setState(() => _loading = true);

    try {
      // 0) panel state may not be built yet!
      final panelState = _panelKey.currentState;
      if (panelState == null) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('설정 패널을 불러올 수 없습니다')));
        return;
      }

      // 1) pull the config
      final config = panelState.gatherConfig();
      setState(() => _lastConfig = config);
      if (_evalCount == 0) {
        _appendLog(
          '--------------------------------------------------------------------------------------------------------------------',
        );
        _appendLog('gathered config #${config}');
        _appendLog(
          '--------------------------------------------------------------------------------------------------------------------',
        );
      }

      // 2) use the exact keys your gatherConfig() provides
      final String acquisitionMethod = config['acquisition'] as String;
      final int initPoints = config['init_points'] as int;
      final int maxIters = config['iterations'] as int;
      final List<dynamic> paramMaps = config['parameters'] as List<dynamic>;

      // 3) stop if we’ve already done maxIters evaluations
      if (_evalCount >= maxIters) {
        _appendLog('최대 iteration($maxIters) 도달했습니다');
        return;
      }

      // 4) build your Parameter list
      final List<Parameter> parameters =
          paramMaps.map((m) {
            return Parameter(
              name: m['name'] as String,
              min: m['min'] as double,
              max: m['max'] as double,
            );
          }).toList();

      // 5) decide random init vs. model-based
      late List<double> nextPoint;
      if (_evalCount < initPoints) {
        final rand = Random();
        nextPoint =
            parameters
                .map((p) => rand.nextDouble() * (p.max - p.min) + p.min)
                .toList();
      } else {
        nextPoint = await BoApi.fetchNextSuggestion(
          acquisitionMethod,
          parameters,
        );
      }

      // 6) update UI + increment eval count
      setState(() {
        _currentBatch = [nextPoint];

        _evalCount += 1;
      });
      _appendLog('batch #${_evalCount}, try: $_currentBatch');
    } catch (e, st) {
      debugPrint('🚨 runOptimization error: $e\n$st');
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Error: $e')));
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _handleSubmitScore() async {
    setState(() => _loading = true);
    try {
      // 1) 현재 스코어를 파싱
      // controller.text 에 사용자 입력이 반영되어 있음
      final scoreText = scoreController.text;
      final score = double.tryParse(scoreText);
      if (score == null) {
        throw '유효한 숫자를 입력하세요';
      }
      //일단은 하나의 score 값만 받는다 생각 - 추후에 multi-objective 하려면 수정 필요
      final List<double> scores = [score];

      // 2) 서버에 제출하고 전체 평가 횟수(total)를 받아옴
      final total = await BoApi.submitScores(_currentBatch, scores);

      // 3) eval count 업데이트
      setState(() {
        _evalCount = total;
      });
      _appendLog('score registered, currently on iter: $total');

      debugPrint('score : $scores');

      // 4) _history에 새 좌표 추가
      //    — JSArray로 받은 _currentBatch를 List<dynamic>으로 처리
      //    — config 내 objectives/parameters도 List<dynamic>에서 Map으로 변환
      final rawParams = _lastConfig!['parameters'] as List<dynamic>;
      final params =
          rawParams.map((e) => Map<String, dynamic>.from(e as Map)).toList();
      final rawObjs = _lastConfig!['objectives'] as List<dynamic>;
      final objs =
          rawObjs.map((e) => Map<String, dynamic>.from(e as Map)).toList();

      final batchAsList = _currentBatch as List<dynamic>;
      debugPrint('_last config : $_lastConfig');

      setState(() {
        for (var suggestionDyn in batchAsList) {
          // suggestionDyn은 List<dynamic> – 각 파라미터 값들
          final values = List<double>.from(suggestionDyn as List<dynamic>);
          final entry = <String, dynamic>{'iteration': _history.length};

          // 파라미터 값 매핑
          for (var i = 0; i < params.length; i++) {
            final name = params[i]['name'] as String;
            entry[name] = values[i];
          }

          // Objective 값 매핑 (scores 리스트와 순서가 동일하다고 가정)
          for (var i = 0; i < objs.length; i++) {
            final name = objs[i]['name'] as String;
            entry[name] = scores[i];
          }

          _history.add(entry);
        }
      });

      // 5) 다음 최적화 배치 요청
      await _runOptimization();
    } catch (e) {
      debugPrint('submitScore error: $e');
      _appendLog('submitScore error: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final history = _history;
    // 1) raw JSArray(dynamic) 꺼내기
    final rawObjs = _lastConfig?['objectives'];
    final rawParams = _lastConfig?['parameters'];

    // 2) List<Map<String,dynamic>>로 변환
    List<Map<String, dynamic>>? objectiveMaps;
    if (rawObjs is List) {
      objectiveMaps =
          rawObjs
              .whereType<Map>()
              .map((e) => Map<String, dynamic>.from(e))
              .toList();
    }

    List<Map<String, dynamic>>? parameterMaps;
    if (rawParams is List) {
      parameterMaps =
          rawParams
              .whereType<Map>()
              .map((e) => Map<String, dynamic>.from(e))
              .toList();
    }

    return Scaffold(
      body: LayoutBuilder(
        builder: (context, constraints) {
          if (constraints.maxWidth > 1300) {
            return Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 🔸 사이드 영역: 버튼 + (사이드바가 보일 때만 내용)
                SidebarWidget(
                  isSidebarVisible: _isSidebarVisible,
                  searchController: searchController,
                  onToggle:
                      () => setState(
                        () => _isSidebarVisible = !_isSidebarVisible,
                      ),
                  onAdd: handleAddNewOptimization,
                  filteredMenuLists: filteredMenuLists,
                  onSelect: handleSidebarSelection,
                ),

                // 🔥 메인 화면
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // 상단 Device Status
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.center,
                          children: [
                            const Text(
                              'Device Status',
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 12),
                            DeviceStatusWidget(statusCodes: deviceStatusCodes),
                          ],
                        ),
                      ),
                      const Divider(),

                      // 하단 3등분 레이아웃
                      Expanded(
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            // 🔹 BO Control Panel
                            Expanded(
                              flex: 2,
                              child: Padding(
                                padding: const EdgeInsets.all(12.0),
                                child: Material(
                                  color: Colors.transparent,
                                  child: SingleChildScrollView(
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.stretch,
                                      children: [
                                        BOControlPanel(
                                          key: _panelKey,
                                          acquisition: acquisition,
                                          initController: initController,
                                          iterController: iterController,
                                          loading: loading,
                                          scoreController: scoreController,
                                          onSuggest: () {
                                            _runOptimization();
                                          },
                                          onSubmitScore:
                                              (double _) =>
                                                  _handleSubmitScore(),
                                          onAcquisitionChanged:
                                              (val) => setState(
                                                () => acquisition = val!,
                                              ),
                                          parameterOptions: parameterOptions,
                                          objectiveCount: objectiveCount,
                                          parameterCount: parameterCount,
                                          onObjectiveCountChanged:
                                              (val) => setState(
                                                () => objectiveCount = val!,
                                              ),
                                          onParameterCountChanged:
                                              (val) => setState(
                                                () => parameterCount = val!,
                                              ),
                                        ),

                                        SizedBox(height: 16),

                                        // Debug 용 터미널 느낌
                                        SizedBox(
                                          height: 240,
                                          child: Container(
                                            color: Colors.black,
                                            padding: EdgeInsets.all(8),
                                            child: Scrollbar(
                                              thumbVisibility: true,
                                              controller: _logScrollController,
                                              child: ListView.builder(
                                                controller:
                                                    _logScrollController,
                                                itemCount: _debugLog.length,
                                                shrinkWrap:
                                                    true, // 내부에서 자기 크기만큼만 그리도록
                                                physics:
                                                    ClampingScrollPhysics(), // 부모 스크롤뷰와 충돌 안 나게
                                                itemBuilder:
                                                    (context, i) => Text(
                                                      _debugLog[i],
                                                      style: TextStyle(
                                                        fontFamily: 'monospace',
                                                        fontSize: 12,
                                                        color: Colors.white,
                                                      ),
                                                    ),
                                              ),
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              ),
                            ),

                            // 🔹 Score History Chart + 영상
                            Expanded(
                              flex: 3,
                              child: Padding(
                                padding: const EdgeInsets.all(12.0),
                                child: MultiResultChart(
                                  history: history,
                                  objectives: objectiveMaps,
                                  parameters: parameterMaps,
                                  maxIterations:
                                      (_lastConfig?['iterations'] as int?) ?? 0,
                                ),
                              ),
                            ),

                            // 🔹 Acquisition Function Heatmap
                            Expanded(
                              flex: 3,
                              child: Padding(
                                padding: const EdgeInsets.all(12.0),
                                child: EquipmentStatus(),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            );
          } else {
            // 모바일 레이아웃
            return SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  DeviceStatusWidget(statusCodes: deviceStatusCodes),
                  const Divider(height: 32, color: Colors.white54),
                  Material(
                    color: Colors.transparent,
                    child: Divider(height: 32), //임시로 둠
                  ),

                  const Divider(height: 32),
                ],
              ),
            );
          }
        },
      ),
    );
  }
}
