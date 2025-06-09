from ctypes import sizeof
import pyads
from Nordson import PressureApply
import time, queue, threading

AMS_NET_ID = '192.168.0.2.1.1'
PLC_PORT = pyads.PORT_TC3PLC1
# plc = pyads.Connection(ams_id, )

PLC_VAR_TRIGGER  = "AxisStateMachine.bADS"          # BOOL, rising edge 감시
PLC_VAR_VALUE    = "AxisStateMachine.P"         # 예: INT, 함수 입력
PLC_VAR_ISENDED    = "AxisStateMachine.bPython"   

def my_function(value):
    print(f"Function called with value: {value}")
    # 실제 함수 내용
    time.sleep(1)  # 함수 실행 대기 (예시)
    return "done"


def main():
    plc = pyads.Connection(AMS_NET_ID, PLC_PORT)
    plc.open()
    
    last_trigger = False

    while True:
        trigger = plc.read_by_name(PLC_VAR_TRIGGER, pyads.PLCTYPE_BOOL)
        # print(trigger)
        if trigger and not last_trigger:
            # Rising Edge 발생
            # value = plc.read_by_name(PLC_VAR_VALUE, pyads.PLCTYPE_INT)
            # --> 외부에서 지정하는 Pressure 값
            PressureApply(value)
            plc.write_by_name(PLC_VAR_ISENDED, True, pyads.PLCTYPE_BOOL)
        last_trigger = trigger
        
        time.sleep(0.05)  # 50ms loop

if __name__ == "__main__":
    main()























# # SYM_TRIGGER  = "MAIN.bTrigger"            # PLC BOOL (Rising-edge)
# # SYM_PARAM    = "MAIN.iWorkpieceId"        # 예시: PLC INT (작업 ID)
# # SYM_ENDED    = "MAIN.bIsEnded"            # PLC BOOL (완료 플래그)

# # ---------- 실제 업무 로직 ----------
# def user_function(workpiece_id: int) -> None:
#     """PLC에서 받은 ID로 무거운 작업을 수행하는 가상의 함수."""
#     print(f"[FUNC] Working on ID {workpiece_id}")
#     time.sleep(5)                         # heavy stuff …
#     print(f"[FUNC] ID {workpiece_id} done!")

# # ---------- 내부 구현 ----------
# class PLCBridge:
#     def __init__(self):
#         self.plc = pyads.Connection(AMS_NET_ID, PLC_PORT)
#         self._prev_state = False          # rising-edge 검출용
#         self._lock = threading.Lock()     # 중복 트리거 보호

#     def start(self):
#         self.plc.open()
#         # 트리거 변수에 대한 ADS Notification 세팅
#         attrib = pyads.NotificationAttrib(
#             sizeof(pyads.PLCTYPE_BOOL),
#             pyads.ADSTRANS_SERVERONCHA,    # 값이 바뀔 때마다
#             0, 0                           # maxDelay, cycleTime
#         )
#         self.handle = self.plc.add_device_notification(
#             SYM_TRIGGER, attrib, self._on_trigger
#         )
#         print("Ready – waiting for bTrigger rising edge …")
#         try:
#             while True:
#                 time.sleep(0.5)            # 메인 스레드는 idle
#         finally:
#             self.plc.del_device_notification(self.handle)
#             self.plc.close()

#     # ---------------- 콜백 ----------------
#     def _on_trigger(self, addr, notif, userdata):
#         new_val = bool(notif.value)
#         if new_val and not self._prev_state:       # rising edge!
#             # 중복 호출 방지
#             if self._lock.acquire(blocking=False):
#                 threading.Thread(target=self._pipeline, daemon=True).start()
#         self._prev_state = new_val

#     # ----------- 파이프라인 본체 -----------
#     def _pipeline(self):
#         try:
#             # 1) PLC 데이터 읽기
#             workpiece_id = self.plc.read_by_name(SYM_PARAM, pyads.PLCTYPE_INT)
#             print(f"[PLC ▶︎ PY] Got workpiece ID: {workpiece_id}")

