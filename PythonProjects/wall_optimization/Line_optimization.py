from print_and_scan import print_and_scan
from NordsonEFD    import NordsonEFD
from bayes_opt      import BayesianOptimization
import time, os
from Calculate_score import calculate_score, calculate_score_3sigma

# ────────────────────────────────────────────────
file_path = r"C:\FTP\Keyence\lj-s\result\SD1_006\250829_104449.txt"
log_dir   = r"C:\Users\Administrator\Documents\JH\optimization_logs"
os.makedirs(log_dir, exist_ok=True)

inst = NordsonEFD(port="COM5", baudrate=115200, timeout=1)
origin_z = 15
total_height = 0.7
count    = 1          # 전역 카운터

def black_box_function(number_of_layers, line_velocity, pressure, spacing):
    global count
    #layer_step 은 number of layers 에의해 결정됨
    number_of_layers = round(number_of_layers)
    layer_step = round((total_height-0.1)/number_of_layers, 3)
    line_velocity     = round(line_velocity,   3)
    pressure          = round(pressure,        3)
    spacing = round(spacing, 3)

    inst.SetPressure(pressure)
    #print_line_by_iter(count, origin_z, standoff_distance, line_velocity)
    print_and_scan(count, spacing=spacing, origin_z=13, layer_step=layer_step, n_layers=number_of_layers, move_x = 20, move_y = 320, speed = line_velocity)

    # 단면적을 0.1mm^2 을 향해 최적화한다
    time.sleep(7)
    score = calculate_score_3sigma(file_path)

    # 여기서 standoff distance, line velocity, pressure, score 값을 flutter로 보내주고싶어

    count += 1
    return score

# 탐색 공간
pbounds = {
    "number_of_layers": (2.5, 6.5),
    "line_velocity"    : (15, 30),
    "pressure"         : (150,300), 
    "spacing" : (0.36, 0.6),
}

optimizer = BayesianOptimization(f=black_box_function,
                                 pbounds=pbounds,
                                 random_state=1)




# ──────────────────────────
if __name__ == "__main__":
    optimizer.maximize(init_points=10, n_iter=26)
    


# ───── JSON 저장 ─────
json_log_path = os.path.join(log_dir, f"BO_{time.strftime('%Y%m%d_%H%M%S')}.json")
optimizer.save_state(json_log_path)