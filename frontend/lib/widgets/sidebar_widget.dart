import 'package:flutter/material.dart';

class SidebarWidget extends StatelessWidget {
  final bool isSidebarVisible;
  final TextEditingController searchController;
  final VoidCallback onToggle;
  final VoidCallback onAdd;
  final List<String> filteredMenuLists;
  final void Function(String) onSelect;

  const SidebarWidget({
    Key? key,
    required this.isSidebarVisible,
    required this.searchController,
    required this.onToggle,
    required this.onAdd,
    required this.filteredMenuLists,
    required this.onSelect,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      width: isSidebarVisible ? 200 : 60,
      color: Theme.of(context).colorScheme.background,
      child: Column(
        children: [
          // Toggle button
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: IconButton(
              icon: Icon(isSidebarVisible ? Icons.chevron_left : Icons.menu),
              onPressed: onToggle,
            ),
          ),

          // Search bar + add button
          if (isSidebarVisible)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8.0),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: searchController,
                      decoration: InputDecoration(
                        hintText: 'Search...',
                        isDense: true,
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 6,
                        ),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(icon: const Icon(Icons.add), onPressed: onAdd),
                ],
              ),
            ),

          const Divider(),

          // Menu list
          Expanded(
            child: ListView.builder(
              itemCount: filteredMenuLists.length,
              itemBuilder: (context, index) {
                final item = filteredMenuLists[index];
                return ListTile(
                  dense: true,
                  title: Text(
                    item,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 14),
                  ),
                  onTap: () => onSelect(item),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
