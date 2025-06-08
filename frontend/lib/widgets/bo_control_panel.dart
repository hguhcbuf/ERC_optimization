import 'package:flutter/material.dart';

class BOControlPanel extends StatefulWidget {
  final String acquisition;
  final TextEditingController initController;
  final TextEditingController iterController;
  final bool loading;
  final VoidCallback onSuggest;
  final void Function(double score) onSubmitScore;
  final void Function(String?) onAcquisitionChanged;
  final List<String> parameterOptions;
  final int objectiveCount;
  final int parameterCount;
  final void Function(int?) onObjectiveCountChanged;
  final void Function(int?) onParameterCountChanged;
  final TextEditingController scoreController;

  const BOControlPanel({
    Key? key,
    required this.acquisition,
    required this.initController,
    required this.iterController,
    required this.loading,
    required this.onSuggest,
    required this.onSubmitScore,
    required this.onAcquisitionChanged,
    required this.parameterOptions,
    required this.objectiveCount,
    required this.parameterCount,
    required this.onObjectiveCountChanged,
    required this.onParameterCountChanged,
    required this.scoreController,
  }) : super(key: key);

  @override
  BOControlPanelState createState() => BOControlPanelState();
}

class BOControlPanelState extends State<BOControlPanel> {
  // Objective inputs
  late List<TextEditingController> _objectiveNameControllers;
  late List<String> _methods;
  late List<String> _directions;
  // Parameter inputs
  late List<String?> _selectedParameters;
  late List<TextEditingController> _paramMinControllers;
  late List<TextEditingController> _paramMaxControllers;

  // bo_control_panel.dart 안에서
  Map<String, dynamic> gatherConfig() {
    // 1) Gather objectives (name, method, direction)
    final objectives = List.generate(
      widget.objectiveCount,
      (i) => {
        'name': _objectiveNameControllers[i].text,
        'method': _methods[i],
        'direction': _directions[i],
      },
    );

    // 2) Gather parameters (name, min, max)
    final parameters = List.generate(
      widget.parameterCount,
      (i) => {
        'name': _selectedParameters[i],
        'min': double.tryParse(_paramMinControllers[i].text) ?? 0.0,
        'max': double.tryParse(_paramMaxControllers[i].text) ?? 2.0,
      },
    );

    // 3) Return full config map
    return {
      'objectiveCount': widget.objectiveCount,
      'objectives': objectives,
      'parameterCount': widget.parameterCount,
      'parameters': parameters,
      'acquisition': widget.acquisition,
      'init_points': int.tryParse(widget.initController.text) ?? 5,
      'iterations': int.tryParse(widget.iterController.text) ?? 10,
    };
  }

  @override
  void initState() {
    super.initState();
    _objectiveNameControllers = List.generate(
      widget.objectiveCount,
      (_) => TextEditingController(),
      growable: true,
    );
    _methods = List<String>.filled(
      widget.objectiveCount,
      'manual',
      growable: true,
    );
    _directions = List<String>.filled(
      widget.objectiveCount,
      'Minimize',
      growable: true,
    );

    _selectedParameters = List<String?>.filled(
      widget.parameterCount,
      widget.parameterOptions.first,
      growable: true,
    );
    _paramMinControllers = List.generate(
      widget.parameterCount,
      (_) => TextEditingController(),
      growable: true,
    );
    _paramMaxControllers = List.generate(
      widget.parameterCount,
      (_) => TextEditingController(),
      growable: true,
    );
  }

  @override
  void didUpdateWidget(covariant BOControlPanel old) {
    super.didUpdateWidget(old);
    // Sync objectives
    if (old.objectiveCount != widget.objectiveCount) {
      final newLen = widget.objectiveCount;
      while (_objectiveNameControllers.length < newLen)
        _objectiveNameControllers.add(TextEditingController());
      while (_objectiveNameControllers.length > newLen)
        _objectiveNameControllers.removeLast();
      while (_methods.length < newLen) _methods.add('manual');
      while (_methods.length > newLen) _methods.removeLast();
      while (_directions.length < newLen) _directions.add('Minimize');
      while (_directions.length > newLen) _directions.removeLast();
    }
    // Sync parameters
    if (old.parameterCount != widget.parameterCount) {
      final newLen = widget.parameterCount;
      while (_selectedParameters.length < newLen)
        _selectedParameters.add(widget.parameterOptions.first);
      while (_selectedParameters.length > newLen)
        _selectedParameters.removeLast();
      while (_paramMinControllers.length < newLen)
        _paramMinControllers.add(TextEditingController());
      while (_paramMinControllers.length > newLen)
        _paramMinControllers.removeLast();
      while (_paramMaxControllers.length < newLen)
        _paramMaxControllers.add(TextEditingController());
      while (_paramMaxControllers.length > newLen)
        _paramMaxControllers.removeLast();
    }
  }

