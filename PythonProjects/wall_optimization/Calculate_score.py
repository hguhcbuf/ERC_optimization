import numpy as np

def calculate_score(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 마지막 두 줄 가져오기
    last_line = lines[-1].strip()
    second_last_line = lines[-2].strip()

    def parse_line(line):
        # 쉼표 기준 split
        parts = line.split(',')
        values = []
        for val in parts:
            val = val.strip()
            # + 기호 제거
            if val.startswith('+'):
                val = val[1:]
            try:
                values.append(float(val))
            except ValueError:
                continue
        return values

    values_last = parse_line(last_line)
    values_second_last = parse_line(second_last_line)

    if not values_last or not values_second_last:
        raise ValueError("데이터를 읽지 못했습니다.")

    # 평균 계산
    avg_last = np.mean(values_last)
    avg_second_last = np.mean(values_second_last)

    return avg_last - avg_second_last



def calculate_score_3sigma(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 마지막 두 줄 가져오기
    last_line = lines[-1].strip()
    second_last_line = lines[-2].strip()

    def parse_line(line):
        # 쉼표 기준 split
        parts = line.split(',')
        values = []
        for val in parts:
            val = val.strip()
            # + 기호 제거
            if val.startswith('+'):
                val = val[1:]
            try:
                values.append(float(val))
            except ValueError:
                continue
        return np.array(values)

    values_last = parse_line(last_line)
    values_second_last = parse_line(second_last_line)

    if values_last.size == 0 or values_second_last.size == 0:
        raise ValueError("데이터를 읽지 못했습니다.")

    def filter_3sigma(values):
        mean = np.mean(values)
        std = np.std(values)
        lower, upper = mean - 3*std, mean + 3*std
        return values[(values >= lower) & (values <= upper)]

    # 3σ 이내 값만 사용
    filtered_last = filter_3sigma(values_last)
    filtered_second_last = filter_3sigma(values_second_last)

    if filtered_last.size == 0 or filtered_second_last.size == 0:
        raise ValueError("3σ 이내 값이 없습니다.")

    avg_last = np.mean(filtered_last)
    avg_second_last = np.mean(filtered_second_last)
    score = avg_second_last - avg_last
    return score, avg_last, avg_second_last



def calculate_score_std(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 마지막 두 번째 줄 가져오기
    second_last_line = lines[-2].strip()

    def parse_line(line):
        parts = line.split(',')
        values = []
        for val in parts:
            val = val.strip()
            if val.startswith('+'):
                val = val[1:]
            try:
                values.append(float(val))
            except ValueError:
                continue
        return np.array(values, dtype=float)

    values = parse_line(second_last_line)
    if values.size == 0:
        raise ValueError("값이 없습니다.")

    # 평균과 표준편차 계산
    avg_val = float(np.mean(values))
    std_val = float(np.std(values, ddof=0))  # 표준편차 (단위: mm)

    # ---- 범위 보정 ----
    # avg 범위: 16 ~ 70
    if avg_val < 16:
        avg_val = 16.0
    elif avg_val > 70:
        avg_val = 70.0

    # std 범위: 0 ~ 5
    if std_val < 0:
        std_val = 0.0
    elif std_val > 3:
        std_val = 3.0

    # ---- Min-Max Normalization ----
    norm_avg = (avg_val - 16) / (70 - 16)   # [0,1]
    norm_std = (std_val - 0) / (3 - 0)      # [0,1]

    # ---- Score ----
    score = norm_avg - norm_std

    return score, norm_avg, norm_std, avg_val, std_val


