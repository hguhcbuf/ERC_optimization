import time
import pyads

# ────────────── PLC 상수 ──────────────
AMS_NET_ID = '192.168.0.2.1.1'
PLC_PORT   = pyads.PORT_TC3PLC1

PLC_VAR_SENSINGTRIGGER = "Temp_Keyence_Exe.bSensingTrigger"
PLC_VAR_SENSECONFIRMED = "Temp_Keyence_Exe.bSenseConfirmed"
# ──────────────────────────────────────


def trigger_sensing(timeout: float = 5.0) -> bool:
    """
    Keyence 센서 트리거 및 확인 절차 수행.
    완료되면 True, 타임아웃되면 False 반환.

    :param timeout: 센싱 확인 대기 최대 시간(초)
    """
    with pyads.Connection(AMS_NET_ID, PLC_PORT) as plc:
        # 1️⃣ SensingTrigger On
        plc.write_by_name(PLC_VAR_SENSINGTRIGGER, True, pyads.PLCTYPE_BOOL)
        time.sleep(0.5)

        # 2️⃣ 센싱 완료 대기
        start_time = time.time()
        while time.time() - start_time < timeout:
            confirmation = plc.read_by_name(PLC_VAR_SENSECONFIRMED, pyads.PLCTYPE_BOOL)
            if confirmation:
                # 센싱 완료 시 SensingTrigger, SenseConfirmed 둘 다 False로 초기화
                plc.write_by_name(PLC_VAR_SENSINGTRIGGER, False, pyads.PLCTYPE_BOOL)
                plc.write_by_name(PLC_VAR_SENSECONFIRMED, False, pyads.PLCTYPE_BOOL)
                return True
            time.sleep(0.1)

        # 타임아웃 시 SensingTrigger Off 후 False 리턴
        plc.write_by_name(PLC_VAR_SENSINGTRIGGER, False, pyads.PLCTYPE_BOOL)
        return False