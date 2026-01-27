from PLC_motion_controller import run_path

path_points_1 = [
       ( 15,  330,  73, 50.0, 50.0, 30.0,  0, 0),
]

# path_points_1 = [( 20,  19.8,  30, 100.0, 150.0, 30.0,  0, 2)]

run_path(path_points_1)


# path_keyence = [( 24.8,  21.8,  30, 50.0, 50.0, 30.0,  0, 2)]
# run_path(path_keyence)