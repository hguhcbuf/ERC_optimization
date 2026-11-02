from bayes_opt import BayesianOptimization
from Functions import calculate_last_line_stddev, write_gcode
from PLC_motion_controller_mod import run_gcode_file, initiate, wait_ready
import time

file_path = r"C:\FTP\Keyence\lj-s\result\SD1_002\260919_135021.txt"
initiate()
xx = 20
def black_box_function(velocity, pressure, standoff_distance):
    global xx
    write_gcode(x=xx, y=350, v=velocity, h=standoff_distance, p=pressure)
    run_gcode_file("EGaln_line.nc")
    wait_ready()
    time.sleep(1)
    score = calculate_last_line_stddev(file_path)
    
    xx+=5
    return score

pbounds = {'velocity': (10, 30), 'pressure': (300,350), 'standoff_distance': (0.1, 0.3)}

optimizer = BayesianOptimization(
    f=black_box_function,
    pbounds=pbounds,
    random_state=1,
)


optimizer.maximize(init_points=6, n_iter=24)
