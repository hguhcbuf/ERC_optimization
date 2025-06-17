import numpy as np
import time
import os

def calculate_last_line_stddev(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 마지막 줄의 숫자 데이터만 가져오기
    last_line = lines[-1].strip()
    # 데이터 부분만 파싱 (쉼표로 구분)
    data_strings = last_line.split(',')

    # 숫자 앞의 + 기호 제거 후 float로 변환
    values = []
    for val in data_strings:
        val = val.strip()
        if val.startswith('+'):
            val = val[1:]
        try:
            f_val = float(val)
            if f_val != 0.0:
                values.append(f_val)
        except ValueError:
            # 숫자가 아니면 무시
            continue

    if not values:
        print("데이터가 없습니다.")
        return
    
    # print(values)
    # print(len(values))

    # 표준편차 계산
    stddev = np.std(values, ddof=0)  # ddof=0이면 표본이 아닌 모집단 표준편차
    average = np.average(values)

    return round(stddev, 3), round(average, 3)

# ──────────────────────────────────────────────────────────────
def wait_for_update_then_calc(file_path: str,
                              poll_sec: float = 1.0,
                              timeout_sec: float = 10.0) -> float:
    """
    파일이 `timeout_sec` 안에 수정되면 stddev 계산값을 반환,
    그렇지 않으면 TimeoutError 발생.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)

    last_mtime       = os.path.getmtime(file_path)
    last_change_time = time.time()          # 마지막 변경 감지 시각

    while True:
        time.sleep(poll_sec)

        current_mtime = os.path.getmtime(file_path)
        if current_mtime != last_mtime:     # 👉 파일이 바뀜!
            last_mtime       = current_mtime
            last_change_time = time.time()  # 타이머 리셋
            return calculate_last_line_stddev(file_path)

        # 변화가 없으면 타임아웃 체크 --> 그냥 계산
        if (time.time() - last_change_time) > timeout_sec:
            return calculate_last_line_stddev(file_path)
import numpy as np





# def calculate_lattice_scores(file_path: str):
#     """
#     파일 끝 두 줄의 숫자 합계를 계산해 (score_1, score_2) 튜플로 반환한다.

#     • 마지막에서 2번째 줄  →  score_1
#     • 마지막      줄       →  score_2

#     각 줄은
#         +000000.166,+000000.157,…
#     같은 형식이며 ‘+’ 기호·선행 0 을 포함한다.
#     공백·빈 토큰·숫자가 아닌 토큰은 무시한다.

#     반환값은 (round(score_1, 3), round(score_2, 3))
#     """
#     with open(file_path, "r", encoding="utf-8") as f:
#         # 공백 줄 제거 후 스트립
#         lines = [ln.strip() for ln in f if ln.strip()]

#     if len(lines) < 2:
#         raise ValueError("파일에 데이터 줄이 2개 미만입니다.")

#     line_2nd_last, line_last = lines[-2], lines[-1]

#     def sum_line(line: str) -> float:
#         total = 0.0
#         for token in line.split(","):
#             token = token.strip()
#             if not token:
#                 continue
#             # + 또는 - 기호 제거
#             if token[0] in "+-":
#                 sign = -1.0 if token[0] == "-" else 1.0
#                 token = token[1:]
#             else:
#                 sign = 1.0
#             try:
#                 total += sign * float(token)
#             except ValueError:
#                 # 숫자가 아니면 패스
#                 continue
#         return total

#     score_1 = sum_line(line_2nd_last)
#     score_2 = sum_line(line_last)

#     return round(score_1, 3), round(score_2, 3)


def calculate_lattice_scores(file_path: str):
    """
    파일 끝 3 줄을 이용해 (score_1, score_2)를 계산한다.

    • score_1 = (마지막-2번째 줄 합) ÷ (마지막-3번째 줄 합)
    • score_2 =  마지막 줄 합

    각 데이터 줄 형식
        +000000.166,+000000.157,…
    → +/- 기호·선행 0 포함, 쉼표 구분.

    반환값은 (round(score_1, 3), round(score_2, 3))
    """
    # ── 파일 읽기 & 공백 제거 ───────────────────────────
    with open(file_path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    if len(lines) < 3:
        raise ValueError("파일에 데이터 줄이 3개 미만입니다.")

    line_third_last, line_second_last, line_last = lines[-3:]

    # ── 한 줄의 합계 계산 함수 ──────────────────────────
    def sum_line(line: str) -> float:
        total = 0.0
        for tok in line.split(","):
            tok = tok.strip()
            if not tok:
                continue
            sign = -1.0 if tok[0] == "-" else 1.0
            if tok[0] in "+-":
                tok = tok[1:]
            try:
                total += sign * float(tok)
            except ValueError:
                continue
        return total

    sum_third  = sum_line(line_third_last)
    sum_second = sum_line(line_second_last)
    sum_last   = sum_line(line_last)

    if sum_third == 0:
        raise ZeroDivisionError("마지막-3번째 줄 합이 0이어서 score_1을 계산할 수 없습니다.")

    score_1 = sum_second / sum_third
    score_2 = sum_last

    return round(score_1, 3), round(score_2, 3)
