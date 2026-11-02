from PLC_communication import PLC_Var
import time
from typing import Iterable, Sequence, List
import pyads


PLC_AMS = '192.168.0.2.1.1'
PLC_PORT = pyads.PORT_TC3PLC1

from typing import List

# GVL_NAME = "UserVar"

def sym(name: str, GVL: str="UserVar") -> str:
    return f"{GVL}.{name}"

# ──────────────────────────────────────────────────────────────
# New PLC variables (VAR_GLOBAL)
RunningGCodeName = PLC_Var(sym("RunningGCodeName"))     # STRING(255)

ContinueGCode    = PLC_Var(sym("ContinueGCode"))        # BOOL
OpMode           = PLC_Var(sym("OpMode"))               # UDINT (0:OFF, 1:JOG, 2:GCODE)

JogButtonX       = PLC_Var(sym("JogButtonX"))           # INT
JogButtonY       = PLC_Var(sym("JogButtonY"))           # INT
JogButtonZ       = PLC_Var(sym("JogButtonZ"))           # INT
# JogVel           = PLC_Var(sym("nMoveAbsVel", "MotorControl"))               # LREAL

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



# g-code 한번만 실행 후 상태 확인
# SingleGCodeName = PLC_Var(sym("SingleGCodeName"))   # STRING(255)
# StartGCodeOnce  = PLC_Var(sym("StartGCodeOnce"))    # BOOL
# GCodeReady      = PLC_Var(sym("GCodeReady"))        # BOOL

SingleGCodeMode   = PLC_Var(sym("SingleGCodeMode"))
SingleGCodeTRG    = PLC_Var(sym("SingleGCodeTRG"))
CodeName          = PLC_Var(sym("CodeName", "HMIVar"))
isReady           = PLC_Var(sym("bNaviActive", "HMIVar"))






# ──────────────────────────────────────────────────────────────
# ALL_VARS: 스칼라 중심으로 구성 (큐/배열은 별도 handling 추천)
ALL_VARS: List[PLC_Var] = [
    RunningGCodeName,
    ContinueGCode,
    OpMode,
    JogButtonX, JogButtonY, JogButtonZ,
    # JogVel,
    JogMovePos,
    JogTargX, JogTargY, JogTargZ,
    JogPowerX, JogPowerY, JogPowerZ,
    NordsonReadPressureBtn, NordsonWritePressureBtn, NordsonPressureActive,
    LJ_S8000CaptureBtn, LJ_S8000CaptureActive,
    GCodeBasePath,
    Auto_CodeType,
    # SingleGCodeName,
    # StartGCodeOnce,
    # GCodeReady
    SingleGCodeMode,
    SingleGCodeTRG,
    CodeName,
    isReady,
]

# ──────────────────────────────────────────────────────────────

plc = None
_io = None
_operation_lock = None


def initiate(ams=PLC_AMS, port=PLC_PORT):
    """Connect without motion. Legacy True/False return contract is retained."""
    global plc, _io, _operation_lock
    import threading
    from Test_Q1_motion import AdsIO
    if _io is not None:
        return True
    candidate = None
    try:
        candidate = AdsIO(ams, port)
        for v in ALL_VARS:
            v.bind(candidate.plc)
        _io, plc = candidate, candidate.plc
        _operation_lock = threading.Lock()
        return True
    except Exception as exc:
        if candidate is not None:
            candidate.close()
        for v in ALL_VARS:
            v._symbol = None
        print("PLC init failed:", exc)
        return False


def _connected():
    if _io is None:
        raise RuntimeError("Call initiate() successfully before using motion functions")
    return _io


def close():
    """Close ADS only; does not disable power or guarantee a machine stop."""
    global plc, _io
    if _io is None:
        return
    if not _operation_lock.acquire(blocking=False):
        raise RuntimeError("Cannot close while a motion function is running")
    try:
        _io.close()
        _io = plc = None
        for v in ALL_VARS:
            v._symbol = None
    finally:
        _operation_lock.release()


def validate_gcode_path(controller, filename):
    """Check the PLC-side directory; no upload and no local existence assumption."""
    import ntpath
    from PLC_communication import GCODE_BASE_PATH
    from Test_Q1_motion import basename, U
    basename(filename)
    actual = controller.r(U + 'GCodeBasePath')
    if ntpath.normcase(ntpath.normpath(actual)) != ntpath.normcase(ntpath.normpath(GCODE_BASE_PATH)):
        raise RuntimeError(f"PLC GCodeBasePath mismatch: {actual!r}; expected {GCODE_BASE_PATH!r}")
    # PLC CONCAT returns STRING(255), including its existing doubled separators.
    if len(actual) + 2 + len(filename) > 255:
        raise ValueError("PLC G-code path exceeds STRING(255)")
    return ntpath.join(GCODE_BASE_PATH, filename)


