

import numpy as np



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

    # 표준편차 계산
    stddev = np.std(values, ddof=0)  # ddof=0이면 표본이 아닌 모집단 표준편차

    return round(stddev, 3)



