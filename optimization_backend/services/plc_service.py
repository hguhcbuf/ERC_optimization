from models.plc_var import PLC_Var
import time
from typing import Iterable, Sequence, List
import pyads

PLC_AMS = '192.168.0.2.1.1'
PLC_PORT = pyads.PORT_TC3PLC1

# ──────────────────────────────────────────────────────────────
Set_Pos_X       =	PLC_Var('PYADS.ADS_Motor.Set_Pos_X')
Set_Pos_Y       =	PLC_Var('PYADS.ADS_Motor.Set_Pos_Y')
Set_Pos_Z       =	PLC_Var('PYADS.ADS_Motor.Set_Pos_Z')
Set_Vel_X       =	PLC_Var('PYADS.ADS_Motor.Set_Vel_X')
Set_Vel_Y       =	PLC_Var('PYADS.ADS_Motor.Set_Vel_Y')
Set_Vel_Z       =	PLC_Var('PYADS.ADS_Motor.Set_Vel_Z')
Set_Enable_X    =	PLC_Var('PYADS.ADS_Motor.Set_Enable_X')
Set_Enable_Y    =	PLC_Var('PYADS.ADS_Motor.Set_Enable_Y')
Set_Enable_Z    =	PLC_Var('PYADS.ADS_Motor.Set_Enable_Z')
Set_Go          =	PLC_Var('PYADS.ADS_Motor.Set_Go')
Act_Pos_X       =	PLC_Var('PYADS.ADS_Motor.Act_Pos_X')
Act_Pos_Y       =	PLC_Var('PYADS.ADS_Motor.Act_Pos_Y')
Act_Pos_Z       =	PLC_Var('PYADS.ADS_Motor.Act_Pos_Z')
Act_Vel_X       =	PLC_Var('PYADS.ADS_Motor.Act_Vel_X')
Act_Vel_Y       =	PLC_Var('PYADS.ADS_Motor.Act_Vel_Y')
Act_Vel_Z       =	PLC_Var('PYADS.ADS_Motor.Act_Vel_Z')
Get_Enable_X    =	PLC_Var('PYADS.ADS_Motor.Get_Enable_X')
Get_Enable_Y    =	PLC_Var('PYADS.ADS_Motor.Get_Enable_Y')
Get_Enable_Z    =	PLC_Var('PYADS.ADS_Motor.Get_Enable_Z')
Get_IDLE        =	PLC_Var('PYADS.ADS_Motor.Get_IDLE')

Set_KeyenceMode =   PLC_Var('PYADS.ADS_Keyence.Set_KeyenceMode')
Force_Capture	=   PLC_Var('PYADS.ADS_Keyence.Force_Capture')

Set_ExtMode     =   PLC_Var('PYADS.ADS_Nordson.Set_ExtMode')

ALL_VARS: List[PLC_Var] = [Set_Pos_X, Set_Pos_Y, Set_Pos_Z, 
                          Set_Vel_X, Set_Vel_Y, Set_Vel_Z,  
                          Set_Enable_X, Set_Enable_Y, Set_Enable_Z, 
                          Act_Pos_X, Act_Pos_Y, Act_Pos_Z, 
                          Act_Vel_X, Act_Vel_Y, Act_Vel_Z, 
                          Get_Enable_X, Get_Enable_Y, Get_Enable_Z, 
                          Set_Go, Get_IDLE, Set_KeyenceMode, Force_Capture, Set_ExtMode]

# inst = NordsonEFD(port='COM4', baudrate=115200, timeout=1)
# ──────────────────────────────────────────────────────────────



def run_path(path_points: Iterable[Sequence]) -> bool:
    """
    순서대로 좌표·속도·압출을 실행하고 완료되면 True 반환.

    path_points: 각 원소가
       (x, y, z, vx, vy, vz, ExtMode, KeyenceMode)
       [float, float, float, float, float, float, int, int]   
    형태인 리스트(또는 다른 iterable)여야 합니다.
    
    여기서 ExtMode 0 은 압출안함, 1은 압출 끝남, 2는 압출 시작, 3은 압출 유지
    여기서 KeyenceMode 0 : no capture, 1 : capture before move, 2 : capture after move
    """
    try:
        with pyads.Connection(PLC_AMS, PLC_PORT) as plc:

            timeout = 30.0
            #편의기능 PLC.communication.py와 연결
            for v in ALL_VARS:
                v.bind(plc)

            # 축 enable
            Set_Enable_X.write(True)
            Set_Enable_Y.write(True)
            Set_Enable_Z.write(True)

            points = list(path_points)
            if not points:
                print("error : path_points is empty")
                return False
            
            total = len(points)

            x, y, z, vx, vy, vz, extmode, keymode = points[0]
            # 첫 idx 값은 무조건 바로 write
            # 속도
            Set_Vel_X.write(vx)
            Set_Vel_Y.write(vy)
            Set_Vel_Z.write(vz)

            # 위치
            Set_Pos_X.write(x)
            Set_Pos_Y.write(y)
            Set_Pos_Z.write(z)

            # 모드
            Set_ExtMode.write(extmode)
            Set_KeyenceMode.write(keymode)


            for idx in range(total):
                # 1) IDLE 대기 후 Go
                t0 = time.time()
                while not Get_IDLE.read():
                    if time.time() - t0 > timeout:
                        raise RuntimeError("IDLE 대기 timeout")
                    time.sleep(0.001)

                Set_Go.write(True)                     # PLC 가 False 로 내려줄 것
                # print(f"[{idx+1}/{total}] Running")

                # 2) BUSY 로 전환될 때까지
                while Get_IDLE.read():
                    if time.time() - t0 > timeout:
                        raise RuntimeError("BUSY 전환 timeout")
                    time.sleep(0.001)

                # 3) BUSY 중 → 다음 포인트 선적재
                if idx + 1 < total:
                    nx, ny, nz, nvx, nvy, nvz, next_extmode, next_keymode = points[idx + 1]
                    # 속도
                    Set_Vel_X.write(nvx)
                    Set_Vel_Y.write(nvy)
                    Set_Vel_Z.write(nvz)

                    # 위치
                    Set_Pos_X.write(nx)
                    Set_Pos_Y.write(ny)
                    Set_Pos_Z.write(nz)

                    # 모드
                    Set_ExtMode.write(next_extmode)
                    Set_KeyenceMode.write(next_keymode)


                # 4) BUSY → IDLE 복귀 대기
                while not Get_IDLE.read():
                    if time.time() - t0 > timeout:
                        raise RuntimeError("완료 timeout")
                    time.sleep(0.001)
            return True

    except Exception as e:
        # 필요시 로깅이나 재시도 로직 추가
        print(f"[PLC 연결 오류] {e}")
        return False