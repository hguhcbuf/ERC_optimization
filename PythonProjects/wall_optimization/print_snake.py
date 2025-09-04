from typing import List, Tuple
import math

# 포인트 형식: (x, y, z, vx, vy, vz, ext, key)
PathPoint = Tuple[float, float, float, float, float, float, int, int]
# ExtMode: 0=압출안함, 1=압출끝남, 2=압출시작, 3=압출유지 (여기선 3만 사용)

def generate_snake_fill(
    width: float = 30.0,         # 기판 폭 (mm)
    height: float = 30.0,        # 기판 높이 (mm)
    spacing: float = 1.0,        # 선 간격 (mm)
    z: float = 0.16,              # 첫 레이어 오프셋 (origin_z에 더해짐)
    layer_step: float | None = None,  # 레이어 간 상승량 (미지정 시 z 사용)
    speed: float = 20.0,         # 프린트/이동 속도 (mm/s)
    origin_z: float = 13.0,      # 시작 Z 오프셋
    n_layers: int = 4            # 총 레이어 수 (1=첫 레이어만)
) -> List[PathPoint]:
    """
    스네이크 패턴을 레이어마다 Z를 올리며 출력.
    - 1,3,5,... 레이어: 정방향 (첫 레이어 경로와 동일)
    - 2,4,6,... 레이어: 역방향 (두 번째 레이어 경로와 동일)
    """
    if layer_step is None:
        layer_step = z  # 호환성: 기본은 z만큼 상승

    def snake_template() -> List[PathPoint]:
        """Z=0으로 템플릿(정방향) 생성. 이후 레이어에서 Z만 덮어쓴다."""
        pts: List[PathPoint] = []
        num_lines = int(math.floor(height / spacing)) + 1
        y_values = [min(i * spacing, height) for i in range(num_lines)]

        for i, y in enumerate(y_values):
            if i % 2 == 0:
                x_start, x_end = 0.0, width
            else:
                x_start, x_end = width, 0.0

            # 이동/시작/프린트/끝 (여기선 ext=3으로 단순화)
            pts.append((x_start, y, 0.0, speed, speed, 20.0, 3, 0))
            pts.append((x_start, y, 0.0, speed, speed, 20.0, 3, 0))
            pts.append((x_end,   y, 0.0, speed, speed, 20.0, 3, 0))
            pts.append((x_end,   y, 0.0, speed, speed, 20.0, 3, 0))
        return pts

    base_tmpl = snake_template()  # 정방향 템플릿 (Z=0, 이후 덮어씀)
    paths: List[PathPoint] = []

    # 첫 레이어 Z (origin_z + z)에서 시작, 이후 layer_step씩 상승
    for L in range(n_layers):
        z_k = origin_z + z + L * layer_step
        # 홀수(0-based 짝수) 레이어: 정방향, 짝수(0-based 홀수) 레이어: 역방향
        seq = base_tmpl if (L % 2 == 0) else reversed(base_tmpl)
        for x, y, _z0, vx, vy, vz, ext, key in seq:
            paths.append((x, y, z_k, vx, vy, vz, ext, key))

    return paths

# 예시:
# p = generate_snake_fill(width=30, height=30, spacing=1.0,
#                         z=0.2, layer_step=0.2,
#                         speed=20, origin_z=13, n_layers=4)
# -> 레이어 Z: 13.2, 13.4, 13.6, 13.8
# -> 방향: 정, 역, 정, 역


def generate_snake_fill_rotated(
    width: float = 30.0,         # 기판 폭 (mm)
    height: float = 30.0,        # 기판 높이 (mm)
    spacing: float = 1.0,        # 선 간격 (mm)
    z: float = 0.16,             # 첫 레이어 오프셋 (origin_z에 더해짐)
    layer_step: float | None = None,  # 레이어 간 상승량
    speed: float = 20.0,         # 프린트/이동 속도 (mm/s)
    origin_z: float = 13.0,      # 시작 Z 오프셋
    n_layers: int = 4            # 총 레이어 수
) -> List[PathPoint]:
    """
    스네이크 패턴을 시계 방향으로 90도 회전시켜 출력.
    - 1,3,5,... 레이어: 정방향
    - 2,4,6,... 레이어: 역방향
    """
    if layer_step is None:
        layer_step = z

    def snake_template() -> List[PathPoint]:
        """Z=0에서 회전된 스네이크 패턴 생성."""
        pts: List[PathPoint] = []
        num_lines = int(math.floor(width / spacing)) + 1
        x_values = [min(i * spacing, width) for i in range(num_lines)]

        for i, x in enumerate(x_values):
            if i % 2 == 0:
                y_start, y_end = 0.0, height
            else:
                y_start, y_end = height, 0.0

            pts.append((x, y_start, 0.0, speed, speed, 20.0, 3, 0))
            pts.append((x, y_start, 0.0, speed, speed, 20.0, 3, 0))
            pts.append((x, y_end,   0.0, speed, speed, 20.0, 3, 0))
            pts.append((x, y_end,   0.0, speed, speed, 20.0, 3, 0))
        return pts

    base_tmpl = snake_template()
    paths: List[PathPoint] = []

    for L in range(n_layers):
        z_k = origin_z + z + L * layer_step
        seq = base_tmpl if (L % 2 == 0) else reversed(base_tmpl)
        for x, y, _z0, vx, vy, vz, ext, key in seq:
            paths.append((x, y, z_k, vx, vy, vz, ext, key))

    return paths

