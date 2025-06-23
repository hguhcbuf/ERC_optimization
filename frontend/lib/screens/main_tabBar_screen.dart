import 'package:flutter/material.dart';
import '../widgets/sidebar_widget.dart';
import '../screens/bo_screen.dart';
import '../screens/joggerMode_screen.dart';
import '../services/bo_api.dart';

class MainTabBarScreen extends StatefulWidget {
  const MainTabBarScreen({super.key});

  @override
  State<MainTabBarScreen> createState() => MainTabBarScreenState();
}

class MainTabBarScreenState extends State<MainTabBarScreen> {
  // Sidebar 부분

  bool _isSidebarVisible = true;

  final TextEditingController searchController = TextEditingController();
  List<String> filteredMenuLists = [];
  List<String> sidebarMenuLists = [
    'line ucb log 1',
    'line ucb log 2',
    'lattice mobo log',
  ];

  // bo 설정 부분
  final List<String> parameterOptions = [
    'Line Speed',
    'Standoff Distance',
    'Extrusion Pressure',
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

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2, // 탭 수
      child: Scaffold(
        backgroundColor: Theme.of(context).colorScheme.surface,
        body: Row(
          children: [
            /// ✅ 왼쪽 사이드바
            SizedBox(
              width: 200,
              child: SidebarWidget(
                isSidebarVisible: _isSidebarVisible,
                searchController: searchController,
                onToggle:
                    () =>
                        setState(() => _isSidebarVisible = !_isSidebarVisible),
                onAdd: handleAddNewOptimization,
                filteredMenuLists: filteredMenuLists,
                onSelect: handleSidebarSelection,
              ), // 구현된 Sidebar 위젯
            ),

            /// ✅ 오른쪽 메인 영역: TabBar + TabBarView
            Expanded(
              child: Column(
                children: [
                  Container(
                    // color: Colors.grey[900],
                    child: const TabBar(
                      indicatorColor: Colors.blue,
                      labelColor: Colors.white,
                      unselectedLabelColor: Colors.grey,
                      tabs: [
                        Tab(text: 'Optimizer'),
                        Tab(text: 'Device Controller'),
                      ],
                    ),
                  ),

                  Expanded(
                    child: TabBarView(
                      children: [
                        BOScreen(), // 탭 1 내용
                        JoggerModeScreen(), // 탭 2 내용
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
