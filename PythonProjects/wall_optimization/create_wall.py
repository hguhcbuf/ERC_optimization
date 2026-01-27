from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass
class WallSpec:
    # window origin (lower-left)
    x0: float = 130.000
    y0: float = 350.000

    # default window size (mm)  -> can override via function arg
    size: float = 9.0  # default: 9 mm (9x9)

    # fixed Z
    z_first: float = 15.1

    # machine style
    z_safe: float = 20.0
    y_approach: float = 340.0     # like your file
    y_start: float = 370.0        # like your file
    smoothing: str = "!smoothingSet(mainType:=smoothingParabola, subType:=smoothingRadius, value:=0.1);"

    # commands
    extrude_on: str = "M10"
    extrude_off: str = "M11"
    park_z: float = 80.0
    park_y: float = 200.0

    # feed
    travel_feed: float = 600.0    # F600 for approach (matches your file)


def _mm_s_to_mm_min(v_mm_s: float) -> float:
    return v_mm_s * 60.0


def generate_wall_like_uploaded(
    speed_mm_s: float,
    line_spacing: float,
    layer_height: float,
    num_layers: int,
    *,
    window_size: float | None = None,   # <-- override here (e.g., 8.0, 9.0, 10.0)
    spec: WallSpec = WallSpec(),
    dwell_start_s: float = 1.0,
    dwell_after_on_s: float = 0.1,
) -> str:
    """
    Style:
      - M10 once at the beginning, M11 once at the end
      - No extrusion toggling between layers
      - Layer change: only Z increases
      - Continuous printing: next layer continues from current XY
      - X direction alternates per layer: layer0 x0->x1, layer1 x1->x0, ...

    Window:
      X: [x0, x0+window_size]
      Y: [y0, y0+window_size]
    """
    if num_layers < 1:
        raise ValueError("num_layers must be >= 1")
    if line_spacing <= 0:
        raise ValueError("line_spacing must be > 0")
    if layer_height <= 0:
        raise ValueError("layer_height must be > 0")

    size = spec.size if window_size is None else float(window_size)
    if size <= 0:
        raise ValueError("window_size must be > 0")

    x0 = spec.x0
    x1 = spec.x0 + size
    yL = spec.y0
    yH = spec.y0 + size

    print_feed = _mm_s_to_mm_min(speed_mm_s)

    lines: List[str] = []
    n = 10

    def add(cmd: str) -> None:
        nonlocal n
        if cmd == "":
            lines.append("")
        else:
            lines.append(f"N{n} {cmd}")
            n += 10

    # --- Header ---
    lines.append(spec.smoothing)
    add(f"G00 X{x0:.3f} Y{spec.y_approach:.3f} Z{spec.z_safe:.3f}")
    add(f"G04 F{dwell_start_s:g}")
    add(f"G01 X{x0:.3f} Y{spec.y_start:.3f} Z{spec.z_first:.3f} F{spec.travel_feed:.0f}")
    add(spec.extrude_on)
    add(f"G04 F{dwell_after_on_s:g}")
    add(f"G01 F{print_feed:.0f}")
    add("")

    # Move into the window top edge (start at yH like your file vibe)
    add(f"Y{yH:.3f}")

    def emit_one_layer_snake(
        *,
        direction: int,
        x_target: float,
    ) -> float:
        """
        Assumes we are currently at (current_x, yH) when called.
        Zig-zag in Y while stepping in X by +/- line_spacing.
        Stops exactly at x_target (clamped, no overshoot).
        Ends at Y=yH.
        Returns final X (== x_target).
        """
        nonlocal cur_x
        at_top = True  # we start at yH

        while True:
            # vertical stroke to the other side
            add(f"Y{(yL if at_top else yH):.3f}")

            # attempt next X step
            x_next = cur_x + direction * line_spacing

            # clamp to boundary (NO overshoot)
            if (direction > 0 and x_next >= x_target) or (direction < 0 and x_next <= x_target):
                cur_x = x_target
                add(f"X{cur_x:.3f}")
                add(f"Y{yH:.3f}")  # finish at top
                break

            # normal step
            cur_x = x_next
            add(f"X{cur_x:.3f}")
            add(f"Y{(yH if at_top else yL):.3f}")

            # toggle vertical direction next time
            at_top = not at_top

        # optional duplicate Y high like your file sometimes
        add(f"Y{yH:.3f}")
        return cur_x

    # --- Print layers (continuous, alternating X direction) ---
    cur_x = x0  # after header + Y move, we're effectively at X=x0, Y=yH (since header ended at X=x0)
    # (If your controller requires explicit X here, uncomment next line)
    # add(f"X{cur_x:.3f}")

    for layer_idx in range(num_layers):
        if layer_idx > 0:
            z = spec.z_first + layer_idx * layer_height
            add(f"Z{z:.3f}")

        # Alternate X direction per layer:
        # even layer: x0 -> x1
        # odd layer : x1 -> x0
        if layer_idx % 2 == 0:
            direction = +1
            x_target = x1
        else:
            direction = -1
            x_target = x0

        # Ensure we start each layer at Y=yH (we always end at yH, so this is usually redundant)
        add(f"Y{yH:.3f}")

        emit_one_layer_snake(direction=direction, x_target=x_target)
        add("")

    # --- Footer ---
    add(spec.extrude_off)
    add(f"G01 Z{spec.park_z:.3f} F{spec.travel_feed:.0f}")
    add(f"Y{spec.park_y:.3f}")
    add("M30")

    return "\n".join(lines) + "\n"


def save_gcode(path: str, gcode: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(gcode)


if __name__ == "__main__":
    gcode = generate_wall_like_uploaded(
        speed_mm_s=30.9,     # -> F2400
        line_spacing=0.389,
        layer_height=0.0857,
        num_layers=7,
        window_size=9.0,     # <-- 여기서 9x9, 8.0 넣으면 8x8
    )
    save_gcode("9x9_sample 2_LTO_pressure 410.nc", gcode)
    print("Saved: sample_wall_9x9.nc")
