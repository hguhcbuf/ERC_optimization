from typing import Iterable, List, Sequence, Tuple
from PLC_motion_controller import run_path
from Shift_path import shift_path
from NordsonEFD import NordsonEFD

# inst = NordsonEFD(port='COM4', baudrate=115200, timeout=1)
# inst.SetPressure(50)




def set_lattice_path_points(
    *,
    origin_z: float,
    first_layer_standoff: float,
    inter_layer_standoff: float,
    n_ligaments: int,
    line_velocity: float,
    num_layers: int,
    # ─────── 공정 파라미터 ───────
    size_xy: float = 10.0,            # 라티스 한 변 길이
    safe_margin: float = 1.0,
    line_start_xy: Tuple[float, float] = (20.0, 318.0),
    travel_v_xy: Tuple[float, float] = (60.0, 120.0),
    z_travel_v: float = 40.0,
    keyence_mode_default: int = 0,
    extra_nozzle_travel: float = 3.0,  # 압출 OFF 후 추가 이동(mm)
    # ─────── 프로파일러 ───────
    profiler_xy: Tuple[float, float] = (17.3, 14.8),
    profiler_z: float = 80.0,
) -> List[Tuple[float, float, float, float, float, float, int, int]]:
    """
    • 각 ligament 길이 = size_xy – 1 mm (기본 9 mm).
    • 인필 끝점에서 압출 OFF 후 same-dir 으로 extra_nozzle_travel(mm) 이동
      → 그 지점에서 Z-clearance 상승.
    • 반환: [(x, y, z, vx, vy, vz, ExtMode, KeyenceMode), …]
    """

    # ── 기본 체크 ───────────────────────────────
    if n_ligaments < 1 or num_layers < 1:
        raise ValueError("n_ligaments 와 num_layers 는 1 이상이어야 합니다.")
    if safe_margin * 2 >= size_xy:
        raise ValueError("safe_margin 이 size_xy 보다 크거나 같습니다.")

    clearance_z = origin_z + 5.0
    start_x, start_y = line_start_xy
    pvx, pvy = travel_v_xy

    inner_span   = size_xy - 2 * safe_margin          # == 8 mm
    ligament_len = size_xy - 1.0                      # 10 → 9 mm

    if n_ligaments == 1:
        offsets = [safe_margin + inner_span / 2.0]
    else:
        pitch = inner_span / (n_ligaments - 1)
        offsets = [safe_margin + i * pitch for i in range(n_ligaments)]

    path: List[Tuple[float, float, float, float, float, float, int, int]] = []

    for layer in range(num_layers):
        printing_z = origin_z + first_layer_standoff + layer * inter_layer_standoff
        even_layer = (layer % 2 == 0)

        if even_layer:  # Y(+) 방향 인필
            for x_off in offsets:
                x0 = start_x + x_off
                y0 = start_y
                y_end   = start_y + ligament_len         # ← 9 mm
                y_extra = y_end   + extra_nozzle_travel

                path.append((x0, y0, clearance_z, pvx, pvy, z_travel_v, 0, keyence_mode_default))
                path.append((x0, y0, printing_z, 30.0, 10.0, z_travel_v, 2, keyence_mode_default))
                path.append((x0, y_end, printing_z, 0.0, line_velocity, 0.0, 1, keyence_mode_default))
                path.append((x0, y_extra, printing_z, 0.0, pvy, 0.0, 0, keyence_mode_default))
                path.append((x0, y_extra, clearance_z, 30.0, pvy, z_travel_v, 0, keyence_mode_default))

        else:          # X(+) 방향 인필
            for y_off in offsets:
                y0 = start_y + y_off
                x0 = start_x
                x_end   = start_x + ligament_len
                x_extra = x_end   + extra_nozzle_travel

                path.append((x0, y0, clearance_z, pvx, pvy, z_travel_v, 0, keyence_mode_default))
                path.append((x0, y0, printing_z, 10.0, 30.0, z_travel_v, 2, keyence_mode_default))
                path.append((x_end, y0, printing_z, line_velocity, 0.0, 0.0, 1, keyence_mode_default))
                path.append((x_extra, y0, printing_z, pvx, 0.0, 0.0, 0, keyence_mode_default))
                path.append((x_extra, y0, clearance_z, pvx, 30.0, z_travel_v, 0, keyence_mode_default))

    # ── 프로파일러 & 복귀 ─────────────────────────
    prof_x, prof_y = profiler_xy
    path.append((prof_x, prof_y, profiler_z, pvx, pvy, z_travel_v, 0, 2))
    path.append((start_x, start_y, profiler_z, pvx, pvy, z_travel_v, 0, 0))

    return path






# 라티스 경로 생성
# lattice_path = set_lattice_path_points(
#     origin_z               = 15.0,
#     first_layer_standoff   = 0.25,
#     inter_layer_standoff   = 0.20,
#     n_ligaments            = 3,
#     line_velocity          = 12.0,
#     num_layers             = 2,
# )

# 프린팅 실행
# ok = run_path(lattice_path)
# print("Run-path success:", ok)

def print_lattice_by_iter(iter_num: int, origin_z, first_layer_standoff, inter_layer_standoff, n_ligaments, line_velocity, num_layers) -> None:
    
    if not 1 <= iter_num <= 81:
        raise ValueError("iter_num must be between 1 and 102 (inclusive).")

    # 행(row)·열(col) 인덱스 계산
    col = (iter_num - 1) % 9         # 0‒16  →  x 0‒160
    row = (iter_num - 1) // 9        # 0‒4   →  y 0‒120

    dx = col * 20                     # 10 mm 간격
    dy = row * 20                     # 30 mm 간격

    # 경로 이동 후 실행
    line_path_points = set_lattice_path_points(origin_z = origin_z, 
                                               first_layer_standoff =first_layer_standoff, 
                                               inter_layer_standoff=inter_layer_standoff, 
                                               n_ligaments=n_ligaments, 
                                               line_velocity=line_velocity, 
                                               num_layers=num_layers)
    shifted_path = shift_path(line_path_points, dx, dy)
    run_path(shifted_path)


# path_points_1 = [
#         ( 100,  390,  15, 30.0, 30.0, 20.0,  0, 0),
# ]
# run_path(path_points_1)


# origin_z               = 15.0
# first_layer_standoff   = 0.2
# inter_layer_standoff   = 0.2
# n_ligaments            = 4
# line_velocity          = 12.0
# num_layers             = 4

# print_lattice_by_iter(2, origin_z, first_layer_standoff, inter_layer_standoff, n_ligaments, line_velocity, num_layers)