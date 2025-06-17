from Line_printing import print_line_by_iter
from NordsonEFD    import NordsonEFD
from Calculate_score import calculate_last_line_stddev
from bayes_opt      import BayesianOptimization

import time, os

# ────────────────────────────────────────────────
file_path = r"C:\FTP\Keyence\lj-s\result\SD2_001\250617_034122.txt"
log_dir   = r"C:\Users\Administrator\Documents\JH\optimization_logs"
os.makedirs(log_dir, exist_ok=True)

inst = NordsonEFD(port="COM4", baudrate=115200, timeout=1)
origin_z = 15
count    = 1          # 전역 카운터

def black_box_function(standoff_distance, line_velocity, pressure):
    global count
    standoff_distance = round(standoff_distance, 3)
    line_velocity     = round(line_velocity,   3)
    pressure          = round(pressure,        3)

    inst.SetPressure(pressure)
    print_line_by_iter(count, origin_z, standoff_distance, line_velocity)

    score, _ = calculate_last_line_stddev(file_path)
    count += 1
    return -score

# 탐색 공간
pbounds = {
    "standoff_distance": (0.15, 1),
    "line_velocity"    : (1, 50),
    "pressure"         : (30, 200)
}

optimizer = BayesianOptimization(f=black_box_function,
                                 pbounds=pbounds,
                                 random_state=1)




# ──────────────────────────
if __name__ == "__main__":
    optimizer.maximize(init_points=10, n_iter=40)
    


# ───── JSON 저장 ─────
json_log_path = os.path.join(log_dir, f"BO_{time.strftime('%Y%m%d_%H%M%S')}.json")
optimizer.save_state(json_log_path)