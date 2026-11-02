from NordsonEFD import NordsonEFD
import PLC_motion_controller
from PLC_motion_controller import initiate, run_gcode_file, jog_move_abs, wait_ready
from make_pillar_gcode import write_pillar_gcode
from capture_trigger import trigger_capture, schedule_capture
from append_log import append_log, wait_file_stable, wait_file_grows
from get_volume_log import read_latest_volume
import time
import os

inst = NordsonEFD(port="COM5", baudrate=115200, timeout=1)


# inst.SetPressure(450)

# print(inst.ReadPressure())

initiate()

run_gcode_file('9x9_sample 2_LFP_pressure 350.nc')