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
            "(허용: x 0–200, y 0–520)"
        )


def shift_path(
    path_points: Iterable[Sequence],
    move_x: float,
    move_y: float,
) -> List[Tuple[float, float, float, float, float, float, int, int]]:
    """
    x·y 좌표를 각각 move_x, move_y 만큼 평행이동한 새 path 리스트를 반환한다.
    - 이동 전·후 어느 지점이라도 허용 범위( x 0–200, y 0–520 )를 벗어나면
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






