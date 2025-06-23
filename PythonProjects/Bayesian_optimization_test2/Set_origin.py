from PLC_motion_controller import run_path
from NordsonEFD import NordsonEFD
from Line_printing import print_line_by_iter
from NordsonEFD    import NordsonEFD
from Calculate_score import calculate_area_error

from Lattice_printing import print_lattice_by_iter          # (run_id, …)
from Calculate_score  import calculate_lattice_scores 

# path_points_1 = [
#         ( 100,  390,  15, 30.0, 30.0, 20.0,  0, 0),
# ]

# path_points_2 = [
#         ( 100,  390,  15.2, 30.0, 30.0, 20.0,  2, 0),
#         ( 110,  390,  15.2, 12.0, 30.0, 20.0,  3, 0),
#         ( 110,  400,  15.2, 30.0, 12.0, 20.0,  1, 0),
# ]

# run_path(path_points_2)






inst                     = NordsonEFD(port="COM5", baudrate=115200, timeout=1)
print(inst.SetPressure(200))
print(inst.ReadPressure())




origin_z               = 15.0
first_layer_standoff   = 0.2
inter_layer_standoff   = 0.2
n_ligaments            = 4
line_velocity          = 12.0
num_layers             = 2

print_lattice_by_iter(6, origin_z, first_layer_standoff, inter_layer_standoff, n_ligaments, line_velocity, num_layers)



# FILE_PATH = r"C:\FTP\Keyence\lj-s\result\SD2_001\250617_034122.txt"
# score1, score2, score3 = calculate_lattice_scores(FILE_PATH)
# print(f"surface area={score1:.4f}  volume = {score2:.4f}  score height = {score3:.4f}")