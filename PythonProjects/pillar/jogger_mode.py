from NordsonEFD import NordsonEFD
import PLC_motion_controller
from PLC_motion_controller import initiate, run_gcode_file, jog_move_abs, wait_ready

# inst = NordsonEFD(port="COM5", baudrate=115200, timeout=1)

# LOG_PROFILE = r"C:\FTP\Keyence\lj-s\result\SD1_007\251023_193910.txt"


# inst.SetPressure(250)
# print(inst.ReadPressure())


initiate()

jog_move_abs(x=116, y=335, z=40)

