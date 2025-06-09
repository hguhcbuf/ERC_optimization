from ctypes import sizeof
import pyads
from Nordson import PressureApply
import time, queue, threading

AMS_NET_ID = '192.168.0.2.1.1'
PLC_PORT = pyads.PORT_TC3PLC1
# plc = pyads.Connection(ams_id, )

# PLC_VAR_TRIGGER  = "AxisStateMachine.bADS"          # BOOL, rising edge 감시
# PLC_VAR_VALUE    = "AxisStateMachine.P"         # 예: INT, 함수 입력
# PLC_VAR_ISENDED    = "AxisStateMachine.bPython"   

PLC_VAR_EXTTRIGGER = "Temp_ADS_Exe.bExtTrigger"
PLC_VAR_EXTNUM = "Temp_ADS_Exe.ExtNum"
PLC_VAR_ISCONFIRMED = "Temp_ADS_Exe.bConfirmed"


# def my_function(value):
#     print(f"Function called with value: {value}")
#     # 실제 함수 내용
#     time.sleep(1)  # 함수 실행 대기 (예시)
#     return "done"

time_limit = 5
start_time = time.time()


def main():
    plc = pyads.Connection(AMS_NET_ID, PLC_PORT)
    plc.open()
    
    # last_trigger = False

    num = int(input("Input number : "))

    plc.write_by_name(PLC_VAR_EXTTRIGGER, True, pyads.PLCTYPE_BOOL)
    plc.write_by_name(PLC_VAR_EXTNUM, num, pyads.PLCTYPE_INT)

    while True:
        
        isConfirmed = plc.read_by_name(PLC_VAR_ISCONFIRMED, 
                                       pyads.PLCTYPE_BOOL)
        if isConfirmed:
            plc.write_by_name(PLC_VAR_EXTTRIGGER, False, 
                              pyads.PLCTYPE_BOOL)
            break

        if time.time() - start_time > time_limit:
            print("error, breaking while loop")
            break


        # trigger = plc.read_by_name(PLC_VAR_TRIGGER, pyads.PLCTYPE_BOOL)
        # # print(trigger)
        # if trigger and not last_trigger:
        #     # Rising Edge 발생
        #     value = plc.read_by_name(PLC_VAR_VALUE, pyads.PLCTYPE_INT)
        #     PressureApply(value)
        #     plc.write_by_name(PLC_VAR_ISENDED, True, pyads.PLCTYPE_BOOL)
        # last_trigger = trigger
        
        time.sleep(0.05)  # 50ms loop

if __name__ == "__main__":
    main()