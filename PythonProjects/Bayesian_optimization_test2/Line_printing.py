from PLC_motion_controller import run_path
from NordsonEFD import NordsonEFD
import time
from Shift_path import shift_path
import Shift_path

# inst = NordsonEFD(port='COM4', baudrate=115200, timeout=1)
# inst.SetPressure(50)


#extrude mode : 0 : no extrude, 1: extrude on - extrude off, 2 : extrude off - extrude on, 3 : extrude on - extrude on
#keyence mode 0 : no capture, 1 : capture before move, 2 : capture after move

# z min = 30

# path_points_1 = [
#         ( 100,  390,  15, 30.0, 30.0, 20.0,  0, 0),

#     ]
# path_points_2 = [
#         ( 100,  390,  55, 30.0, 30.0, 20.0,  1, 0),
            
#     ]

# path_points_keyence = [
#         ( 75.6,        41.4,  80,   60.0, 120.0, 20.0,  0, 2),

#     ]




# origin_z = 15
# standoff_distance = 0.2
# line_velocity = 10


# line_starting_point_x = 20
# line_starting_point_y = 318
# line_length = 20
# profiler_point_x = line_starting_point_x - 8.2
# profiler_point_y = line_starting_point_y - 298
# line_ending_point = line_starting_point_y + line_length
# height_z = origin_z + standoff_distance
# z_clearence = origin_z + 5

# line_path_points = [
#         ( line_starting_point_x,   line_starting_point_y,  80,   60.0, 80.0, 40.0,  0, 0),
#         ( line_starting_point_x,   line_starting_point_y,  height_z, 30.0, 10.0, 40.0,  2, 0),
#         ( line_starting_point_x,   line_ending_point ,  height_z, 30.0, line_velocity, 40.0,  1, 0),
#         ( line_starting_point_x,   line_ending_point ,  z_clearence, 30.0, 120, 40.0,  0, 0),
#         ( profiler_point_x,        profiler_point_y,  80,   60.0, 120.0, 40.0,  0, 2),
#         ( line_starting_point_x,   line_starting_point_y,  80,   60.0, 120.0, 40.0,  0, 0),
#     ]

# test_path_point = [
#         ( line_starting_point_x,   line_starting_point_y,  height_z, 30.0, 10.0, 40.0,  0, 0),

#     ]

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

# x (0-200), y (0-520), z (0-160)


# try:
#     print_line_at = shift_path(line_path_points, 10, 60)
#     run_path(print_line_at)
# except Shift_path.PathOutOfRangeError as e:
#     print("좌표 오류:", e)



path_points_1 = [
        ( 100,  390,  15, 30.0, 30.0, 20.0,  0, 0),
]
run_path(path_points_1)

# time.sleep(10)
# run_path(path_points_2)

# run_path(test_path_point)
# 


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
    

# origin_z = 15
# standoff_distance = 0
# line_velocity = 10
# print_line_by_iter(1, origin_z, standoff_distance, line_velocity)