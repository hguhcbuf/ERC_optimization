from PLC_motion_controller import run_path
from Shift_path import shift_path
from print_snake import generate_snake_fill, generate_snake_fill_rotated

# origin-z = 13

def print_and_scan(iter_num, spacing=1.5, origin_z=13, layer_step=0.1, n_layers=2, move_x:float = 20, move_y:float = 330, speed:float = 20):

    path_2 = generate_snake_fill_rotated(width=20, height=24, spacing=spacing, origin_z=origin_z, layer_step=layer_step, n_layers=n_layers, speed=speed)
    # x 10 - 40, y 300 - 330
    path_2 = shift_path(path_points=path_2, move_x= move_x, move_y= move_y)
    

    last_point = list(path_2[-1])
    last_point[2] = 15
    last_point[6] = 1
    tuple_last_point = tuple(last_point)
    path_2.append(tuple_last_point)

    first_point = list(path_2[0])
    first_point[2] = 15
    first_point[4] = 80
    first_point[6] = 0
    tuple_first_point = tuple(first_point)
    path_2.insert(0, tuple_first_point)

    path_keyence = ( 24.8,  22.8,  30, 50.0, 50.0, 30.0,  0, 2)


    path_2.append(path_keyence)

    

    if not 1 <= iter_num <= 36:
        raise ValueError("iter_num must be between 1 and 102 (inclusive).")

    # 행(row)·열(col) 인덱스 계산
    col = (iter_num - 1) % 6         # 0‒16  →  x 0‒160
    row = (iter_num - 1) // 6        # 0‒5   →  y 0‒120

    dx = col * 24                     # 10 mm 간격
    dy = row * 26                     # 30 mm 간격

    final_path = shift_path(path_2, dx, dy)

    run_path(final_path)

    return 

