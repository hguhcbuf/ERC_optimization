# 261102_test: PLC 함수 API

기준 PLC: `hguhcbuf/PAMOS-control` commit `6e04b78ccaa3bc1cff0a4cb4ab03b7ee25554b91`.
Python 기준: `ERC_optimization` commit `503379194111ba41bcd305a7f706dbbe0495473c`.
PLC 프로젝트는 수정하지 않았습니다. 기존 pyads 환경을 사용합니다.

## 파일 경로와 실행

G-code는 **PLC PC**의 `C:\Users\Administrator\Desktop\GCodes`에 저장합니다.
`test.nc`는 사용자가 실행 성공을 확인한 파일이며, 내용은 이 저장소에 없습니다.
API는 ADS로 파일명만 전달합니다. 파일 업로드, 생성, 파일 내용 검증은 하지 않습니다.
`UserVar.GCodeBasePath`를 읽어 위 경로와 일치하는지 검사하며 임의로 변경하지 않습니다.
PLC 소스의 중복 역슬래시는 경로 비교 시 정규화하고, 기존 `HMIVar.CodeName`의
두 역슬래시 접두사는 유지합니다. `f_MakeAbsPath`는 두 문자열을 CONCAT합니다.
파일명은 경로를 제외한 ASCII `.nc` 이름만 허용합니다.

이 폴더를 작업 디렉터리로 사용하거나 Python import 경로에 넣으세요.
모듈 import만으로 ADS 연결이나 모션은 시작하지 않습니다.

```python
from PLC_motion_controller_mod import initiate, run_gcode, close

if not initiate():
    raise RuntimeError('PLC 연결 실패')
try:
    # XYZ 전용 파일. mode 0/1에서 mode 2로 진입하면 기존 XYZ 초기화/참조가 가능.
    run_gcode('test.nc', allow_xyz_init=True)
finally:
    close()
```

Q1 명령이 들어간 파일이라면 실행 호출을 다음처럼 바꿉니다.

```python
run_gcode('test.nc', use_q1=True, allow_xyz_init=True, timeout=600)
```

`use_q1=True` 호출은 Q1 commissioning 확인과 enable을 명시적으로 요청합니다.
파일에 Q1 명령이 있는지는 호출자가 알아야 합니다. 기본값은 `False`이며 Q1 전원을
켜지 않고 XYZ 경로만 선택합니다. `allow_xyz_init=False` 기본값에서는 이미
state=200/OpMode=2인 경우에만 실행합니다. 매번 허용 인자를 쓰고 싶지 않다면
상위 앱에서 장비 초기화 단계의 책임을 명확히 한 래퍼 함수를 만드세요.

## 함수

| 함수 | 동작 |
|---|---|
| `initiate(ams=..., port=...)` | 연결 및 기존 PLC_Var 바인딩; 성공 True, 실패 False |
| `run_gcode(filename='test.nc', use_q1=False, allow_xyz_init=False, timeout=600)` | 단일 파일 완료까지 blocking; 성공 True, 실패 예외 |
| `run_gcode_file(filename='pillar.nc', start_pulse=0.1, **kwargs)` | 기존 이름 호환; run_gcode와 동일하게 완료까지 대기 |
| `jog_q1(velocity=..., seconds=..., direction='+')` | state 0/100에서 Q1 Jog; 최대 2초, 정상 종료 후 버튼 0 |
| `disable_q1()` | 대기·비예약·정지 확인 후 Q1 enable 및 commissioning 해제 |
| `get_status()` | PLC 진단 값을 dict로 반환; 읽기만 수행 |
| `wait_ready(timeout=600, poll=0.05)` | idle 대기; 새 명령 실행 성공을 단독으로 입증하지 않음 |
| `close()` | ADS 연결 종료; 축 power를 끄지 않음 |

`run_gcode_file()`는 이전과 달리 **완료까지 기다리고 실패 시 예외를 발생**시킵니다.
기존 `start_pulse` 인자는 허용하지만 실제 펄스를 만들지는 않습니다. PLC가 trigger를
소비하는 것을 확인합니다. 자동화 호출부는 기존 False 반환 검사 대신 try/except를 사용하세요.
UI에서는 blocking 모션 함수를 UI 메인 스레드 밖의 작업 스레드에서 실행하세요.
한 프로세스 내 모션 중복 호출은 거부합니다. 다른 Python/HMI 프로세스와의 분산 잠금은
아니므로 다른 명령 송신자는 정지해야 합니다. 기존 ALL_VARS/raw write는 잠금을 우회합니다.

