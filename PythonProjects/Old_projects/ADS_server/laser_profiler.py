from ctypes import sizeof
import pyads
import time, queue, threading

AMS_NET_ID = '192.168.0.2.1.1'
PLC_PORT = pyads.PORT_TC3PLC1

PLC_VAR_SENSINGTRIGGER = "Temp_Keyence_Exe.bSensingTrigger"
PLC_VAR_SENSECONFIRMED = "Temp_Keyence_Exe.bSenseConfirmed"


def main():
    plc = pyads.Connection(AMS_NET_ID, PLC_PORT)
    plc.open()

    plc.write_by_name(PLC_VAR_SENSINGTRIGGER, True, pyads.PLCTYPE_BOOL)
    time.sleep(0.5)

    while True:
        confirmation = plc.read_by_name(PLC_VAR_SENSECONFIRMED, pyads.PLCTYPE_BOOL)
        if confirmation:
            plc.write_by_name(PLC_VAR_SENSINGTRIGGER, False, pyads.PLCTYPE_BOOL)
            plc.write_by_name(PLC_VAR_SENSECONFIRMED, False, pyads.PLCTYPE_BOOL)
        if not confirmation:
            break
        time.sleep(0.1)
    


if __name__ == "__main__":
    main()