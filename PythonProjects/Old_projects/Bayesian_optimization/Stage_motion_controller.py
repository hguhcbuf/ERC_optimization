
import time
import pyads
from typing import Iterable, Sequence

# ──────────────────────────────────────────────────────────────
AMS_NET_ID = "192.168.0.2.1.1"
PLC_PORT   = pyads.PORT_TC3PLC1

PLC_VAR_ENABLE_X   = "Temp_Motion_Exe.bEnable_X"
PLC_VAR_ENABLE_Y   = "Temp_Motion_Exe.bEnable_Y"
PLC_VAR_ENABLE_Z   = "Temp_Motion_Exe.bEnable_Z"

PLC_VAR_TARGET_POS_X = "Temp_Motion_Exe.Target_Pos_X"
PLC_VAR_TARGET_POS_Y = "Temp_Motion_Exe.Target_Pos_Y"
PLC_VAR_TARGET_POS_Z = "Temp_Motion_Exe.Target_Pos_Z"

PLC_VAR_TARGET_VEL_X = "Temp_Motion_Exe.Target_Vel_X"
PLC_VAR_TARGET_VEL_Y = "Temp_Motion_Exe.Target_Vel_Y"
PLC_VAR_TARGET_VEL_Z = "Temp_Motion_Exe.Target_Vel_Z"

PLC_VAR_ISMOVED_X = "Temp_Motion_Exe.bIsMoved_X"
PLC_VAR_ISMOVED_Y = "Temp_Motion_Exe.bIsMoved_Y"
PLC_VAR_ISMOVED_Z = "Temp_Motion_Exe.bIsMoved_Z"

PLC_VAR_EXTRUDE   = "Temp_Motion_Exe.bExtrude"
# ──────────────────────────────────────────────────────────────


def _reset_moved_flags(plc: pyads.Connection) -> None:
    """bIsMoved 플래그 수동 초기화(프로젝트 설정에 따라 필요)."""
    plc.write_by_name(PLC_VAR_ISMOVED_X, False, pyads.PLCTYPE_BOOL)
    plc.write_by_name(PLC_VAR_ISMOVED_Y, False, pyads.PLCTYPE_BOOL)
    plc.write_by_name(PLC_VAR_ISMOVED_Z, False, pyads.PLCTYPE_BOOL)


def run_path(path_points: Iterable[Sequence]) -> bool:
    """
    순서대로 좌표·속도·압출을 실행하고 완료되면 True 반환.

    path_points: 각 원소가
       (x, y, z, vx, vy, vz, extrude)
    형태인 리스트(또는 다른 iterable)여야 합니다.
    """
    try:
        with pyads.Connection(AMS_NET_ID, PLC_PORT) as plc:
            # 축 enable
            plc.write_by_name(PLC_VAR_ENABLE_X, True, pyads.PLCTYPE_BOOL)
            plc.write_by_name(PLC_VAR_ENABLE_Y, True, pyads.PLCTYPE_BOOL)
            plc.write_by_name(PLC_VAR_ENABLE_Z, True, pyads.PLCTYPE_BOOL)

            total = len(path_points)
            for idx, p in enumerate(path_points, start=1):
                # tuple · list · 기타 시퀀스 모두 지원
                x, y, z, vx, vy, vz, extrude = p

                print(f"[{idx}/{total}] 이동 → ({x}, {y}, {z})  |  v=({vx},{vy},{vz})  |  extrude={extrude}")

                _reset_moved_flags(plc)

                # 속도
                plc.write_by_name(PLC_VAR_TARGET_VEL_X, vx, pyads.PLCTYPE_LREAL)
                plc.write_by_name(PLC_VAR_TARGET_VEL_Y, vy, pyads.PLCTYPE_LREAL)
                plc.write_by_name(PLC_VAR_TARGET_VEL_Z, vz, pyads.PLCTYPE_LREAL)

                # 위치 & 압출 여부
                plc.write_by_name(PLC_VAR_TARGET_POS_X, x, pyads.PLCTYPE_LREAL)
                plc.write_by_name(PLC_VAR_TARGET_POS_Y, y, pyads.PLCTYPE_LREAL)
                plc.write_by_name(PLC_VAR_TARGET_POS_Z, z, pyads.PLCTYPE_LREAL)
                plc.write_by_name(PLC_VAR_EXTRUDE, extrude, pyads.PLCTYPE_BOOL)

                # 세 축 모두 완료될 때까지 대기
                while True:
                    if (plc.read_by_name(PLC_VAR_ISMOVED_X, pyads.PLCTYPE_BOOL) and
                        plc.read_by_name(PLC_VAR_ISMOVED_Y, pyads.PLCTYPE_BOOL) and
                        plc.read_by_name(PLC_VAR_ISMOVED_Z, pyads.PLCTYPE_BOOL)):
                        break
                    time.sleep(0.05)  # TwinCAT 주기보다 살짝 길게

            print("=== 촬영 포인트 도착 ===")
            return True

    except Exception as e:
        # 필요시 로깅이나 재시도 로직 추가
        print(f"[PLC 이동 오류] {e}")
        return False