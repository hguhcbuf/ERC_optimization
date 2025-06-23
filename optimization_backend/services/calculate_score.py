import numpy as np
import time
import os

def calculate_area_error(file_path: str, target_area: float = 0.1) -> float:
    """
    파일의 **마지막 줄** 숫자 값들이 `target_area`와 얼마나
    차이나는지(절대 오차)의 평균을 계산해 반환한다.

    반환값: mean_abs_error (소수점 3자리, float)

    예) 값이 [98, 101, 99] 이면  
        |98-100| + |101-100| + |99-100| = 1 + 1 + 1 = 3 → 3/3 = 1.0
    """
    with open(file_path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    if not lines:
        raise ValueError("파일에 데이터가 없습니다.")

    # 마지막 줄 → 쉼표로 분리
    last_values = []
    for tok in lines[-1].split(","):
        tok = tok.strip()
        if not tok:
            continue
        if tok[0] in "+-":
            sign = -1.0 if tok[0] == "-" else 1.0
            tok = tok[1:]
        else:
            sign = 1.0
        try:
            val = sign * float(tok)
            last_values.append(val)
        except ValueError:
            continue

    if not last_values:
        raise ValueError("마지막 줄에 숫자 데이터가 없습니다.")

    # 절대 오차 평균
    mean_err = float(np.mean([abs(v - target_area) for v in last_values]))
    return round(mean_err, 3)
