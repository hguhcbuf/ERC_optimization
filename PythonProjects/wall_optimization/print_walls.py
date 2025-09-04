from typing import List, Tuple
import matplotlib.pyplot as plt

#  포인트 형식: (x, y, z, vx, vy, vz, ext, key)
PathPoint = Tuple[float, float, float, float, float, float, int, int]

def generate_straight_fill(
    width: float = 30.0,        # 기판 폭 (mm)
    height: float = 30.0,       # 기판 높이 ( mm)
    spacing: float = 1.0,       # 선 간격 (mm)
    z: float = 0.2,             # 적층 높이 (mm)
    speed: float = 20.0,        # 프린트 속도 (mm/s)
    ext_on: int = 1,            # 압력 on 플래그
    ext_off: int = 0,           # 압력 off 플래그
    key_off: int = 0,            # 촬영 off (필요시 1로 변경)
    origin_z: int = 30,
) -> List[PathPoint]:
    """
    각 라인을 왼쪽에서 오른쪽으로만 이동하며,
    일정 간격으로 띄워서 프린팅 경로를 생성.
    """
    paths: List[PathPoint] = []
    num_lines = int(height // spacing) + 1

    for i in range(num_lines):
        y = i * spacing
        x_start, x_end = 0.0, width

        # 이동(압력 OFF)
        paths.append((x_start, y, z+origin_z, speed, speed, speed, ext_off, key_off))
        # 압력 ON (프린팅 시작)
        paths.append((x_start, y, z+origin_z, speed, speed, speed, ext_on,  key_off))
        # 프린팅 직선
        paths.append((x_end,   y, z+origin_z, speed, speed, speed, ext_on,  key_off))
        # 압력 OFF (프린팅 종료)
        paths.append((x_end,   y, z+origin_z, speed, speed, speed, ext_off, key_off))

    return paths

