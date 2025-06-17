from typing import Iterable, List, Sequence, Tuple
from PLC_motion_controller import run_path
from Shift_path import shift_path
from NordsonEFD import NordsonEFD

# inst = NordsonEFD(port='COM4', baudrate=115200, timeout=1)
# inst.SetPressure(50)




def set_lattice_path_points(
    *,
    # ─────── 핵심 디자인 변수 ───────
    origin_z: float,
    first_layer_standoff: float,
    inter_layer_standoff: float,
    n_ligaments: int,
    line_velocity: float,
    num_layers: int,
    # ─────── 공정·기계 파라미터 ───────
    size_xy: float = 10.0,                    # 한 변 길이
    safe_margin: float = 1.0,                 # 가장자리 여유 (mm)
    line_start_xy: Tuple[float, float] = (20.0, 318.0),
    travel_v_xy: Tuple[float, float] = (60.0, 120.0),
    z_travel_v: float = 40.0,
    keyence_mode_default: int = 0,
    # ─────── 프로파일러 설정 ───────
    profiler_xy: Tuple[float, float] = (17.3, 14.8),
    profiler_z: float = 80.0,
) -> List[Tuple[float, float, float, float, float, float, int, int]]:
    """
    8 mm 폭(좌·우 safe_margin 1 mm)을 유지하며 라티스 path_points를 생성.
    반환 = [(x, y, z, vx, vy, vz, ExtMode, KeyenceMode), ...]
    """

    # ── sanity check ──────────────────────────────────
    if n_ligaments < 1:
        raise ValueError("n_ligaments는 1 이상이어야 합니다.")
    if num_layers < 1:
        raise ValueError("num_layers는 1 이상이어야 합니다.")
    if safe_margin * 2 >= size_xy:
        raise ValueError("safe_margin이 너무 큽니다 (size_xy보다 작아야 함).")

    # ── 고정 파라미터 ─────────────────────────────────
    clearance_z = origin_z + 5.0
    start_x, start_y = line_start_xy
    pvx, pvy = travel_v_xy

    # ── 8 mm 폭 안쪽에 선분 배치 ──────────────────────
    inner_span = size_xy - 2 * safe_margin  # == 8 mm
    if n_ligaments == 1:
        offsets = [safe_margin + inner_span / 2.0]          # 중앙
    else:
        pitch = inner_span / (n_ligaments - 1)
        offsets = [safe_margin + i * pitch for i in range(n_ligaments)]

    # ── path 빌드 ─────────────────────────────────────
    path: List[Tuple[float, float, float, float, float, float, int, int]] = []

    for layer in range(num_layers):
        printing_z = origin_z + first_layer_standoff + layer * inter_layer_standoff
        even_layer = (layer % 2 == 0)

        if even_layer:  # ── Y(+) 방향 선분 ──
            for x_off in offsets:
                x0 = start_x + x_off
                y0 = start_y
                y1 = start_y + size_xy

                # ① 시작점 이동 (Z = clearance)
                path.append((x0, y0, clearance_z, pvx, pvy, z_travel_v, 0, keyence_mode_default))
                # ② Z ↓ & 압출 시작
                path.append((x0, y0, printing_z, 30.0, 10.0, z_travel_v, 2, keyence_mode_default))
                # ③ 프린팅(Y+)
                path.append((x0, y1, printing_z, 0.0, line_velocity, 0.0, 1, keyence_mode_default))
                # ④ Z ↑ clearance
                path.append((x0, y1, clearance_z, 30.0, pvy, z_travel_v, 0, keyence_mode_default))

        else:          # ── X(+) 방향 선분 ──
            for y_off in offsets:
                y0 = start_y + y_off
                x0 = start_x
                x1 = start_x + size_xy

                # ① 시작점 이동
                path.append((x0, y0, clearance_z, pvx, pvy, z_travel_v, 0, keyence_mode_default))
                # ② Z ↓ & 압출 시작
                path.append((x0, y0, printing_z, 10.0, 30.0, z_travel_v, 2, keyence_mode_default))
                # ③ 프린팅(X+)
                path.append((x1, y0, printing_z, line_velocity, 0.0, 0.0, 1, keyence_mode_default))
                # ④ Z ↑ clearance
                path.append((x1, y0, clearance_z, pvx, 30.0, z_travel_v, 0, keyence_mode_default))

    # ── 라티스 완료 후 프로파일러 촬영 & 복귀 ───────────
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


# origin_z               = 15.0
# first_layer_standoff   = 0.2
# inter_layer_standoff   = 0.2
# n_ligaments            = 4
# line_velocity          = 12.0
# num_layers             = 4

# print_lattice_by_iter(15, origin_z, first_layer_standoff, inter_layer_standoff, n_ligaments, line_velocity, num_layers)