#             # 2) 사용자 함수 실행
#             user_function(workpiece_id)

#             # 3) 완료 플래그 작성
#             self.plc.write_by_name(SYM_ENDED, True, pyads.PLCTYPE_BOOL)
#             print(f"[PY ▶︎ PLC] {SYM_ENDED} := TRUE")

#         finally:
#             # 4) 락 해제 → 다음 트리거 대비
#             self._lock.release()

# # ---------- 실행 ----------
# if __name__ == "__main__":
#     PLCBridge().start()


# # # ───────── 앱 전역 ─────────
# # event_q       = queue.Queue(maxsize=10)    # 트리거 이벤트 버퍼
# # last_trigger  = False                      # 상승 엣지 검출용

# # # ───────── 실제 작업 함수 (예시) ─────────
# # def my_function(x: int) -> None:
# #     """PLC 값으로 무거운 일을 수행하는 자리."""
# #     print(f"[Python] my_function({x}) 실행 중…")
# #     time.sleep(2)      # Heavy work 대신 딜레이
# #     print("[Python] my_function 완료!")

# # # ───────── ADS 콜백 ─────────
# # def on_trigger(addr, notification, user):
# #     """bTrigger 값 바뀔 때마다 호출 (별도 쓰레드)."""
# #     global last_trigger
# #     new_val = bool(notification.value)
# #     if new_val and not last_trigger:       # rising edge만 넣기
# #         try:
# #             event_q.put_nowait(None)       # 내용은 의미 없음
# #             print("[PLC ▶︎ PY] Rising edge 감지 → 작업 큐에 push")
# #         except queue.Full:
# #             print("⚠️  Queue full! 이벤트 누락됨")
# #     last_trigger = new_val                 # 상태 업데이트

# # # ───────── 워커 스레드 ─────────
# # def worker(plc: pyads.Connection):
# #     """큐에 이벤트가 들어오면 PLC에서 값 읽고 함수 실행 후 bIsEnded=TRUE"""
# #     while True:
# #         event_q.get()                      # block until trigger
# #         try:
# #             # 1) PLC 입력값 읽기
# #             inp_val = plc.read_by_name(SYMBOL_INPUT, pyads.PLCTYPE_INT)
# #             print(f"[PY ▶︎ 함수] Read {SYMBOL_INPUT} = {inp_val}")

# #             # 2) 사용자 함수 실행
# #             my_function(inp_val)

# #             # 3) 종료 비트 TRUE
# #             plc.write_by_name(SYMBOL_ENDED, True, pyads.PLCTYPE_BOOL)
# #             print(f"[PY ▶︎ PLC] {SYMBOL_ENDED} ← TRUE")

# #         except Exception as e:
# #             print(f"⚠️  워커 오류: {e}")

# # # ───────── 메인 ─────────
# # def main():
# #     with pyads.Connection(AMS_NET_ID, PLC_PORT) as plc:
# #         # print(plc.get_all_symbols())




# #         # ① bTrigger 변화 통보 설정
# #         attr = pyads.NotificationAttrib(
# #             sizeof(pyads.PLCTYPE_BOOL),
# #             pyads.ADSTRANS_SERVERONCHA,    # 값이 바뀔 때마다
# #             0, 0
# #         )
# #         handle = plc.add_device_notification(SYMBOL_TRIGGER, attr, on_trigger)
# #         print("🔗 ADS 연결 및 Notification 등록 완료!")

# #         # ② 워커 스레드 기동
# #         threading.Thread(target=worker, args=(plc,), daemon=True).start()

# #         try:
# #             while True:
# #                 time.sleep(1)              # 메인 스레드는 그냥 살아만 있음
# #         finally:
# #             plc.del_device_notification(handle)

# # if __name__ == "__main__":
# #     main()