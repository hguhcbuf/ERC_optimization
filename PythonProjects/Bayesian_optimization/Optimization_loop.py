from bayes_opt import BayesianOptimization
import Laser_profiler_controller
import Pressure_value_controller
import Stage_motion_controller
import Calculate_score
import time

file_path = r"C:\FTP\Keyence\lj-s\result\SD2_001\250608_233045.txt"
path_points = [
    ( 100,  380,  80, 60.0, 80.0, 20.0, False),
    ( 100,  380,  32.5, 30.0, 30.0, 20.0, False),
    ( 100,  420,  32.5, 30.0, 30.0, 20.0, True),
    ( 100,  420,  80, 30.0, 30.0, 20.0, False),

    ( 110,  7,  80, 5.0, 20.0, 20.0, False),
]

def black_box_function(speed, pressure):
    score = 0
    speed = round(speed, 1)
    pressure = round(pressure, 1)
    Pressure_value_controller.PressureApply(pressure)
    time.sleep(1)

    path_points = [
        ( 100,  380,  80, 60.0, 80.0, 20.0, False),
        ( 100,  380,  32.5, 30.0, 30.0, 20.0, False),
        ( 100,  420,  32.5, 30.0, speed, 20.0, True),
        ( 100,  420,  80, 30.0, 30.0, 20.0, False),

        ( 110,  7,  80, 5.0, 80.0, 20.0, False),
    ]

    if Stage_motion_controller.run_path(path_points) == True:
        time.sleep(0.5)
        success = Laser_profiler_controller.trigger_sensing()
        if success:
            print("촬영 success")
            score = Calculate_score.calculate_last_line_stddev(file_path)
        else:
            print("촬영 실패")

    time.sleep(5)
    return score

pbounds = {'speed': (2, 20), 'pressure': (30, 70)}

optimizer = BayesianOptimization(
    f=black_box_function,
    pbounds=pbounds,
    random_state=1,
)

if __name__ == "__main__":
    optimizer.maximize(init_points=2, n_iter=4)
    print("Best result:", optimizer.max)