Jog 예시(속도는 NC 단위/초이며 실기 안전값을 뜻하지 않음):

```python
from PLC_motion_controller_mod import initiate, jog_q1, close
if not initiate():
    raise RuntimeError('PLC 연결 실패')
try:
    jog_q1(velocity=0.01, seconds=0.3, direction='+')
finally:
    close()
```

G-code 종료 후에는 state 200이므로 바로 Jog할 수 없습니다. 기존 장비 모드 전환 절차로
state 0 또는 100에 도달한 후 Jog하세요. 이 API는 Jog를 위해 XYZ 모드를 자동 전환하지 않습니다.
Q1 Reset과 ESTOP 해제는 기존 장비 복구 절차로 수행합니다.

## PLC 실행 순서와 종료 상태

- state 0/100/200의 모드 일치, 비예약, 큐 비어 있음, 미처리 trigger/Jog/Reset 없음 확인.
- 선택된 축에 필요한 오류 검사. XYZ 전용 실행은 Q1의 Power/Link/오류를 준비조건으로 요구하지 않음.
  단, 업데이트된 PLC의 Q1 심볼 존재 및 기존 Q1 Jog/예약 없음은 확인합니다.
- `ContinueGCode=False`, `Auto_CodeType=0`, `SingleGCodeMode=True` 설정.
- `Q1UseInGCode`를 지정하고 mode 2에서 state 200의 latch 일치까지 대기.
- `HMIVar.CodeName` 설정, `SingleGCodeTRG=True` 쓰기.
- PLC가 trigger를 False로 소비하고 RunningGCodeName이 일치하는지 확인.
- state 200, bBusy=False, bQ1Reserved=False까지 대기. 짧은 파일도 bNaviActive 전이 관측에 의존하지 않음.
- 종료 후 Q1UseInGCode=False. mode 2 대기 유지; Q1 사용 시 power ON 유지.
- SingleGCodeMode=True / ContinueGCode=False / Auto_CodeType=0은 자동 복원하지 않음.

`timeout`은 준비 대기와 완료 대기에 각각 적용하며, 요청 수락은 최대 5초입니다.
ADS 개별 호출의 시간도 있으므로 전체 호출 시간의 엄격한 상한은 아닙니다.
오류/취소/시간 초과가 쓰기 이후 발생하면 bESTOP=True 등을 최선 노력으로 요청합니다.
오류를 자동 reset하거나 명령을 자동 재시도하지 않습니다. ADS 단절이나 프로세스 강제 종료
시에는 정지를 보장하지 못하며, Python Jog 타이머는 PLC watchdog이 아닙니다.

## 기존 CLI

```powershell
python Test_Q1_motion.py
python Test_Q1_motion.py gcode --file test.nc --allow-xyz-init
python Set_height.py --file test.nc --allow-xyz-init
python Set_height.py --file test.nc --use-q1 --allow-xyz-init
```

`Test_Q1_motion.py gcode`는 기존처럼 **Q1 포함 실행**입니다. XYZ 전용은 API 또는
`Set_height.py`의 기본 모드를 사용하세요. CLI는 RUN 입력을 요구하고 함수 API는
명시적 함수 호출을 실행 요청으로 취급합니다. `Set_height.py` 기본 파일은 기존의
`set_height.nc`이며, 사용되지 않는 외부 생성기 import를 제거했습니다.

`q1_test.nc`는 기존 예제를 그대로 보존했습니다. 실기에서 검증되지 않은 NC 단위·feed를
확대하지 않았고 `test.nc`를 임의로 새로 생성하지 않았습니다.

## 검증과 적용

오프라인 테스트(가짜 PLC, ADS 연결 없음):

```powershell
python -m unittest -v test_motion_api
```

14개 테스트: 즉시 완료/동일 파일 재실행, Q1 선택·오류 분리, 큐·ESTOP·busy 거부,
XYZ 초기화 허용, 경로·파일명·비유한 값 검증, 수락·완료 timeout의 stop 요청,
Jog 종료 버튼 해제, import 부작용 없음, 동시 실행 거부, 기존 함수 이름 호환.

장비 시험: 먼저 status 조회 → 기존 test.nc를 내용에 맞는 use_q1 선택으로 실행 →
실제 종료 위치/NC 상태/오류 확인 → 동일 파일 재실행 확인 → 기존 XYZ 파일 검증.
PLC Build/장비 시험은 이 변경 작업에서 수행하지 않았습니다. 테스트 통과는 하드웨어 검증이 아닙니다.
