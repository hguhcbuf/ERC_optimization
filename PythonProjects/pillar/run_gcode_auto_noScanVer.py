from NordsonEFD import NordsonEFD
import PLC_motion_controller
from PLC_motion_controller import initiate, run_gcode_file, jog_move_abs, wait_ready
from make_pillar_gcode import write_pillarNoScan_gcode
from capture_trigger import trigger_capture, schedule_capture
from append_log import append_log, wait_file_stable, wait_file_grows
from get_volume_log import read_latest_volume
import time, os

LOG_PROFILE = r"C:\FTP\Keyence\lj-s\result\SD2_005\pedotpss_scale_test1.txt"

V_LIST = [
    0.02, 0.04, 0.06, 0.08, 0.1,
    0.12, 0.14, 0.16, 0.18, 0.2,
    0.22, 0.24, 0.26, 0.28, 0.3,
    0.32, 0.34, 0.36, 0.38, 0.4,
    0.42, 0.44, 0.46, 0.48, 0.5,
    0.55, 0.6, 0.65, 0.7, 0.75,
    0.8, 0.85, 0.9, 0.95, 1.0
]

H_LIST = [
    1, 2, 3, 4, 5,
    6, 7, 8, 9, 10,
    11, 12, 13, 14, 15,
    16, 17, 18, 19, 20
]

X_START, X_END, X_STEP = 20.0, 180.0, 8.0
Y_START, Y_END, Y_STEP = 320.0, 480.0, 8.0

START_V = 0.2
START_H = 1
RESET_XY = False

def iter_positions():
    y = Y_START
    while y <= Y_END + 1e-9:
        x = X_START
        while x <= X_END + 1e-9:
            yield (x, y)
            x += X_STEP
        y += Y_STEP

pos_iter = iter_positions()

# # from x78 to x122
# # y335 to 386
# X_START, X_END, X_STEP = 78.0, 122.0, 1.5
# Y_START, Y_END, Y_STEP = 335.0, 386.0, 1.5

# START_V = 0.02
# START_H = 2
# RESET_XY = False


# def iter_positions():
#     y = Y_START
#     row = 0

#     while y <= Y_END + 1e-9:
#         xs = []
#         x = X_START

#         while x <= X_END + 1e-9:
#             xs.append(x)
#             x += X_STEP

#         if row % 2 == 1:
#             xs = xs[::-1]

#         for x in xs:
#             yield (x, y)

#         y += Y_STEP
#         row += 1


# pos_iter = iter_positions()

initiate()

# 현재 자동화 작동 시작 시간
start_time = time.time()

for v_star in V_LIST:
    for h_star in H_LIST:

        # START 지점 전에는 좌표를 소비하지 않고 스킵
        if RESET_XY:
            if (v_star < START_V) or (v_star == START_V and h_star < START_H):
                continue

            # START 지점 도달하면 좌표 iterator를 새로 시작
            pos_iter = iter_positions()
            RESET_XY = False

        # 실제로 찍는 조합이므로 좌표 1개 소비
        try:
            x, y = next(pos_iter)
        except StopIteration:
            raise RuntimeError("좌표가 부족합니다. (x,y) 그리드를 더 키우거나 step을 줄이세요.")

        prev_sz = os.path.getsize(LOG_PROFILE)

        write_pillarNoScan_gcode(
            x=x,
            y=y,
            v=v_star,
            h=h_star
        )

        wait_ready()
        # 시작 후 경과 시간 계산
        elapsed_sec = time.time() - start_time
        run_gcode_file('pillar_no_scan.nc')
        wait_ready()
        time.sleep(0.5)

        

        append_log(LOG_PROFILE, {
            "v_star": v_star,
            "h_star": h_star,
            "elapsed_sec": round(elapsed_sec, 2),
            "x": x,
            "y": y,
        })

        v_str = f"{v_star:g}"
        h_str = f"{h_star:d}"

        print(
            f"v_star-{v_str}_h_star-{h_str}_"
            f"x-{x:g}_y-{y:g}_"
            f"elapsed-{elapsed_sec:.2f}s"
        )