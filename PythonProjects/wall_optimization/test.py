from PLC_motion_controller import run_path
from NordsonEFD import NordsonEFD

from NordsonEFD    import NordsonEFD
from print_walls import generate_straight_fill
from Shift_path import shift_path
from print_snake import generate_snake_fill
from Calculate_score import calculate_score
from print_and_scan import print_and_scan

inst                     = NordsonEFD(port="COM5", baudrate=115200, timeout=1)
print(inst.SetPressure(313.3))
print(inst.ReadPressure())
print_and_scan(iter_num=1, spacing=0.52, origin_z=15, layer_step=0.1, n_layers=6, move_x = 20, move_y = 320, speed = 24)

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