def _positive(value, name):
    import math
    if isinstance(value, bool) or not math.isfinite(float(value)) or float(value) <= 0:
        raise ValueError(f"{name} must be a finite positive number")
    return float(value)


def _execute(kind, action, *, check_q1=True):
    from Test_Q1_motion import Q1Test
    io = _connected()
    if not _operation_lock.acquire(blocking=False):
        raise RuntimeError("Another operation is running in this process")
    controller = Q1Test(io, check_q1=check_q1)
    try:
        controller.preflight(kind)
        return action(controller)
    except BaseException:
        if controller.owned:
            controller.abort()
        raise
    finally:
        _operation_lock.release()


def run_gcode(filename='test.nc', *, use_q1=False, allow_xyz_init=False, timeout=600.0):
    """Execute one PLC-side .nc file; return True only after completion/group removal.

    use_q1=True explicitly enables/commissions Q1 for this run. Without it, Q1
    faults/power are not a prerequisite for XYZ execution. The caller must know
    whether the file contains Q1 commands; remote file contents are not inspected.
    allow_xyz_init=True permits entering mode 2 from mode 0/1 (XYZ referencing).
    This blocking API raises on errors/timeouts; it never silently retries motion.
    """
    from Test_Q1_motion import basename, M, U
    basename(filename)
    timeout = _positive(timeout, 'timeout')
    if not isinstance(use_q1, bool) or not isinstance(allow_xyz_init, bool):
        raise TypeError('use_q1 and allow_xyz_init must be bool')
    def action(c):
        validate_gcode_path(c, filename)
        if (c.state(), c.r(U+'OpMode')) != (200, 2) and not allow_xyz_init:
            raise RuntimeError('Entering G-code mode may reference XYZ; pass allow_xyz_init=True')
        c.gcode(filename, timeout, use_q1=use_q1)
        return True
    return _execute('gcode', action, check_q1=use_q1)


def run_gcode_file(filename='pillar.nc', start_pulse=0.1, **kwargs):
    """Compatibility name; now BLOCKS until complete and raises on failure.

    start_pulse is accepted for old callers but no longer generates a timed pulse:
    PLC state 200 consumes SingleGCodeTRG. Pass the same options as run_gcode().
    """
    _positive(start_pulse, 'start_pulse')
    return run_gcode(filename, **kwargs)


def jog_q1(*, velocity, seconds, direction='+'):
    """Timed Q1 jog in idle state 0/100. NC units/s; maximum 2 seconds.

    Calling explicitly confirms Q1 commissioning. ADS loss/process termination
    can leave a Jog request active: this timer is NOT a PLC watchdog.
    """
    velocity = _positive(velocity, 'velocity')
    seconds = _positive(seconds, 'seconds')
    if seconds > 2 or direction not in ('+', '-'):
        raise ValueError("seconds must be <= 2 and direction must be '+' or '-'")
    def action(c):
        c.jog(velocity, seconds, 1 if direction == '+' else -1)
        return True
    return _execute('jog', action)


def disable_q1():
    """Remove Q1 software power permission only when idle and unreserved."""
    def action(c):
        c.disable()
        return True
    return _execute('disable', action)


def get_status():
    """Read diagnostics; raise on unavailable symbols/ADS failure."""
    from Test_Q1_motion import STATUS_TAGS
    io = _connected()
    return {name: io.read(name) for name in STATUS_TAGS}


def wait_ready(timeout=600.0, poll=0.05):
    """Wait for PLC idle; this alone is not evidence that a new request ran."""
    from Test_Q1_motion import Q1Test, M, U
    timeout = _positive(timeout, 'timeout')
    poll = _positive(poll, 'poll')
    c = Q1Test(_connected(), check_q1=False)
    deadline = time.monotonic() + timeout
    while True:
        c.fault_check()
        if (c.state(), c.r(U+'OpMode')) in ((0, 0), (100, 1), (200, 2)) and not c.r(M+'bBusy') and not c.r(M+'bQ1Reserved') and not c.r(U+'SingleGCodeTRG'):
            return True
        if time.monotonic() >= deadline:
            raise TimeoutError('Timeout waiting for PLC idle')
        time.sleep(poll)
