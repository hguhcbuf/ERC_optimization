from pathlib import Path
import math


# ============================================================
# Light-harvesting pillar array G-code
# ============================================================

GCODE_DIR = Path(r"C:\Users\Administrator\Desktop\GCodes")
LIGHT_HARVESTING_PATH = GCODE_DIR / "light_harvesting.nc"
NOZZLE_DIAMETER = 0.254  # mm (254 um); shared by BO and geometry estimator
NOZZLE_RADIUS = NOZZLE_DIAMETER / 2
NOZZLE_OUTER_DIAMETER = 0.508  # mm, straight metal tube
DIE_SWELLING_RATIO = 1.113
REFERENCE_DIAMETER_MM = NOZZLE_DIAMETER * DIE_SWELLING_RATIO  # H*, d* basis
COLLISION_MARGIN_MM = 0.020  # radial clearance, including G-code rounding

ARRAY_SIZE = 5.0  # mm; includes first base-grid point beyond this distance


def pillar_radius_mm(V_star):
    """V* = nozzle lift speed / free-extrudate speed.

    Volume conservation: A_pillar = A_extrudate / V*.
    """
    v = np.asarray(V_star, dtype=float)
    if not np.isfinite(v).all() or np.any(v <= 0):
        raise ValueError("V_star must be positive and finite.")
    return REFERENCE_DIAMETER_MM / (2.0 * np.sqrt(v))


def collision_clearance_mm(V_star, d_star):
    """Signed nozzle-to-existing-pillar clearance; pillar overlap is allowed.

    Staggered nearest-neighbor pitch is d/sqrt(2).
    Only the nozzle outer radius plus the existing pillar radius is required.
    """
    radius = pillar_radius_mm(V_star)
    required = radius + NOZZLE_OUTER_DIAMETER / 2
    return (np.asarray(d_star) * REFERENCE_DIAMETER_MM / np.sqrt(2.0)
            - required - COLLISION_MARGIN_MM)


