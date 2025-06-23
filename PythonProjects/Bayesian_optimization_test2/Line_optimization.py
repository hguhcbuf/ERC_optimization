from Line_printing import print_line_by_iter
from NordsonEFD    import NordsonEFD
from Calculate_score import calculate_area_error
from bayes_opt      import BayesianOptimization

import time, os

# ────────────────────────────────────────────────
file_path = r"C:\FTP\Keyence\lj-s\result\SD2_001\250617_034122.txt"
log_dir   = r"C:\Users\Administrator\Documents\JH\optimization_logs"
os.makedirs(log_dir, exist_ok=True)

inst = NordsonEFD(port="COM5", baudrate=115200, timeout=1)
origin_z = 15
count    = 1          # 전역 카운터

def black_box_function(standoff_distance, line_velocity, pressure):
    global count
    standoff_distance = round(standoff_distance, 3)
    line_velocity     = round(line_velocity,   3)
    pressure          = round(pressure,        3)

    inst.SetPressure(pressure)
    print_line_by_iter(count, origin_z, standoff_distance, line_velocity)

    # 단면적을 0.1mm^2 을 향해 최적화한다
    score = calculate_area_error(file_path, 0.1)

    # 여기서 standoff distance, line velocity, pressure, score 값을 flutter로 보내주고싶어

    count += 1
    return -score

# 탐색 공간
pbounds = {
    "standoff_distance": (0.1, 0.5),
    "line_velocity"    : (2, 40),
    "pressure"         : (250, 450)
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