from ctypes import sizeof
import pyads
from Nordson import PressureApply
import time, queue, threading

AMS_NET_ID = '192.168.0.2.1.1'
PLC_PORT = pyads.PORT_TC3PLC1


PLC_VAR_ENABLE_X = "Temp_Motion_Exe.bEnable_X"
PLC_VAR_ENABLE_Y = "Temp_Motion_Exe.bEnable_Y"
PLC_VAR_ENABLE_Z = "Temp_Motion_Exe.bEnable_Z"

PLC_VAR_TARGET_POS_X = "Temp_Motion_Exe.Target_Pos_X"
PLC_VAR_TARGET_POS_Y = "Temp_Motion_Exe.Target_Pos_Y"
PLC_VAR_TARGET_POS_Z = "Temp_Motion_Exe.Target_Pos_Z"

PLC_VAR_TARGET_VEL_X = "Temp_Motion_Exe.Target_Vel_X"
PLC_VAR_TARGET_VEL_Y = "Temp_Motion_Exe.Target_Vel_Y"
PLC_VAR_TARGET_VEL_Z = "Temp_Motion_Exe.Target_Vel_Z"

PLC_VAR_ISMOVED_X = "Temp_Motion_Exe.bIsMoved_X"
PLC_VAR_ISMOVED_Y = "Temp_Motion_Exe.bIsMoved_Y"
PLC_VAR_ISMOVED_Z = "Temp_Motion_Exe.bIsMoved_Z"

PLC_VAR_EXTRUDE = "Temp_Motion_Exe.bExtrude"

# ------------------------------------------------------------------
# x (0-200), y (0-520), z (0-160) 인데 z 0-10은 y축과 부딛힐 수 있음
# (x, y, z, vx, vy, vz, extrude)
path_points = [
    ( 100,  300,  80, 30.0, 10.0, 20.0, False),
]

# path_points = [
#     ( 100,  380,  80, 60.0, 80.0, 20.0, False),
#     ( 100,  380,  32.5, 30.0, 30.0, 20.0, False),
#     ( 100,  420,  32.5, 30.0, 30.0, 20.0, True),
#     ( 100,  420,  80, 30.0, 30.0, 20.0, False),

#     ( 110,  7,  80, 5.0, 20.0, 20.0, False),
# ]

# bIsMoved false로 리셋
def reset_moved_flags(plc):
    plc.write_by_name(PLC_VAR_ISMOVED_X, False, pyads.PLCTYPE_BOOL)
    plc.write_by_name(PLC_VAR_ISMOVED_Y, False, pyads.PLCTYPE_BOOL)
    plc.write_by_name(PLC_VAR_ISMOVED_Z, False, pyads.PLCTYPE_BOOL)

def main() -> None:
    plc = pyads.Connection(AMS_NET_ID, PLC_PORT)
    plc.open()

    # 축 Enable
    plc.write_by_name(PLC_VAR_ENABLE_X, True, pyads.PLCTYPE_BOOL)
    plc.write_by_name(PLC_VAR_ENABLE_Y, True, pyads.PLCTYPE_BOOL)
    plc.write_by_name(PLC_VAR_ENABLE_Z, True, pyads.PLCTYPE_BOOL)

    for idx, (x, y, z, vx, vy, vz, extrude) in enumerate(path_points, start=1):
        print(f"[{idx}/{len(path_points)}] 이동 준비  →  (X={x}, Y={y}, Z={z})")

        # 0. 이전 이동 완료 플래그 초기화
        reset_moved_flags(plc)

        # 1. 속도 먼저 세팅
        plc.write_by_name(PLC_VAR_TARGET_VEL_X, vx, pyads.PLCTYPE_LREAL)
        plc.write_by_name(PLC_VAR_TARGET_VEL_Y, vy, pyads.PLCTYPE_LREAL)
        plc.write_by_name(PLC_VAR_TARGET_VEL_Z, vz, pyads.PLCTYPE_LREAL)

        # 2. 목적지 좌표 & 압출 설정
        plc.write_by_name(PLC_VAR_TARGET_POS_X, x, pyads.PLCTYPE_LREAL)
        plc.write_by_name(PLC_VAR_TARGET_POS_Y, y, pyads.PLCTYPE_LREAL)
        plc.write_by_name(PLC_VAR_TARGET_POS_Z, z, pyads.PLCTYPE_LREAL)

        plc.write_by_name(PLC_VAR_EXTRUDE, extrude, pyads.PLCTYPE_BOOL)

        # 3. 이동 완료 대기 – 세 축 모두 bIsMoved_* 가 True가 될 때까지
        while True:
            is_x = plc.read_by_name(PLC_VAR_ISMOVED_X, pyads.PLCTYPE_BOOL)
            is_y = plc.read_by_name(PLC_VAR_ISMOVED_Y, pyads.PLCTYPE_BOOL)
            is_z = plc.read_by_name(PLC_VAR_ISMOVED_Z, pyads.PLCTYPE_BOOL)
            if is_x and is_y and is_z:
                print(f"    → 도착!  Extrude={extrude}")
                break
            time.sleep(0.05)      # TwinCAT Task 주기보다 약간 길게

    plc.close()
    print("=== 모든 포인트 완료 ===")

if __name__ == "__main__":
    main()