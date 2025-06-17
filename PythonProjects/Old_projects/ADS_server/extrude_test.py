from ctypes import sizeof
import pyads
from Nordson import PressureApply
import time, queue, threading

AMS_NET_ID = '192.168.0.2.1.1'
PLC_PORT = pyads.PORT_TC3PLC1

PLC_VAR_EXTRUDE = "Temp_Motion_Exe.bExtrude"


def main():
    plc = pyads.Connection(AMS_NET_ID, PLC_PORT)
    plc.open()

    num = int(input("Input number : "))

    if num == 0:

        plc.write_by_name(PLC_VAR_EXTRUDE, True, pyads.PLCTYPE_BOOL)
        time.sleep(3)

    plc.write_by_name(PLC_VAR_EXTRUDE, False, pyads.PLCTYPE_BOOL)
    


if __name__ == "__main__":
    main()