  @override
  Widget build(BuildContext context) {
    final textStyle = const TextStyle(color: Colors.white);
    final hintStyle = const TextStyle(color: Colors.white70);
    final canRun =
        !widget.loading &&
        int.tryParse(widget.initController.text) != null &&
        int.tryParse(widget.iterController.text) != null;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Objective Count selector
        Row(
          children: [
            Text('Objective Count:', style: textStyle),
            const SizedBox(width: 8),
            SizedBox(
              width: 80,
              child: DropdownButton<int>(
                isExpanded: true,
                value: widget.objectiveCount,
                dropdownColor: Theme.of(context).scaffoldBackgroundColor,
                style: textStyle,
                onChanged: widget.onObjectiveCountChanged,
                items:
                    [1, 2, 3, 4, 5]
                        .map(
                          (count) => DropdownMenuItem(
                            value: count,
                            child: Text(count.toString(), style: textStyle),
                          ),
                        )
                        .toList(),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),

        // Objective Name + Method + Direction rows
        for (int i = 0; i < widget.objectiveCount; i++)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Row(
              children: [
                // Objective name input
                Expanded(
                  flex: 3,
                  child: TextField(
                    controller: _objectiveNameControllers[i],
                    style: textStyle,
                    decoration: InputDecoration(
                      hintText: 'Objective Name',
                      hintStyle: hintStyle,
                      isDense: true,
                      enabledBorder: UnderlineInputBorder(
                        borderSide: BorderSide(color: Colors.white54),
                      ),
                      focusedBorder: UnderlineInputBorder(
                        borderSide: BorderSide(color: Colors.white),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                // Method selector
                SizedBox(
                  width: 100,
                  child: DropdownButton<String>(
                    isExpanded: true,
                    value: _methods[i],
                    dropdownColor: Theme.of(context).scaffoldBackgroundColor,
                    style: textStyle,
                    onChanged: (val) {
                      setState(() {
                        _methods[i] = val!;
                      });
                    },
                    items:
                        ['manual', 'bus 1', 'bus 2']
                            .map(
                              (method) => DropdownMenuItem(
                                value: method,
                                child: Text(method, style: textStyle),
                              ),
                            )
                            .toList(),
                  ),
                ),
                const SizedBox(width: 8),
                // Direction selector
                SizedBox(
                  width: 100,
                  child: DropdownButton<String>(
                    isExpanded: true,
                    value: _directions[i],
                    dropdownColor: Theme.of(context).scaffoldBackgroundColor,
                    style: textStyle,
                    onChanged: (val) {
                      setState(() {
                        _directions[i] = val!;
                      });
                    },
                    items:
                        ['Minimize', 'Maximize']
                            .map(
                              (dir) => DropdownMenuItem(
                                value: dir,
                                child: Text(dir, style: textStyle),
                              ),
                            )
                            .toList(),
                  ),
                ),
              ],
            ),
          ),

        const SizedBox(height: 24),

        // Parameter Count selector
        Row(
          children: [
            Text('Parameter Count:', style: textStyle),
            const SizedBox(width: 8),
            SizedBox(
              width: 80,
              child: DropdownButton<int>(
                isExpanded: true,
                value: widget.parameterCount,
                dropdownColor: Theme.of(context).scaffoldBackgroundColor,
                style: textStyle,
                onChanged: widget.onParameterCountChanged,
                items:
                    [1, 2, 3, 4, 5]
                        .map(
                          (count) => DropdownMenuItem(
                            value: count,
                            child: Text(count.toString(), style: textStyle),
                          ),
                        )
                        .toList(),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),

        // Parameter rows
        for (int i = 0; i < widget.parameterCount; i++)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Row(
              children: [
                // 파라미터 이름 드롭다운
                Expanded(
                  flex: 2,
                  child: DropdownButtonFormField<String>(
                    isExpanded: true,
                    value: _selectedParameters[i],
                    items:
                        widget.parameterOptions
                            .map(
                              (param) => DropdownMenuItem(
                                value: param,
                                child: Text(param, style: textStyle),
                              ),
                            )
                            .toList(),
                    onChanged:
                        (val) => setState(() => _selectedParameters[i] = val!),
                    decoration: InputDecoration(
                      hintText: 'Select parameter',
                      hintStyle: hintStyle,
                      isDense: true,
                      enabledBorder: UnderlineInputBorder(
                        borderSide: BorderSide(color: Colors.white54),
                      ),
                      focusedBorder: UnderlineInputBorder(
                        borderSide: BorderSide(color: Colors.white),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                // Min 입력란
                Expanded(
                  child: TextField(
                    controller: _paramMinControllers[i],
                    style: textStyle,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                      hintText: 'Min',
                      hintStyle: hintStyle,
                      isDense: true,
                      enabledBorder: UnderlineInputBorder(
                        borderSide: BorderSide(color: Colors.white54),
                      ),
                      focusedBorder: UnderlineInputBorder(
                        borderSide: BorderSide(color: Colors.white),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                // Max 입력란 (추가된 부분)
                Expanded(
                  child: TextField(
                    controller: _paramMaxControllers[i],
                    style: textStyle,
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                      hintText: 'Max',
                      hintStyle: hintStyle,
                      isDense: true,
                      enabledBorder: UnderlineInputBorder(
                        borderSide: BorderSide(color: Colors.white54),
                      ),
                      focusedBorder: UnderlineInputBorder(
                        borderSide: BorderSide(color: Colors.white),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),

        const SizedBox(height: 24),

        // Acquisition Function
        Text('Acquisition Function:', style: textStyle),
        DropdownButton<String>(
          value: widget.acquisition,
          dropdownColor: Theme.of(context).scaffoldBackgroundColor,
          style: textStyle,
          onChanged: widget.onAcquisitionChanged,
          items: [
            DropdownMenuItem(
              value: 'ei',
              child: Text('Expected Improvement (EI)', style: textStyle),
            ),
            DropdownMenuItem(
              value: 'ucb',
              child: Text('Upper Confidence Bound (UCB)', style: textStyle),
            ),
            DropdownMenuItem(
              value: 'pi',
              child: Text('Probability of Improvement (PI)', style: textStyle),
            ),
          ],
        ),
        const SizedBox(height: 16),

        // Random Points & Iterations - scrollable on narrow screens
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: [
              SizedBox(
                width: 200,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Initial Random Points:', style: textStyle),
                    TextField(
                      controller: widget.initController,
                      style: textStyle,
                      keyboardType: TextInputType.number,
                      decoration: InputDecoration(
                        isDense: true,
                        enabledBorder: UnderlineInputBorder(
                          borderSide: BorderSide(color: Colors.white54),
                        ),
                        focusedBorder: UnderlineInputBorder(
                          borderSide: BorderSide(color: Colors.white),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              SizedBox(
                width: 200,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Iterations:', style: textStyle),
                    TextField(
                      controller: widget.iterController,
                      style: textStyle,
                      keyboardType: TextInputType.number,
                      decoration: InputDecoration(
                        isDense: true,
                        enabledBorder: UnderlineInputBorder(
                          borderSide: BorderSide(color: Colors.white54),
                        ),
                        focusedBorder: UnderlineInputBorder(
                          borderSide: BorderSide(color: Colors.white),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 24),
        ElevatedButton(
          onPressed: canRun ? () => widget.onSuggest() : null,
          child:
              widget.loading
                  ? const CircularProgressIndicator()
                  : const Text('Run Optimization'),
        ),
        const SizedBox(height: 16),

        // Submit measured score
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: widget.scoreController,
                keyboardType: TextInputType.number,
                style: textStyle,
                decoration: InputDecoration(
                  hintText: 'Enter measured score',
                  hintStyle: hintStyle,
                  isDense: true,
                ),
              ),
            ),
            const SizedBox(width: 8),
            ElevatedButton(
              onPressed: () {
                final score = double.tryParse(widget.scoreController.text);
                if (score != null) widget.onSubmitScore(score);
              },
              child: const Text('Submit Score'),
            ),
          ],
        ),
      ],
    );
  }
}
