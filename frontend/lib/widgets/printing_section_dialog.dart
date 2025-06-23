import 'dart:math' as math;
import 'package:flutter/material.dart';

/// Dialog showing a 200×200 mm board with 20 mm safe-area
/// and a 160×160 mm printable zone. Colours adapt to the
/// dark Material theme supplied in the host app.
class PrintingSectionDialog extends StatefulWidget {
  const PrintingSectionDialog({super.key});

  @override
  State<PrintingSectionDialog> createState() => _PrintingSectionDialogState();
}

class _PrintingSectionDialogState extends State<PrintingSectionDialog> {
  final _dxCtrl = TextEditingController(text: '30');
  final _dyCtrl = TextEditingController(text: '30');

  double get dx => double.tryParse(_dxCtrl.text) ?? 30;
  double get dy => double.tryParse(_dyCtrl.text) ?? 30;

  static const double printable = 160; // mm

  int get cols => (printable / dx).floor();
  int get rows => (printable / dy).floor();
  int get maxIter => cols * rows;

  @override
  void dispose() {
    _dxCtrl.dispose();
    _dyCtrl.dispose();
    super.dispose();
  }

  void _apply() => setState(() {});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;

    return Dialog(
      backgroundColor: cs.background,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      child: SizedBox(
        width: 720,
        height: 840,
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Printing Section Configuration',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  color: cs.onBackground,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 26),

              // ── controls row ──
              Row(
                children: [
                  _numberField(context, 'dx (mm)', _dxCtrl),
                  const SizedBox(width: 16),
                  _numberField(context, 'dy (mm)', _dyCtrl),
                  const SizedBox(width: 32),
                  Text(
                    'Cols: $cols   Rows: $rows   MaxIter: $maxIter',
                    style: TextStyle(color: cs.onBackground.withOpacity(.8)),
                  ),
                  const Spacer(),
                  ElevatedButton(
                    onPressed: _apply,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: cs.primary,
                      foregroundColor: cs.onPrimary,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 36,
                        vertical: 14,
                      ),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: const Text('Set'),
                  ),
                ],
              ),
              const SizedBox(height: 32),

              // ── board preview ──
              Expanded(
                child: LayoutBuilder(
                  builder: (context, constraints) {
                    final size = math.min(
                      constraints.maxWidth,
                      constraints.maxHeight,
                    );
                    return Center(
                      child: SizedBox(
                        width: size,
                        height: size,
                        child: CustomPaint(
                          painter: _BoardPainter(
                            dx: dx,
                            dy: dy,
                            colorScheme: cs,
                          ),
                        ),
                      ),
                    );
                  },
                ),
              ),
              Align(
                alignment: Alignment.bottomRight,
                child: TextButton(
                  onPressed: () => Navigator.pop(context),
                  style: TextButton.styleFrom(foregroundColor: cs.primary),
                  child: const Text('Close'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _numberField(
    BuildContext context,
    String label,
    TextEditingController ctrl,
  ) {
    final cs = Theme.of(context).colorScheme;
    return SizedBox(
      width: 120,
      child: TextField(
        controller: ctrl,
        keyboardType: const TextInputType.numberWithOptions(
          decimal: true,
          signed: false,
        ),
        decoration: InputDecoration(
          labelText: label,
          labelStyle: TextStyle(color: cs.onSurface.withOpacity(.8)),
          enabledBorder: UnderlineInputBorder(
            borderSide: BorderSide(color: cs.onSurface.withOpacity(.3)),
          ),
          focusedBorder: UnderlineInputBorder(
            borderSide: BorderSide(color: cs.primary, width: 2),
          ),
          isDense: true,
        ),
        style: TextStyle(color: cs.onSurface),
      ),
    );
  }
}

// ──────────────────────────────────────────────────────────────
// Painter – colours pulled from current dark theme
// ──────────────────────────────────────────────────────────────
class _BoardPainter extends CustomPainter {
  _BoardPainter({
    required this.dx,
    required this.dy,
    required this.colorScheme,
  });
  final double dx;
  final double dy;
  final ColorScheme colorScheme;

  static const double boardMm = 200;
  static const double safeMm = 20;
  static const double printableMm = boardMm - safeMm * 2; // 160
  static const double siteMm = 15; // red box size (mm)

  @override
  void paint(Canvas canvas, Size size) {
    final scale = size.width / boardMm;

    // Rectangles in pixel space
    final boardRect = Rect.fromLTWH(0, 0, boardMm * scale, boardMm * scale);
    final printableRect = Rect.fromLTWH(
      safeMm * scale,
      safeMm * scale,
      printableMm * scale,
      printableMm * scale,
    );

    // 1) safe-area fill
    canvas.drawRect(
      boardRect,
      Paint()..color = colorScheme.secondary.withOpacity(0.25),
    ); // subtle yellow-grey

    // 2) printable background
    canvas.drawRect(printableRect, Paint()..color = colorScheme.surface);

    // 3) printable border
    canvas.drawRect(
      printableRect,
      Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 2
        ..color = colorScheme.primary,
    );

    // 4) SAFE AREA label
    final labelPainter = TextPainter(
      text: TextSpan(
        text: 'SAFE AREA',
        style: TextStyle(
          color: colorScheme.onSurface.withOpacity(.6),
          fontSize: 12,
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    labelPainter.paint(
      canvas,
      Offset(
        boardRect.right - labelPainter.width - 4,
        boardRect.bottom - labelPainter.height - 4,
      ),
    );

    // 5) red boxes – fully cover edges after spacing correction
    final cols = (printableMm / dx).floor();
    final rows = (printableMm / dy).floor();

    final usableW = printableMm - siteMm; // leave half-site margin each side
    final usableH = printableMm - siteMm;
    final realDx = cols > 1 ? usableW / (cols - 1) : 0;
    final realDy = rows > 1 ? usableH / (rows - 1) : 0;

    final siteFill = Paint()..color = Colors.red.shade400;
    final siteStroke =
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.2
          ..color = Colors.red.shade900;

    for (int c = 0; c < cols; c++) {
      for (int r = 0; r < rows; r++) {
        final xMm = safeMm + c * realDx;
        final yMm = safeMm + r * realDy;
        final rect = Rect.fromLTWH(
          xMm * scale,
          yMm * scale,
          siteMm * scale,
          siteMm * scale,
        );
        canvas.drawRect(rect, siteFill);
        canvas.drawRect(rect, siteStroke);
      }
    }
  }

  @override
  bool shouldRepaint(covariant _BoardPainter oldDelegate) =>
      oldDelegate.dx != dx || oldDelegate.dy != dy;
}
