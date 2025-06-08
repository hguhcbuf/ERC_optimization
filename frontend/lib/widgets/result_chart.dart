import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';

/// MultiResultChart displays objective and parameter trends over iterations.
class MultiResultChart extends StatelessWidget {
  final List<Map<String, dynamic>>? history;
  final List<Map<String, dynamic>>? objectives;
  final List<Map<String, dynamic>>? parameters;
  final int? maxIterations;

  const MultiResultChart({
    Key? key,
    required this.history,
    required this.objectives,
    required this.parameters,
    required this.maxIterations,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    // If config missing, show placeholder
    if (objectives == null || parameters == null || maxIterations == null) {
      return const Center(
        child: Text(
          'No result',
          style: TextStyle(fontSize: 16, fontStyle: FontStyle.italic),
        ),
      );
    } else {
      debugPrint(
        'objectives : $objectives, parameters : $parameters, maxiter : $maxIterations, history : $history',
      );
    }

    final hist = history ?? [];
    final rows = <Widget>[];

    // Objective charts
    for (var obj in objectives!) {
      final name = obj['name'] as String;
      final spots =
          hist.map((e) {
            final iter = (e['iteration'] as num).toInt() + 1;
            return FlSpot(iter.toDouble(), (e[name] as num).toDouble());
          }).toList();
      final bounds = _computeBounds(spots, defaultMin: 0.0, defaultMax: 5.0);
      rows.add(_buildChartRow(name, spots, bounds.min, bounds.max));
    }

    // Parameter charts
    for (var p in parameters!) {
      final name = p['name'] as String;
      final minVal = (p['min'] as num).toDouble();
      final maxVal = (p['max'] as num).toDouble();
      final spots =
          hist.map((e) {
            final iter = (e['iteration'] as num).toInt() + 1;
            return FlSpot(iter.toDouble(), (e[name] as num).toDouble());
          }).toList();
      rows.add(_buildChartRow(name, spots, minVal, maxVal));
    }

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children:
            rows
                .map(
                  (w) => Padding(
                    padding: const EdgeInsets.symmetric(vertical: 12.0),
                    child: SizedBox(height: 240, child: w),
                  ),
                )
                .toList(),
      ),
    );
  }

  Widget _buildChartRow(
    String label,
    List<FlSpot> spots,
    double minY,
    double maxY,
  ) {
    final double yInterval = spots.length > 1 ? (maxY - minY) / 5.0 : 1.0;

    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        // Y-axis label
        Container(
          width: 40,

          alignment: Alignment.center,
          child: Transform.rotate(
            angle: -3.1416 / 2,
            child: Text(
              label,
              style: const TextStyle(fontWeight: FontWeight.bold),
              maxLines: 1, // ← 한 줄만 허용
              softWrap: false, // ← 줄 바꿈 금지
              overflow: TextOverflow.visible, // ← 넘치는 텍스트는 잘리지 않고 보이도록
            ),
          ),
        ),
        const SizedBox(width: 8),
        // Line chart
        Expanded(
          child: LineChart(
            LineChartData(
              minX: 1,
              maxX: maxIterations!.toDouble(),
              minY: minY,
              maxY: maxY,
              gridData: const FlGridData(show: true),
              titlesData: FlTitlesData(
                bottomTitles: AxisTitles(
                  axisNameWidget: const Padding(
                    padding: EdgeInsets.only(top: 8.0),
                    child: Text('Iteration'),
                  ),
                  axisNameSize: 24,
                  sideTitles: SideTitles(
                    showTitles: true,
                    interval: 1.0,
                    getTitlesWidget:
                        (v, _) =>
                            (v >= 1 && v % 1 == 0)
                                ? Text(v.toInt().toString())
                                : const SizedBox.shrink(),
                  ),
                ),
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    interval: yInterval,
                    reservedSize: 40,
                    getTitlesWidget: (v, _) => Text(v.toStringAsFixed(1)),
                  ),
                ),
                topTitles: AxisTitles(
                  sideTitles: SideTitles(showTitles: false),
                ),
                rightTitles: AxisTitles(
                  sideTitles: SideTitles(showTitles: false),
                ),
              ),
              lineBarsData: [
                LineChartBarData(
                  spots: spots,
                  isCurved: false,
                  dotData: const FlDotData(show: true),
                  barWidth: 2,
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  _Bounds _computeBounds(
    List<FlSpot> spots, {
    required double defaultMin,
    required double defaultMax,
  }) {
    if (spots.length > 1) {
      final ys = spots.map((s) => s.y);
      final min = ys.reduce((a, b) => a < b ? a : b);
      final max = ys.reduce((a, b) => a > b ? a : b);
      return _Bounds(min, max);
    }
    return _Bounds(defaultMin, defaultMax);
  }
}

class _Bounds {
  final double min;
  final double max;
  const _Bounds(this.min, this.max);
}
