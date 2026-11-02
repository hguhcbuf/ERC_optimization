from PLC_communication import PLC_Var
import time
from typing import Iterable, Sequence, List
import pyads


PLC_AMS = '192.168.0.2.1.1'
PLC_PORT = pyads.PORT_TC3PLC1

from typing import List

GVL_NAME = "UserVar"

def sym(name: str) -> str:
    return f"{GVL_NAME}.{name}"

# ──────────────────────────────────────────────────────────────
# New PLC variables (VAR_GLOBAL)
RunningGCodeName = PLC_Var(sym("RunningGCodeName"))     # STRING(255)

ContinueGCode    = PLC_Var(sym("ContinueGCode"))        # BOOL
OpMode           = PLC_Var(sym("OpMode"))               # UDINT (0:OFF, 1:JOG, 2:GCODE)

JogButtonX       = PLC_Var(sym("JogButtonX"))           # INT
JogButtonY       = PLC_Var(sym("JogButtonY"))           # INT
JogButtonZ       = PLC_Var(sym("JogButtonZ"))           # INT
JogVel           = PLC_Var(sym("JogVel"))               # LREAL

JogMovePos       = PLC_Var(sym("JogMovePos"))           # BOOL
JogTargX         = PLC_Var(sym("JogTargX"))             # STRING
JogTargY         = PLC_Var(sym("JogTargY"))             # STRING
JogTargZ         = PLC_Var(sym("JogTargZ"))             # STRING

JogPowerX        = PLC_Var(sym("JogPowerX"))            # BOOL
JogPowerY        = PLC_Var(sym("JogPowerY"))            # BOOL
JogPowerZ        = PLC_Var(sym("JogPowerZ"))            # BOOL

NordsonReadPressureBtn  = PLC_Var(sym("NordsonReadPressureBtn"))   # BOOL
NordsonWritePressureBtn = PLC_Var(sym("NordsonWritePressureBtn"))  # BOOL
NordsonPressureActive   = PLC_Var(sym("NordsonPressureActive"))    # BOOL

LJ_S8000CaptureBtn      = PLC_Var(sym("LJ_S8000CaptureBtn"))       # BOOL
LJ_S8000CaptureActive   = PLC_Var(sym("LJ_S8000CaptureActive"))    # BOOL

GCodeBasePath    = PLC_Var(sym("GCodeBasePath"))         # STRING(255)

Auto_CodeType    = PLC_Var(sym("Auto_CodeType"))         # INT


bStartBackend    = PLC_Var(sym("bStartBackend"))         # BOOL


# g-code 한번만 실행 후 상태 확인
SingleGCodeName = PLC_Var(sym("SingleGCodeName"))   # STRING(255)
StartGCodeOnce  = PLC_Var(sym("StartGCodeOnce"))    # BOOL
GCodeReady      = PLC_Var(sym("GCodeReady"))        # BOOL

# ──────────────────────────────────────────────────────────────
# ALL_VARS: 스칼라 중심으로 구성 (큐/배열은 별도 handling 추천)
ALL_VARS: List[PLC_Var] = [
    RunningGCodeName,
    ContinueGCode,
    OpMode,
    JogButtonX, JogButtonY, JogButtonZ,
    JogVel,
    JogMovePos,
    JogTargX, JogTargY, JogTargZ,
    JogPowerX, JogPowerY, JogPowerZ,
    NordsonReadPressureBtn, NordsonWritePressureBtn, NordsonPressureActive,
    LJ_S8000CaptureBtn, LJ_S8000CaptureActive,
    GCodeBasePath,
    Auto_CodeType,
    bStartBackend,
    SingleGCodeName,
    StartGCodeOnce,
    GCodeReady
]

# ──────────────────────────────────────────────────────────────

plc = None

# def initiate():
#     global plc

#     try:
#         plc = pyads.Connection(PLC_AMS, PLC_PORT)
#         plc.open()

#         plc.set_timeout(5000)  # 5초

#         for v in ALL_VARS:
#             v.bind(plc)

#         print("PLC connected & variables bound")

#         return True

#     except Exception as e:
#         print("PLC init failed:", e)
#         return False

def initiate():
    global plc

    try:
        plc = pyads.Connection(PLC_AMS, PLC_PORT)
        plc.open()
        plc.set_timeout(5000)

        for v in ALL_VARS:
            try:
                v.bind(plc)
                print(f"[OK] {v.name}")
            except Exception as e:
                print(f"[FAIL] {v.name} -> {e}")
                raise

        print("PLC connected & variables bound")
        return True

    except Exception as e:
        print("PLC init failed:", e)
        return False



def run_gcode_file(filename: str = 'pillar.nc',
                   start_pulse: float = 0.1):
    try:
        # GCODE mode
        OpMode.write(2)

        # 파일명 전달
        SingleGCodeName.write(filename)

        # Start pulse
        StartGCodeOnce.write(True)
        time.sleep(start_pulse)
        StartGCodeOnce.write(False)

        return True
    
    except Exception as e:
        print("running gcode failed:", e)
        return False
    



def jog_move_abs(x: float,
                 y: float,
                 z: float,
                 timeout: float = 60.0):
    """
    JOG 모드에서 지정 좌표로 이동
    """

    # JOG mode
    OpMode.write(1)

    # 목표좌표 (STRING이라 문자열로 써야 함)
    JogTargX.write(f"{x:.3f}")
    JogTargY.write(f"{y:.3f}")
    JogTargZ.write(f"{z:.3f}")

    # 이동 트리거
    JogMovePos.write(True)


    # 완료 대기 (Busy 풀릴 때까지)
    t0 = time.time()
    while time.time() - t0 < timeout:
        if GCodeReady.read():   # bBusy 기반 Ready면 이걸 쓰는 게 안전
            return True
        time.sleep(0.05)

    raise RuntimeError("Jog move timeout")


def wait_ready(timeout: float = 600.0, poll: float = 0.05):
    t0 = time.time()
    while not GCodeReady.read():
        if time.time() - t0 > timeout:
            raise RuntimeError("Timeout waiting for GCodeReady")
        time.sleep(poll)