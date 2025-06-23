from services.plc_service import run_path
from typing import Iterable, Sequence, List, Tuple


class PathOutOfRangeError(ValueError):
    """x·y 좌표가 허용 범위를 벗어나면 던지는 예외."""


def _assert_in_range(x: float, y: float, *, tag: str = "") -> None:
    """
    (x, y) 가 0 ≤ x ≤ 200, 0 ≤ y ≤ 520 안에 있는지 확인.
    벗어나면 PathOutOfRangeError 를 raise.
    """
    if not (0.0 <= x <= 200.0) or not (0.0 <= y <= 520.0):
        raise PathOutOfRangeError(
            f"{tag} 좌표가 범위를 벗어났습니다: x={x}, y={y} "
            "(허용: x 0-200, y 0-520)"
        )


def shift_path(
    path_points: Iterable[Sequence],
    move_x: float,
    move_y: float,
) -> List[Tuple[float, float, float, float, float, float, int, int]]:
    """
    x·y 좌표를 각각 move_x, move_y 만큼 평행이동한 새 path 리스트를 반환한다.
    - 이동 전·후 어느 지점이라도 허용 범위( x 0-200, y 0-520 )를 벗어나면
      PathOutOfRangeError 예외를 발생시킨다.
    """
    shifted: List[Tuple[float, float, float, float, float, float, int, int]] = []

    for idx, p in enumerate(path_points):
        x, y, z, vx, vy, vz, ext, key = p
        _assert_in_range(x, y, tag=f"[원본 #{idx}]")

        nx, ny = x + move_x, y + move_y
        _assert_in_range(nx, ny, tag=f"[이동 후 #{idx}]")

        shifted.append((nx, ny, z, vx, vy, vz, ext, key))

    return shifted



def set_line_path_points(origin_z, standoff_distance, line_velocity):
    #고정값들
    line_starting_point_x = 20
    line_starting_point_y = 318
    line_length = 20
    profiler_point_x = line_starting_point_x - 8.2
    profiler_point_y = line_starting_point_y - 298
    line_ending_point = line_starting_point_y + line_length
    height_z = origin_z + standoff_distance
    z_clearence = origin_z + 5

    line_path_points = [
            ( line_starting_point_x,   line_starting_point_y,  80,   60.0, 80.0, 40.0,  0, 0),
            ( line_starting_point_x,   line_starting_point_y,  height_z, 30.0, 10.0, 40.0,  2, 0),
            ( line_starting_point_x,   line_ending_point ,  height_z, 30.0, line_velocity, 40.0,  1, 0),
            ( line_starting_point_x,   line_ending_point ,  z_clearence, 30.0, 120, 40.0,  0, 0),
            ( profiler_point_x,        profiler_point_y,  80,   60.0, 150.0, 40.0,  0, 2),
            ( line_starting_point_x,   line_starting_point_y,  80,   60.0, 150.0, 40.0,  0, 0),
        ]
    return line_path_points




def print_line_by_iter(iter_num: int, origin_z, standoff_distance, line_velocity) -> None:
    
    if not 1 <= iter_num <= 102:
        raise ValueError("iter_num must be between 1 and 102 (inclusive).")

    # 행(row)·열(col) 인덱스 계산
    col = (iter_num - 1) % 17         # 0‒16  →  x 0‒160
    row = (iter_num - 1) // 17        # 0‒4   →  y 0‒120

    dx = col * 10                     # 10 mm 간격
    dy = row * 30                     # 30 mm 간격

    # 경로 이동 후 실행
    line_path_points = set_line_path_points(origin_z, standoff_distance, line_velocity)
    shifted_path = shift_path(line_path_points, dx, dy)
    run_path(shifted_path)