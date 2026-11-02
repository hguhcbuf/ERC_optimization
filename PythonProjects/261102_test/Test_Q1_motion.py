# -*- coding: utf-8 -*-
"""Q1 Jog / NC I 단일 파일 시험 — 기존 파일은 수정하지 않습니다.

배치: 이 파일을 PLC_communication.py 옆에 두고 기존 pyads 환경에서 실행.
PLC: NCI_261028_Axis4_Q1_review의 motQ1 / UserVar.Q1* 인터페이스 필요.
PLC_motion_controller_mod.py/Set_height.py는 import하지 않습니다(자동 실행 방지).

명령 (숫자는 예시이며 실기 안전값이 아닙니다):
  python Test_Q1_motion.py                         # 읽기만: 상태 출력
  python Test_Q1_motion.py jog --velocity 0.01 --seconds 0.3 --direction +
  python Test_Q1_motion.py make-gcode --distance 0.01 --feed 0.6
  python Test_Q1_motion.py gcode --file q1_test.nc --allow-xyz-init
  python Test_Q1_motion.py disable                 # 정지 확인 후 Q1만 disable

Jog: state=0,OpMode=0 또는 state=100,OpMode=1에서만 실행. 모드를 자동 전환하지 않음.
G-code: state=0/100/200 대기에서만 시작. OpMode=2 진입은 XYZ Power/Reference 가능.
make-gcode: 로컬 파일만 생성. PLC PC의 UserVar.GCodeBasePath 폴더에 직접 복사해야 함.
ADS는 파일명만 전달합니다. 로컬 Python 폴더에 .nc를 두는 것으로 업로드되지 않습니다.

시험 전 다른 Python/HMI 명령 송신을 멈추고 큐를 정상적으로 비우십시오.
기존 큐를 삭제하거나 bESTOP/오류를 자동 Reset하거나 PLC 상태를 강제로 쓰지 않습니다.
Commissioned/Enable은 사용자가 RUN 확인한 이동 명령에서 TRUE로 씁니다.
정상 시험 종료 후 Q1 Power는 ON 유지(토크 제거/하중 낙하 방지), disable은 별도 명령.
G-code 이후 SingleGCodeMode=True, ContinueGCode=False, Auto_CodeType=0 유지.
기존 자동 실행 설정을 자동 복원하지 않으므로 공정 재개 전 명시적으로 복원하십시오.

중요: Python Jog 시간 제한은 안전 watchdog이 아닙니다. 프로세스 강제 종료/ADS 단절 시
PLC에 Jog=1이 남을 수 있습니다. 독립 정지 수단이 있는 환경에서만 실기 Jog 사용.
Ctrl+C/오류 시 Jog=0 및 필요 시 bESTOP=True를 최선 노력으로 요청합니다.
통신 실패 시 정지를 보장하지 못하며 Power를 자동 차단하지 않습니다.
PLC/하드웨어 실제 시험은 미실시. 안전 PLC/STO를 대체하지 않습니다.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path
import time

U = 'UserVar.'
M = 'MotorControl.'
ERROR_STATES = {99, 199, 299, 9999}
POLL = 0.05

# 전체 진단 출력. 기존 bError는 과거 오류가 남을 수 있어 단독 중지 판정에 쓰지 않음.
STATUS_TAGS = [
    U+'OpMode', M+'nMotorControlState', M+'bBusy', U+'bESTOP', M+'bError',
    U+'GCodeNameQueue.Count', U+'ContinueGCode', U+'SingleGCodeMode',
    U+'SingleGCodeTRG', U+'Auto_CodeType', U+'GCodeBasePath',
    U+'RunningGCodeName',
    U+'Q1Commissioned', U+'Q1Enable', U+'Q1UseInGCode', U+'Q1Reset',
    U+'Q1JogButton', U+'Q1JogVelocity',
    M+'motQ1.NcToPlc.AxisId', M+'bQ1Linked', M+'bQ1Enable', M+'bQ1Ready',
    M+'bQ1ManualAllowed', M+'bQ1UseLatched', M+'bQ1Reserved', M+'nQ1Interlock',
    M+'fb_Q1Power.Status', M+'fb_Q1Power.Error', M+'fb_Q1Power.ErrorID',
    M+'fb_Q1Status.Valid', M+'fb_Q1Status.StandStill', M+'fb_Q1Status.ErrorStop',
    M+'fb_Q1Status.Error', M+'fb_Q1Status.ErrorID',
    M+'fb_Q1Jog.Busy', M+'fb_Q1Jog.Error', M+'fb_Q1Jog.ErrorID',
    M+'fb_Q1Reset.Busy', M+'fb_Q1Reset.Error', M+'fb_Q1Reset.ErrorID',
    M+'fb_BuildGroupQ1.bErr', M+'fb_BuildGroupQ1.nErrId',
    M+'fb_LoadProgEx.bErr', M+'fb_LoadProgEx.nErrId',
    M+'fb_StartStopEx.bErr', M+'fb_StartStopEx.nErrId',
    M+'motQ1.NcToPlc.SetPos', M+'fQ1ActPos', M+'fQ1ActVelo',
    M+'motQ1.NcToPlc.ErrorCode',
]


class AdsIO:
    """기존 PLC_Var의 bind/read/write를 그대로 재사용."""
    def __init__(self, ams=None, port=None):
        import pyads
        from PLC_communication import PLC_AMS, PLC_PORT, PLC_Var
        self.var_type = PLC_Var
        self.tags = {}
        self.plc = pyads.Connection(ams or PLC_AMS, port or PLC_PORT)
        try:
            self.plc.open()
            self.plc.set_timeout(1000)
            state, _ = self.plc.read_state()
            if state != pyads.ADSSTATE_RUN:
                raise RuntimeError(f'PLC RUN 아님: ADS state={state}')
            print(f'Connected: {ams or PLC_AMS}, port={port or PLC_PORT}')
        except BaseException:
            self.plc.close()
            raise

    def bind(self, name):
        if name not in self.tags:
            v = self.var_type(name)
            v.bind(self.plc)
            self.tags[name] = v
        return self.tags[name]

    def read(self, name):
        return self.bind(name).read()

    def write(self, name, value):
        self.bind(name).write(value)

    def close(self):
        self.plc.close()


class Q1Test:
    def __init__(self, io, check_q1=True):
        self.check_q1 = check_q1
        self.io = io
        self.owned = False
        self.last_state = None

    def r(self, name):
        return self.io.read(name)

    def w(self, name, value):
        self.io.write(name, value)
        print(f'WRITE {name} = {value!r}')

    def status(self):
        for name in STATUS_TAGS:
            try:
                print(f'{name:48s} = {self.r(name)!r}')
            except Exception as exc:
                print(f'{name:48s} = READ ERROR: {exc}')

    def state(self):
        s = int(self.r(M+'nMotorControlState'))
        if s != self.last_state:
            print(f'MotorControl state: {s}')
            self.last_state = s
        return s

    def fault_check(self):
        if self.r(U+'bESTOP') or self.state() in ERROR_STATES:
            raise RuntimeError('ESTOP/PLC 오류 상태. status의 오류 번호 확인; 자동 Reset 안 함.')
        if not self.check_q1:
            return
        if self.r(M+'motQ1.NcToPlc.AxisId') != 4:
            raise RuntimeError('Q1 AxisId가 4가 아닙니다.')
        for fb in ('fb_Q1Power', 'fb_Q1Jog', 'fb_Q1Reset', 'fb_Q1Status'):
            if self.r(M+fb+'.Error'):
                raise RuntimeError(f'{fb}: ErrorID={self.r(M+fb+".ErrorID")}')
        if self.r(M+'motQ1.NcToPlc.ErrorCode') != 0:
            raise RuntimeError(f'NC ErrorCode={self.r(M+"motQ1.NcToPlc.ErrorCode")}')

    def wait(self, predicate, timeout, label, check_fault=True):
        end = time.monotonic() + timeout
        while True:
            if check_fault:
                self.fault_check()
            if predicate():
                return
            if time.monotonic() >= end:
                raise TimeoutError(f'{label}: {timeout:g}초 시간 초과')
            time.sleep(POLL)

    def preflight(self, kind):
        # Bind ALL required interfaces before making any write. Missing PLC code fails closed.
        for name in STATUS_TAGS:
            self.r(name)
        self.fault_check()
        state, mode = self.state(), self.r(U+'OpMode')
        allowed = {(0, 0), (100, 1)}
        if kind != 'jog':
            allowed.add((200, 2))
        if (state, mode) not in allowed:
            raise RuntimeError(f'대기 상태 아님: state={state}, OpMode={mode}')
        if self.r(M+'bBusy') or self.r(M+'bQ1Reserved'):
            raise RuntimeError('기존 작업 또는 Q1 그룹 예약이 남아 있습니다.')
        if self.r(U+'GCodeNameQueue.Count') != 0:
            raise RuntimeError('기존 G-code 큐가 비어 있지 않습니다. 자동 삭제하지 않습니다.')
        for name in ('SingleGCodeTRG', 'JogMovePos', 'Q1Reset', 'bRESET', 'bClearQueue'):
            if self.r(U+name):
                raise RuntimeError(f'{name} 요청이 남아 있습니다.')
        for name in ('JogButtonX', 'JogButtonY', 'JogButtonZ', 'Q1JogButton'):
            if self.r(U+name) != 0:
                raise RuntimeError(f'{name}가 0이 아닙니다.')
        if self.r(M+'fb_Q1Jog.Busy') or self.r(M+'fb_Q1Reset.Busy'):
            raise RuntimeError('Q1 Jog/Reset 진행 중입니다.')
        if self.check_q1 and not self.r(M+'bQ1Linked'):
            raise RuntimeError('motQ1 Link To PLC 확인 필요')

    def arm(self):
        # Called only after an explicit RUN confirmation and repeated preflight.
        self.owned = True
        self.w(U+'Q1Commissioned', True)
        self.w(U+'Q1Enable', True)
        self.wait(lambda: self.r(M+'fb_Q1Power.Status')
                  and self.r(M+'fb_Q1Status.Valid')
                  and self.r(M+'fb_Q1Status.StandStill'), 10, 'Power/정지 준비')

    def abort(self):
        # EStop first: group state machine chooses the NCI stop path for reserved Q1.
        print('시험 중단: 소프트웨어 정지를 요청합니다. 실제 정지를 직접 확인하십시오.')
        for name, value in [(U+'bESTOP', True), (U+'Q1JogButton', 0),
                            (U+'SingleGCodeTRG', False), (U+'ContinueGCode', False)]:
            try:
                self.w(name, value)
            except Exception as exc:
                print(f'정지 요청 실패 [{name}]: {exc}; 독립 정지 수단 필요')
        print('ESTOP/오류는 자동 해제하지 않습니다. NC 상태 확인 후 기존 복구 절차 사용.')

    def jog(self, velocity, seconds, direction):
        self.arm()
        self.w(U+'Q1UseInGCode', False)
        self.w(U+'Q1JogVelocity', velocity)
        self.wait(lambda: self.r(M+'bQ1ManualAllowed'), 3, '수동 허용')
        before = self.r(M+'fQ1ActPos')
        self.w(U+'Q1JogButton', direction)
        active_seen = False
        deadline = time.monotonic() + seconds
        try:
            while time.monotonic() < deadline:
                self.fault_check()
                if self.state() not in (0, 100) or not self.r(M+'fb_Q1Power.Status'):
                    raise RuntimeError('Jog 중 모드/Power 상태 변경')
                active_seen = active_seen or bool(self.r(M+'fb_Q1Jog.Busy'))
                time.sleep(min(POLL, max(0, deadline-time.monotonic())))
        finally:
            self.w(U+'Q1JogButton', 0)
        self.wait(lambda: not self.r(M+'fb_Q1Jog.Busy')
                  and self.r(M+'fb_Q1Status.StandStill'), 10, 'Jog 정지')
        after = self.r(M+'fQ1ActPos')
        print(f'Jog 종료: actual {before} -> {after}, delta={after-before}, Busy 관측={active_seen}')
        print('이 출력은 실제 기구 이동/스케일 정확성을 보증하지 않습니다. Q1 Power는 ON 유지.')
        self.owned = False

    def gcode(self, filename, timeout, use_q1=True):
        # Function API and CLI share this exact PLC handshake.
        self.owned = True
        if use_q1:
            self.arm()
        self.w(U+'ContinueGCode', False)
        self.w(U+'Auto_CodeType', 0)       # CodeName이 기존 큐에도 중복 등록되지 않게 함
        self.w(U+'SingleGCodeMode', True)
        self.w(U+'Q1UseInGCode', use_q1)
        self.w(U+'OpMode', 2)             # Existing XYZ power/reference path may execute
        self.wait(lambda: self.state() == 200 and not self.r(M+'bBusy')
                  and bool(self.r(M+'bQ1UseLatched')) == use_q1
                  and (not use_q1 or self.r(M+'bQ1Ready')),
                  timeout, 'G-code 대기/XYZ 초기화/Q1 준비')
        # Same filename prefix as the supplied PLC_motion_controller_mod.py.
        plc_name = '\\\\' + filename
        self.w('HMIVar.CodeName', plc_name)
        if self.r('HMIVar.CodeName') != plc_name:
            raise RuntimeError('CodeName 읽기 검증 실패')
        if self.r(U+'SingleGCodeTRG'):
            raise RuntimeError('다른 실행 요청 감지')
        self.w(U+'SingleGCodeTRG', True)
        # PLC state 200 consumes the trigger and copies RunningGCodeName in one scan.
        # Do not depend on observing HMIVar.bNaviActive=False: a short file may finish fast.
        self.wait(lambda: not self.r(U+'SingleGCodeTRG')
                  and self.r(U+'RunningGCodeName') == plc_name, 5, '실행 요청 수락')
        self.wait(lambda: self.state() == 200 and not self.r(M+'bBusy')
                  and not self.r(M+'bQ1Reserved'), timeout, '파일 완료 및 그룹 해제')
        self.w(U+'Q1UseInGCode', False)
        print('단일 파일 완료 및 PLC 예약 해제 확인. NC 실제 그룹 해제도 확인하십시오.')
        print('OpMode=2 대기. Q1 Power는 변경하지 않고, 자동 큐 실행 설정은 복원하지 않습니다.')
        self.owned = False

    def disable(self):
        if self.r(M+'fb_Q1Power.Status'):
            if not self.r(M+'fb_Q1Status.Valid') or not self.r(M+'fb_Q1Status.StandStill'):
                raise RuntimeError('유효한 정지 상태 확인 실패')
        self.owned = True
        self.w(U+'Q1UseInGCode', False)
        self.w(U+'Q1Enable', False)
        self.wait(lambda: not self.r(M+'fb_Q1Power.Status'), 5, 'Power OFF', check_fault=False)
        self.w(U+'Q1Commissioned', False)
        self.owned = False
        print('Q1 software enable OFF. XYZ Power는 변경하지 않았습니다.')


def finite_positive(value):
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise argparse.ArgumentTypeError('유한한 양수 필요')
    return result


def basename(value):
    if (not value or value in ('.', '..') or len(value) > 200
            or any(c in value for c in '\\/:*?"<>|')
            or any(ord(c) < 32 or ord(c) > 126 for c in value)
            or not value.lower().endswith('.nc')):
        raise argparse.ArgumentTypeError('영문/숫자 기반 .nc 파일명만 입력 (경로 제외)')
    return value


def make_gcode(filename, distance, feed):
    path = Path(filename)
    content = ('(VERIFY SCALE LIMITS AND CLEARANCE BEFORE HARDWARE USE)\n'
               f'N10 G91\nN20 G01 Q1={distance:.9f} F{feed:.9f}\n'
               f'N30 G01 Q1={-distance:.9f} F{feed:.9f}\nN40 G90\nN50 M02\n')
    if distance < 1e-9 or feed < 1e-9:
        raise ValueError('값이 출력 정밀도보다 작습니다.')
    with path.open('x', encoding='ascii', newline='\n') as f:
        f.write(content)
    print(content)
    print(f'로컬 생성: {path.resolve()}')
    print('PLC의 UserVar.GCodeBasePath 폴더에 직접 복사하세요. 업로드/실행하지 않았습니다.')
    print('M02는 기존 공압 fast-M 출력 해제를 보증하지 않으므로 시험 전 출력 상태 확인.')


def parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--ams', help='생략 시 기존 PLC_communication.PLC_AMS')
    p.add_argument('--port', type=int, help='생략 시 기존 PLC_PORT')
    sub = p.add_subparsers(dest='action')
    sub.add_parser('status', help='읽기만 수행')
    j = sub.add_parser('jog', help='Q1 시간 제한 Jog (0/100 대기 상태에서만)')
    j.add_argument('--velocity', type=finite_positive, required=True)
    j.add_argument('--seconds', type=finite_positive, required=True, help='0 < 시간 <= 2초, 안전 watchdog 아님')
    j.add_argument('--direction', choices=['+', '-'], required=True)
    g = sub.add_parser('gcode', help='PLC PC에 이미 저장된 파일 실행')
    g.add_argument('--file', type=basename, required=True)
    g.add_argument('--timeout', type=finite_positive, default=120)
    g.add_argument('--allow-xyz-init', action='store_true', help='기존 XYZ Power/Reference 경로를 허용')
    mk = sub.add_parser('make-gcode', help='Q1 왕복 예제 로컬 생성; PLC 연결 안 함')
    mk.add_argument('--file', type=basename, default='q1_test.nc')
    mk.add_argument('--distance', type=finite_positive, required=True, help='NC 단위')
    mk.add_argument('--feed', type=finite_positive, required=True, help='Q1 단독 블록 NC 단위/분')
    sub.add_parser('disable', help='정지/비예약 확인 후 Q1 software enable 해제')
    return p


def main(argv=None):
    p = parser()
    args = p.parse_args(argv)
    action = args.action or 'status'
    if action == 'jog' and args.seconds > 2:
        p.error('첫 시험 Jog는 한 번에 최대 2초입니다.')
    if action == 'gcode' and not args.allow_xyz_init:
        p.error('G-code 모드에서 기존 XYZ 초기화가 가능합니다. --allow-xyz-init 명시 필요.')
    if action == 'make-gcode':
        make_gcode(args.file, args.distance, args.feed)
        return 0
    io = None
    test = None
    try:
        io = AdsIO(args.ams, args.port)
        test = Q1Test(io)
        test.status()
        if action == 'status':
            print('\n읽기만 완료. 명령 목록: python Test_Q1_motion.py --help')
            return 0
        test.preflight(action)
        if action == 'gcode':
            print(f'실행 대상 PLC 경로: {test.r(U+"GCodeBasePath")}\\{args.file}')
            print('파일을 이 PLC PC 경로에 복사했는지 확인. XYZ 초기화 및 파일 내 모든 명령 실행 가능.')
        elif action == 'jog':
            print(f'Q1 Jog: 방향={args.direction}, 속도={args.velocity} NC단위/s, 요청시간={args.seconds}s')
            print('ADS 단절/프로세스 종료 시 자동 정지를 보장하지 못합니다.')
        else:
            print('Q1 토크 허가 해제 요청입니다. 하중 유지 조건을 확인하십시오.')
        print('다른 명령 송신 중지, 축/스케일/한계/정지 수단 확인 후에만 진행.')
        if input('실행하려면 RUN 입력 (그 외 취소): ').strip() != 'RUN':
            print('취소: 쓰기 명령 없음')
            return 0
        test.preflight(action)  # User may have waited at the prompt.
        if action == 'gcode':
            from PLC_motion_controller_mod import validate_gcode_path
            validate_gcode_path(test, args.file)
        if action == 'jog':
            test.jog(args.velocity, args.seconds, 1 if args.direction == '+' else -1)
        elif action == 'gcode':
            test.gcode(args.file, args.timeout)
        elif action == 'disable':
            test.disable()
        test.status()
        return 0
    except (Exception, KeyboardInterrupt) as exc:
        print(f'\n중단: {type(exc).__name__}: {exc}')
        if test is not None and test.owned:
            test.abort()
        return 1
    finally:
        if io is not None:
            io.close()


if __name__ == '__main__':
    raise SystemExit(main())

