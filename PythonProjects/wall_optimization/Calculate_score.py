import numpy as np

def calculate_score(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 마지막 두 번째 줄 가져오기
    profile_lines = lines[-2].strip()
    height_line = lines[-1].strip()

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

    profile_values = parse_line(profile_lines)

    height_val = float(height_line[1:])

    if profile_values.size == 0:
        raise ValueError("값이 없습니다.")

    # 프로파일의 평균과 표준편차 계산
    avg_val = float(np.mean(profile_values))
    std_val = float(np.std(profile_values, ddof=0))  # 표준편차 (단위: mm)

    # std 범위: 0 ~ 5 
    if std_val < 0:
        std_val = 0.0
    elif std_val > 5:
        std_val = 5.0

    # ---- Min-Max Normalization ----
    norm_avg = (avg_val - 0) / (50 - 0)   # [0,1]
    norm_std = (std_val - 0) / (5 - 0)      # [0,1]

    # ---- Score ----
    score = norm_avg - norm_std * 0.2 

    trigger_harsh_extrude = False
    # nothing printed --> penalty
    if avg_val < 18:
        score = 0.0
        trigger_harsh_extrude = False

    return score, norm_avg, norm_std, avg_val, std_val, trigger_harsh_extrude