def array_coordinates(d_star, start_x=0.0, start_y=0.0):
    """Staggered-grid centers in mm; d_star = grid pitch / swollen extrusion diameter."""
    if not math.isfinite(d_star) or d_star <= 0:
        raise ValueError("d_star must be finite and > 0.")
    d = d_star * REFERENCE_DIAMETER_MM
    n = math.floor(ARRAY_SIZE / d) + 2
    coordinates = []
    for row in range(2 * n - 1):
        offset = d / 2 if row % 2 else 0.0
        count = n - 1 if row % 2 else n
        y = start_y + (row // 2) * d + offset
        coordinates.extend((start_x + col * d + offset, y) for col in range(count))
    return coordinates


def write_light_harvesting_gcode(
    v_star: float,
    h: float,
    d_star: float,
    start_x: float,
    start_y: float,
    initial_height: float,
    *,
    enforce_nozzle_clearance: bool = True,
):
    """
    Generate staggered pillar-array G-code.

    enforce_nozzle_clearance=False is used explicitly by vanilla BO.
    Numeric input validation remains active in either mode.

    Parameters
    ----------
    v_star : float
        V_star = nozzle lift speed / free-extrudate speed.
        Z printing velocity = v_star * 1300.0 [mm/min]

    h : float
        Same role as h in the previous pillar function.
        Physical pillar height = h * REFERENCE_DIAMETER_MM [mm] (254 um nozzle)

    d_star : float
        Dimensionless grid pitch: d_star = d_mm / REFERENCE_DIAMETER_MM.
        Internal d below is the physical grid pitch in mm.

        Base grid:
            n x n

        Offset grid:
            (n-1) x (n-1)

        Offset:
            x = d/2
            y = d/2

    start_x : float
        X coordinate of first pillar [mm].

    start_y : float
        Y coordinate of first pillar [mm].

    initial_height : float
        Z position where pillar printing starts [mm].
    """

    # ========================================================
    # 1. Validation
    # ========================================================

    if v_star <= 0:
        raise ValueError("v_star must be > 0.")

    if h <= 0:
        raise ValueError("h must be > 0.")

    if not all(math.isfinite(value) for value in
               (v_star, h, d_star, start_x, start_y, initial_height)):
        raise ValueError("All G-code inputs must be finite.")
    if d_star <= 0:
        raise ValueError("d_star must be > 0.")
    d = d_star * REFERENCE_DIAMETER_MM
    if enforce_nozzle_clearance and collision_clearance_mm(v_star, d_star) < 0:
        raise ValueError("Nozzle contact: increase d_star or increase V_star.")


    # ========================================================
    # 2. Basic printing parameters
    # ========================================================

    # Same relation as your previous function
    vel = v_star * 900.0

    # H* is converted using the shared swollen extrusion diameter (0.3048 mm).
    pillar_height_mm = h * REFERENCE_DIAMETER_MM

    final_height = (
        initial_height
        + pillar_height_mm
    )

    # --------------------------------------------------------
    # Z clearance
    #
    # Clearance height from substrate:
    # 3 x pillar height
    # --------------------------------------------------------

    z_clearance = (
        initial_height
        + 2.0 * pillar_height_mm
    )


    # ========================================================
    # 3. Determine n from 5 mm x 5 mm target area
    # ========================================================


    # We intentionally include the FIRST point
    # that exceeds 5 mm.
    #
    # Example:
    # d = 0.9 mm
    #
    # 6th point : 4.5 mm
    # 7th point: 5.4 mm  -> include
    #
    # therefore n = 7

    n = math.floor(
        ARRAY_SIZE / d
    ) + 2


    # ========================================================
    # 4. Generate staggered coordinates
    # ========================================================

    coordinates = array_coordinates(d_star, start_x, start_y)


    # ========================================================
    # 5. Build G-code
    # ========================================================

    lines = []
    lines.append("#set paramVertexSmoothing(2; 1; 0.1)#")
    lines.append("G90")
    lines.append("")

    # --------------------------------------------------------
    # First raise Z to safe height
    # --------------------------------------------------------

    lines.append(
        f"G00 Z{z_clearance:.3f}"
    )

    lines.append("")


    # ========================================================
    # 6. Print each pillar
    # ========================================================

    for pillar_index, (x, y) in enumerate(
        coordinates,
        start=1
    ):

        # lines.append(
        #     f"; Pillar {pillar_index}"
        # )

        # Move to pillar position
        lines.append(
            f"G00 X{x:.3f} Y{y:.3f}"
        )

        # Move down to printing start height
        lines.append(
            f"G00 Z{initial_height:.3f}"
        )

        # Extrusion ON
        lines.append("M10")

        # Same 1 s dwell as old code
        lines.append("G04 F0.8")

        # Print pillar upward
        lines.append(
            f"G01 Z{final_height:.3f} F{vel:.3f}"
        )

        # Extrusion OFF
        lines.append("M11")

        # Raise to clearance
        lines.append(
            f"G00 Z{z_clearance:.3f}"
        )

        lines.append("")


    # ========================================================
    # 7. Move to laser profiler
    #
    # Same relative displacement as previous function
    # ========================================================

    # lines.append("; Move to laser profiler")
    lines.append("G91")
    lines.append(
        "G00 Y-311.900 X-10.700"
    )
    lines.append("G90")

    # Laser profiler scan
    lines.append("M50")
    lines.append("G04 F1")

    # lines.append("G91")
    # lines.append(
    #     "G00 Y311.900 X10.700"
    # )
    # lines.append("G90")

    # End
    lines.append("M30")


    # ========================================================
    # 8. Save file
    # ========================================================

    GCODE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    gcode = "\n".join(lines)

    LIGHT_HARVESTING_PATH.write_text(
        gcode,
        encoding="utf-8"
    )


    # # ========================================================
    # # 9. Print summary
    # # ========================================================

    total_pillars = len(coordinates)

    # print("=" * 60)
    # print("LIGHT HARVESTING G-CODE CREATED")
    # print("=" * 60)

    # print(
    #     f"File             : {LIGHT_HARVESTING_PATH}"
    # )

    # print(
    #     f"V*               : {v_star}"
    # )

    # print(
    #     f"H*               : {h}"
    # )

    # print(
    #     f"Physical height  : {pillar_height_mm:.3f} mm"
    # )

    # print(
    #     f"d                : {d:.3f} mm"
    # )

    # print(
    #     f"n                : {n}"
    # )

    # print(
    #     f"Base grid        : {n} x {n} "
    #     f"= {n**2}"
    # )

    # print(
    #     f"Offset grid      : {n-1} x {n-1} "
    #     f"= {(n-1)**2}"
    # )

    # print(
    #     f"Total pillars    : {total_pillars}"
    # )

    # print(
    #     f"Final Z          : {final_height:.3f} mm"
    # )

    # print(
    #     f"Z clearance      : {z_clearance:.3f} mm"
    # )

    # print(
    #     f"Printing feed    : {vel:.3f}"
    # )

    # print("=" * 60)


    return {
        "path": LIGHT_HARVESTING_PATH,
        "d_star": float(d_star),
        "d_mm": d,
        "nozzle_diameter_mm": NOZZLE_DIAMETER,
        "reference_diameter_mm": REFERENCE_DIAMETER_MM,
        "n": n,
        "total_pillars": total_pillars,
        "coordinates": coordinates,
        "pillar_height_mm": pillar_height_mm,
        "z_clearance": z_clearance,
    }



# #------------------------------------------------------------------------------------------test-----------------------------------------------------------
from shapely.geometry import Point
from shapely.ops import unary_union
import numpy as np




def estimate_array_surface_area(H_star, V_star, coordinates,
                                circle_resolution=64, roi_origin=None,
                                include_substrate=True):
    """Area inside the +X,+Y 5 mm ROI from the first pillar center.

    Union footprints before clipping. Clip the ORIGINAL union boundary for
    sides: rectangle cut edges are not physical sidewalls. Pillar bottoms are
    excluded. Exposed substrate is included by default to match profiler area.
    Circles use a polygon approximation; BO's disjoint fast path uses true arcs.
    """
    from shapely.geometry import box, GeometryCollection
    if H_star <= 0 or V_star <= 0 or not np.isfinite([H_star, V_star]).all():
        raise ValueError("H_star and V_star must be positive and finite.")
    coordinates = list(coordinates)
    if roi_origin is None:
        roi_origin = coordinates[0] if coordinates else (0.0, 0.0)
    x0, y0 = roi_origin
    roi = box(x0, y0, x0 + ARRAY_SIZE, y0 + ARRAY_SIZE)
    h = H_star * REFERENCE_DIAMETER_MM
    r = pillar_radius_mm(V_star)
    circles = [Point(x, y).buffer(r, resolution=circle_resolution) for x, y in coordinates]
    union = unary_union(circles) if circles else GeometryCollection()
    top = union.intersection(roi).area
    perimeter = union.boundary.intersection(roi).length if circles else 0.0
    side = perimeter * h
    substrate = max(0.0, roi.area - top)
    return {"N_pillars": len(coordinates), "pillar_height_mm": h,
            "pillar_radius_mm": r, "top_area_mm2": top,
            "side_area_mm2": side, "exposed_perimeter_mm": perimeter,
            "substrate_area_mm2": substrate, "roi_area_mm2": roi.area,
            "pillar_surface_area_mm2": top + side,
            "surface_area_mm2": top + side + (substrate if include_substrate else 0.0)}


def disjoint_roi_surface_area(X):
    """Vectorized true-circle side arcs clipped to ROI; disjoint arrays only.

    Top + uncovered substrate = ROI area. Integrate only circle boundary arcs
    inside the ROI, so clipping never introduces artificial vertical faces.
    """
    X = np.atleast_2d(np.asarray(X, dtype=float))
    result = np.empty(len(X))
    for start in range(0, len(X), 256):
        rows = X[start:start+256]
        d = rows[:, 2] * REFERENCE_DIAMETER_MM
        r = pillar_radius_mm(rows[:, 1])
        n = np.floor(ARRAY_SIZE / d).astype(int) + 2
        m = int(n.max())
        iy, ix = np.meshgrid(np.arange(2*m-1), np.arange(m), indexing="ij")
        iy, ix = iy.ravel(), ix.ravel()
        odd = iy % 2
        valid = (iy[None, :] < 2*n[:, None]-1) & (ix[None, :] < n[:, None]-odd)
        cx = (ix + odd/2)[None, :] * d[:, None]
        cy = (iy/2)[None, :] * d[:, None]
        rr = r[:, None]
        cuts = [np.zeros_like(cx), np.full_like(cx, 2*np.pi)]
        for edge in (0.0, ARRAY_SIZE):
            a = np.arccos(np.clip((edge-cx)/rr, -1, 1))
            cuts += [a, 2*np.pi-a]
            a = np.arcsin(np.clip((edge-cy)/rr, -1, 1))
            cuts += [np.mod(a, 2*np.pi), np.mod(np.pi-a, 2*np.pi)]
        angles = np.sort(np.stack(cuts, axis=-1), axis=-1)
        mid = (angles[..., 1:] + angles[..., :-1])/2
        px = cx[..., None] + rr[..., None]*np.cos(mid)
        py = cy[..., None] + rr[..., None]*np.sin(mid)
        inside = ((px >= 0) & (px <= ARRAY_SIZE) & (py >= 0) & (py <= ARRAY_SIZE)
                  & valid[..., None])
        perimeter = (np.diff(angles, axis=-1)*inside).sum(axis=(1,2))*r
        result[start:start+len(rows)] = ARRAY_SIZE**2 + perimeter*rows[:, 0]*REFERENCE_DIAMETER_MM
    return result
