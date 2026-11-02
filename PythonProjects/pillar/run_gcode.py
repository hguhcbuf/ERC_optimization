# from NordsonEFD import NordsonEFD
# import PLC_motion_controller
from PLC_motion_controller_mod import initiate, run_gcode_file, jog_move_abs, wait_ready
from make_pillar_gcode import write_pillar_gcode, write_pillar_array_gcode
from capture_trigger import trigger_capture, schedule_capture
from append_log import append_log, wait_file_stable, wait_file_grows
from get_volume_log import read_latest_volume
import time
import os

# 1. 최대 높이 (T101) 
# 2. 돌출 부피 (T101) 
# 3. 폭 (T100)
# 4. envelope (T102 트렌드 높이 계측 - 피크 값)
# 5. 연속 프로파일 길이 Developed Profile Length (T100)(ISO 4287)

#x20, y320 이 오른쪽 먼쪽 끝, x180, y480 
#v*=1 is v = 587

# inst = NordsonEFD(port="COM5", baudrate=115200, timeout=1)

LOG_PROFILE = r"C:\FTP\Keyence\lj-s\result\SD2_005\260621_172852.txt"



# inst.SetPressure(300)
# print(inst.ReadPressure())

########################################################################

# 0.07-20, 0.12-12, 0.4-7

initiate()

v_star = 0.05
h_star = 15
trial = 22

prev_sz = os.path.getsize(LOG_PROFILE)

write_pillar_gcode(x = 145.0, y = 450.0, v = v_star, h = h_star)
wait_ready()
run_gcode_file('pillar.nc')
wait_ready()
wait_file_stable(LOG_PROFILE)

wait_file_grows(LOG_PROFILE, prev_sz, timeout_s=15.0)
time.sleep(1)
append_log(LOG_PROFILE, {
    "v_star": v_star,
    "h_star": h_star,
    "trial": trial
})


# trigger_capture(f"pedot14-{trial}_v_star-{v_star}_h_star-{h_star}.png")

##########################################################################

# read_latest_volume(LOG_PROFILE)



# from x80 to x120
# y335 to 375

# running single line!!
# initiate()
# run_gcode_file('single_line.nc')
# run_gcode_file('height_to_scale.nc')
# run_gcode_file('printing_pillar_on_scale.nc')
# run_gcode_file('single_line_on_scale.nc')



# # 10번 뽑기!!
# trial = 1
# for i in range(10):
    
#     x = 40.0 + trial*5
#     write_pillar_gcode(x = x, y = 370.0, v = 1, h = 1.5)

    
#     wait_ready()
#     run_gcode_file('pillar.nc')
#     wait_ready()
#     wait_file_stable(LOG_PROFILE)
#     append_log(LOG_PROFILE, {
#         "finding base volume":0,
#         "trial":trial
#     })
#     trigger_capture(f"finding base volume trial {trial}.png")
#     trial +=1





# initiate()

# wait_ready()

# write_pillar_array_gcode(
#     x0=116.0,
#     y0=335.0,
#     v=0.2,
#     h=10,
#     n=11,
#     m=6,
#     d=2
# )
# run_gcode_file("pillar_array.nc")
