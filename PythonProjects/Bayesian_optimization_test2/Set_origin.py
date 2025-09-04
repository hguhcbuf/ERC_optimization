from PLC_motion_controller import run_path
from NordsonEFD import NordsonEFD
from Line_printing import print_line_by_iter
from NordsonEFD    import NordsonEFD
from Calculate_score import calculate_area_error

from Lattice_printing import print_lattice_by_iter          # (run_id, …)
from Calculate_score  import calculate_lattice_scores 
from Shift_path import shift_path

#  (x좌표, y좌표, z좌표, x속도, y속도, z속도, 압력on/off, 촬영 on/off)
path_points_1 = [
        ( 20,  0,  50, 30.0, 30.0, 30.0,  0, 0),
        ( 20,  390,  50, 30.0, 30.0, 30.0,  0, 0),
]

# # path_points_2 = [
# #         ( 100,  390,  15.2, 30.0, 30.0, 20.0,  2, 0),
# #         ( 110,  390,  15.2, 12.0, 30.0, 20.0,  3, 0),
# #         ( 110,  400,  15.2, 30.0, 12.0, 20.0,  1, 0),
# # ]

run_path(path_points_1)

# new_path_point = shift_path(path_points_1, 10, 0)
# print(new_path_point)



# inst                     = NordsonEFD(port="COM5", baudrate=115200, timeout=1)
# print(inst.SetPressure(400))
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