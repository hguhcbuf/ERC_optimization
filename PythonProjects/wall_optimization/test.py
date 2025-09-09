from PLC_motion_controller import run_path
from NordsonEFD import NordsonEFD

from NordsonEFD    import NordsonEFD
from print_walls import generate_straight_fill
from Shift_path import shift_path
from print_snake import generate_snake_fill
from Calculate_score import calculate_score
from print_and_scan import print_and_scan
import numpy as np

import numpy as np

import numpy as np

import numpy as np

def calculate_score_std(line, file_path=r"C:\FTP\Keyence\lj-s\result\SD1_006\250829_104449.txt"):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 마지막 두 번째 줄 가져오기
    second_last_line = lines[line].strip()

    def parse_line(line):
        parts = line.split(',')
        values = []
        for val in parts:
            val = val.strip()
            if val.startswith('+'):
                val = val[1:]
            try:
                values.append(float(val))
            except ValueError:
                continue
        return np.array(values, dtype=float)

    values = parse_line(second_last_line)
    if values.size == 0:
        raise ValueError("값이 없습니다.")

    # 평균과 표준편차 계산
    avg_val = float(np.mean(values))
    std_val = float(np.std(values, ddof=0))  # 표준편차 (단위: mm)

    # ---- 범위 보정 ----
    # avg 범위: 16 ~ 70
    if avg_val < 16:
        avg_val = 16.0
    elif avg_val > 70:
        avg_val = 70.0

    # std 범위: 0 ~ 5
    if std_val < 0:
        std_val = 0.0
    elif std_val > 3:
        std_val = 3.0

    # ---- Min-Max Normalization ----
    norm_avg = (avg_val - 16) / (70 - 16)   # [0,1]
    norm_std = (std_val - 0) / (3 - 0)      # [0,1]

    # ---- Score ----
    score = norm_avg - norm_std

    return norm_avg, norm_std



# 테스트 루프 (끝에서부터 2칸씩 올라가며)
c = -2
for i in range(50):
    a, b = calculate_score_std(line=c)
    print(f"line {c:4d} -> avg = {a:.6f}, fwhm = {b:.6f}")
    c += -2




# inst                     = NordsonEFD(port="COM5", baudrate=115200, timeout=1)
# print(inst.SetPressure(313.3))
# print(inst.ReadPressure())
# print_and_scan(iter_num=1, spacing=0.52, origin_z=15, layer_step=0.1, n_layers=6, move_x = 20, move_y = 320, speed = 24)

# file_path = r"C:\FTP\Keyence\lj-s\result\SD1_006\250819_124738.txt"
# a = calculate_score(file_path)
# print(a)
# # def generate_straight_fill(
#     width: float = 30.0,        # 기판 폭 (mm)
#     height: float = 30.0,       # 기판 높이 ( mm)
#     spacing: float = 1.0,       # 선 간격 (mm)
#     z: float = 0.2,             # 적층 높이 (mm)
#     speed: float = 20.0,        # 프린트 속도 (mm/s)
#     ext_on: int = 1,            # 압력 on 플래그
#     ext_off: int = 0,           # 압력 off 플래그
#     key_off: int = 0            # 촬영 off (필요시 1로 변경)
# ) -> List[PathPoint]:
    
# path = generate_straight_fill(origin_z=13)

# path = shift_path(path_points=path, move_x= 40, move_y= 330)



# path_2 = generate_snake_fill(width=24, height=20, spacing=1.5, origin_z=13, layer_step= 0.1, n_layers=2)
# # x 10 - 40, y 300 - 330
# path_2 = shift_path(path_points=path_2, move_x= 40, move_y= 330)
# last_point = list(path_2[-1])
# last_point[2] = 15
# last_point[6] = 1
# tuple_last_point = tuple(last_point)
# path_2.append(tuple_last_point)

# first_point = list(path_2[0])
# first_point[6] = 0
# tuple_first_point = tuple(first_point)
# path_2.insert(0, tuple_first_point)

# path_keyence = ( 40.8,  31.8,  30, 50.0, 50.0, 30.0,  0, 2)


# path_2.append(path_keyence)

# for i in path_2:
#     print(i)

# run_path(path_2)



# run_path(path_keyence)



# #  (x좌표, y좌표, z좌표, x속도, y속도, z속도, 압력on/off, 촬영 on/off)
# path_points_2 = [
#         ( 25,  315,  30, 50.0, 50.0, 30.0,  0, 1),
# ]
# path_points_1 = [
#         ( 40,  330,  13, 50.0, 50.0, 30.0,  0, 1),
# ]
# run_path(path_points_1)

# # # path_points_2 = [
# # #         ( 100,  390,  15.2, 30.0, 30.0, 20.0,  2, 0),
# # #         ( 110,  390,  15.2, 12.0, 30.0, 20.0,  3, 0),
# # #         ( 110,  400,  15.2, 30.0, 12.0, 20.0,  1, 0),
# # # ]



# new_path_point = shift_path(path_points_1, 10, 0)
# print(new_path_point)



# inst                     = NordsonEFD(port="COM5", baudrate=115200, timeout=1)
# print(inst.SetPressure(300))
# print(inst.ReadPressure())




# origin_z               = 15.0
# first_layer_standoff   = 0.2
# inter_layer_standoff   = 0.2
# n_ligaments            = 4
# line_velocity          = 12.0
# num_layers             = 2

# print_lattice_by_iter(6, origin_z, first_layer_standoff, inter_layer_standoff, n_ligaments, line_velocity, num_layers)

# print_line_by_iter(1, 15, 0.2, 8)

# FILE_PATH = r"C:\FTP\Keyence\lj-s\result\SD2_001\250617_034122.txt"
# score1, score2, score3 = calculate_lattice_scores(FILE_PATH)
# print(f"surface area={score1:.4f}  volume = {score2:.4f}  score height = {score3:.4f}")